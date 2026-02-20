"""
Order & Assignment Service with Order Status State Machine
Handles order creation, assignment, tracking, and status transitions

Order Status Flow:
PENDING → ASSIGNED → PICKED_UP → IN_TRANSIT → DELIVERED
                  ↘ CANCELLED (at any point before DELIVERED)
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import logging
import httpx

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database import get_db, engine, Base
from shared.models import (
    Order, OrderTracking, OrderStatus, User, Rider, RiderCompany,
    Payment, PaymentStatus
)
from shared.auth import get_current_user, TokenPayload, require_role
from shared.security import setup_security_middleware, check_rate_limit, public_limiter, api_limiter, get_client_ip

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Order & Assignment Service")
setup_security_middleware(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service URLs
TRACKING_SERVICE_URL = os.environ.get("TRACKING_SERVICE_URL", "http://localhost:8300")
NOTIFICATION_SERVICE_URL = os.environ.get("NOTIFICATION_SERVICE_URL", "http://localhost:8400")
PAYMENT_SERVICE_URL = os.environ.get("PAYMENT_SERVICE_URL", "http://localhost:8200")
ASSIGNMENT_SERVICE_URL = os.environ.get("ASSIGNMENT_SERVICE_URL", "http://localhost:8900")

# ==================== Pydantic Models ====================

class CreateOrderRequest(BaseModel):
    payment_id: str
    merchant_id: Optional[str] = None
    pickup_address: str
    pickup_lat: float
    pickup_lng: float
    dropoff_address: str
    dropoff_lat: float
    dropoff_lng: float
    distance_km: float
    eta_min: int
    price_ghs: float

class AssignOrderRequest(BaseModel):
    rider_id: str
    company_id: str

class UpdateOrderStatusRequest(BaseModel):
    status: str  # PICKED_UP, IN_TRANSIT, DELIVERED, CANCELLED
    notes: Optional[str] = None

class OrderResponse(BaseModel):
    id: str
    status: str
    pickup_address: str
    dropoff_address: str
    distance_km: float
    eta_min: int
    price_ghs: float
    assigned_rider_id: Optional[str]
    created_at: datetime
    assigned_at: Optional[datetime]
    delivered_at: Optional[datetime]
    tracking_link: Optional[str]

# ==================== Order Status State Machine ====================

class OrderStateMachine:
    """Manages valid order status transitions."""
    
    VALID_TRANSITIONS = {
        OrderStatus.PENDING:              [OrderStatus.AWAITING_ACCEPTANCE, OrderStatus.ASSIGNED, OrderStatus.CANCELLED],
        OrderStatus.AWAITING_ACCEPTANCE:  [OrderStatus.ASSIGNED, OrderStatus.PENDING, OrderStatus.CANCELLED],
        OrderStatus.ASSIGNED:             [OrderStatus.PICKED_UP, OrderStatus.CANCELLED],
        OrderStatus.PICKED_UP:            [OrderStatus.IN_TRANSIT, OrderStatus.CANCELLED],
        OrderStatus.IN_TRANSIT:           [OrderStatus.DELIVERED, OrderStatus.CANCELLED],
        OrderStatus.DELIVERED:            [],  # Final state
        OrderStatus.CANCELLED:            [],  # Final state
    }
    
    @staticmethod
    def is_valid_transition(current_status: OrderStatus, new_status: OrderStatus) -> bool:
        """Check if transition is valid."""
        return new_status in OrderStateMachine.VALID_TRANSITIONS.get(current_status, [])
    
    @staticmethod
    def get_allowed_transitions(current_status: OrderStatus) -> List[str]:
        """Get list of allowed status values from current state."""
        return [s.value for s in OrderStateMachine.VALID_TRANSITIONS.get(current_status, [])]



# ==================== Health Check ====================

@app.get("/health")
async def health():
    return {"status": "ok", "service": "order"}

# ==================== Order Creation ====================

@app.post("/orders/create", response_model=OrderResponse)
async def create_order(
    request: CreateOrderRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new order after payment."""
    
    # Verify payment exists and is completed
    payment = db.query(Payment).filter(Payment.id == request.payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    if payment.status != PaymentStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment not completed"
        )
    
    try:
        # Resolve merchant_id: orders.merchant_id FKs merchants.id, not users.id
        # If explicit merchant_id provided (admin flow), use it; else look up by user_id
        merchant_profile_id = request.merchant_id
        if not merchant_profile_id:
            from shared.models import Merchant as _Merchant
            merch = db.query(_Merchant).filter(_Merchant.user_id == current_user.user_id).first()
            merchant_profile_id = merch.id if merch else None

        # Create order
        order = Order(
            payment_id=request.payment_id,
            merchant_id=merchant_profile_id,
            pickup_address=request.pickup_address,
            pickup_lat=request.pickup_lat,
            pickup_lng=request.pickup_lng,
            dropoff_address=request.dropoff_address,
            dropoff_lat=request.dropoff_lat,
            dropoff_lng=request.dropoff_lng,
            distance_km=request.distance_km,
            eta_min=request.eta_min,
            price_ghs=request.price_ghs,
            status=OrderStatus.PENDING,
            created_at=datetime.utcnow()
        )
        db.add(order)
        db.commit()
        
        logger.info(f"Order created: {order.id}")
        
        # Auto-assign order immediately
        auto_assign_success = False
        assigned_rider_id = None
        try:
            async with httpx.AsyncClient() as client:
                assignment_response = await client.post(
                    f"{TRACKING_SERVICE_URL.replace('8300', '8100')}/orders/auto-assign",
                    json={
                        "order_id": order.id,
                        "order_lat": request.pickup_lat,
                        "order_lng": request.pickup_lng,
                        "company_id": request.merchant_id or current_user.user_id,
                        "strategy": "hybrid"
                    },
                    timeout=10.0
                )
                if assignment_response.status_code == 200:
                    assignment_data = assignment_response.json()
                    if assignment_data.get("success"):
                        auto_assign_success = True
                        assigned_rider_id = assignment_data.get("rider_id")
                        logger.info(f"Order {order.id} auto-assigned to rider {assigned_rider_id}")
                    else:
                        logger.warning(f"Auto-assignment failed for order {order.id}: {assignment_data.get('message')}")
                else:
                    logger.warning(f"Assignment service returned status {assignment_response.status_code}")
        except Exception as e:
            logger.warning(f"Failed to auto-assign order {order.id}: {str(e)}")
        
        # Send notification: Order placed
        try:
            async with httpx.AsyncClient() as client:
                user = db.query(User).filter(User.id == current_user.user_id).first()
                if user:
                    await client.post(
                        f"{NOTIFICATION_SERVICE_URL}/notify/event",
                        json={
                            "phone": user.phone,
                            "event": "order_placed",
                            "order_id": order.id
                        },
                        timeout=5.0
                    )
        except Exception as e:
            logger.warning(f"Failed to send notification: {str(e)}")
        
        # Get updated order status if auto-assignment was successful
        if auto_assign_success:
            db.refresh(order)
        
        return OrderResponse(
            id=order.id,
            status=order.status.value,
            pickup_address=order.pickup_address,
            dropoff_address=order.dropoff_address,
            distance_km=order.distance_km,
            eta_min=order.eta_min,
            price_ghs=order.price_ghs,
            assigned_rider_id=assigned_rider_id,
            created_at=order.created_at,
            assigned_at=order.assigned_at if auto_assign_success else None,
            delivered_at=None,
            tracking_link=None
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"Order creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order"
        )

# ==================== Order Assignment ====================

@app.post("/orders/{order_id}/assign", response_model=OrderResponse)
async def assign_order(
    order_id: str,
    request: AssignOrderRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually assign a rider to an order (fallback/override).
    
    Note: Orders are normally auto-assigned on creation. This endpoint
    is used for emergency reassignments, admin overrides, or if auto-assignment fails.
    """
    
    # Get order
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Verify state machine: can only assign from PENDING
    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot assign order with status {order.status.value}. Only PENDING orders can be assigned."
        )
    
    # Verify rider exists and belongs to company
    rider = db.query(Rider).filter(
        and_(Rider.id == request.rider_id, Rider.company_id == request.company_id)
    ).first()
    if not rider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rider not found or doesn't belong to the company"
        )
    
    try:
        # Update order status
        order.assigned_rider_id = request.rider_id
        order.company_id = request.company_id
        order.status = OrderStatus.ASSIGNED
        order.assigned_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Order {order_id} assigned to rider {request.rider_id}")
        
        # Start tracking session
        tracking_link = None
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{TRACKING_SERVICE_URL}/tracking/start",
                    json={
                        "order_id": order_id,
                        "rider_id": request.rider_id
                    },
                    timeout=5.0
                )
                if response.status_code == 200:
                    tracking_data = response.json()
                    tracking_link = tracking_data.get("tracking_link")
                    
                    # Create tracking record
                    tracking = OrderTracking(
                        order_id=order_id,
                        tracking_link=tracking_link,
                        is_active=True
                    )
                    db.add(tracking)
                    db.commit()
        except Exception as e:
            logger.warning(f"Failed to start tracking: {str(e)}")
        
        # Send notification: Rider assigned with tracking link
        try:
            async with httpx.AsyncClient() as client:
                merchant = db.query(User).filter(User.id == order.merchant_id).first()
                if merchant and tracking_link:
                    await client.post(
                        f"{NOTIFICATION_SERVICE_URL}/notify/event",
                        json={
                            "phone": merchant.phone,
                            "event": "rider_assigned",
                            "order_id": order_id,
                            "tracking_link": tracking_link
                        },
                        timeout=5.0
                    )
        except Exception as e:
            logger.warning(f"Failed to send assignment notification: {str(e)}")
        
        return OrderResponse(
            id=order.id,
            status=order.status.value,
            pickup_address=order.pickup_address,
            dropoff_address=order.dropoff_address,
            distance_km=order.distance_km,
            eta_min=order.eta_min,
            price_ghs=order.price_ghs,
            assigned_rider_id=order.assigned_rider_id,
            created_at=order.created_at,
            assigned_at=order.assigned_at,
            delivered_at=order.delivered_at,
            tracking_link=tracking_link
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"Assignment failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign order"
        )

# ==================== Rider Accept Order ====================

@app.post("/orders/{order_id}/accept")
async def accept_order(
    order_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Rider accepts an order that is AWAITING_ACCEPTANCE.
    Only the assigned rider can accept. Transitions to ASSIGNED.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatus.AWAITING_ACCEPTANCE:
        raise HTTPException(
            status_code=400,
            detail=f"Order is not awaiting acceptance (status: {order.status.value})"
        )

    # Verify the accepting user is the assigned rider
    rider = db.query(Rider).filter(Rider.user_id == current_user.user_id).first()
    if not rider or order.assigned_rider_id != rider.id:
        raise HTTPException(
            status_code=403,
            detail="You are not the assigned rider for this order"
        )

    # Check deadline hasn't passed
    from datetime import datetime as _dt
    if order.acceptance_deadline and _dt.utcnow() > order.acceptance_deadline:
        raise HTTPException(
            status_code=400,
            detail="Acceptance window has expired (90s timeout)"
        )

    order.status = OrderStatus.ASSIGNED
    order.acceptance_deadline = None
    db.commit()
    db.refresh(order)

    return {
        "order_id": order.id,
        "status": order.status.value,
        "message": "Order accepted — proceed to pickup",
        "pickup_address": order.pickup_address,
        "dropoff_address": order.dropoff_address,
        "price_ghs": order.price_ghs
    }

# ==================== Update Order Status ====================

@app.post("/orders/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: str,
    request: UpdateOrderStatusRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update order status (rider action: PICKED_UP, IN_TRANSIT, DELIVERED)."""
    
    # Get order
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Parse new status
    try:
        new_status = OrderStatus[request.status.upper()]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Allowed: {[s.value for s in OrderStatus]}"
        )
    
    # Verify state machine
    if not OrderStateMachine.is_valid_transition(order.status, new_status):
        allowed = OrderStateMachine.get_allowed_transitions(order.status)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from {order.status.value} to {new_status.value}. Allowed transitions: {allowed}"
        )
    
    # Verify rider permission (only assigned rider can update)
    if current_user.role != "superadmin":
        rider_rec = db.query(Rider).filter(Rider.user_id == current_user.user_id).first()
        if not rider_rec or order.assigned_rider_id != rider_rec.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the assigned rider or admin can update order status"
            )
    
    try:
        # Update status
        order.status = new_status
        
        # Update timestamps
        if new_status == OrderStatus.PICKED_UP:
            order.picked_up_at = datetime.utcnow()
        elif new_status == OrderStatus.DELIVERED:
            order.delivered_at = datetime.utcnow()
        elif new_status == OrderStatus.CANCELLED:
            order.cancelled_at = datetime.utcnow()
        
        db.commit()
        logger.info(f"Order {order_id} status updated to {new_status.value}")
        
        # Send notification
        try:
            async with httpx.AsyncClient() as client:
                merchant = db.query(User).filter(User.id == order.merchant_id).first()
                if merchant:
                    await client.post(
                        f"{NOTIFICATION_SERVICE_URL}/notify/event",
                        json={
                            "phone": merchant.phone,
                            "event": new_status.value.lower(),
                            "order_id": order_id
                        },
                        timeout=5.0
                    )
        except Exception as e:
            logger.warning(f"Failed to send status notification: {str(e)}")
        
        return OrderResponse(
            id=order.id,
            status=order.status.value,
            pickup_address=order.pickup_address,
            dropoff_address=order.dropoff_address,
            distance_km=order.distance_km,
            eta_min=order.eta_min,
            price_ghs=order.price_ghs,
            assigned_rider_id=order.assigned_rider_id,
            created_at=order.created_at,
            assigned_at=order.assigned_at,
            delivered_at=order.delivered_at,
            tracking_link=order.tracking.tracking_link if order.tracking else None
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"Status update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update order status"
        )

# ==================== Get Order ====================

@app.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get order details."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return OrderResponse(
        id=order.id,
        status=order.status.value,
        pickup_address=order.pickup_address,
        dropoff_address=order.dropoff_address,
        distance_km=order.distance_km,
        eta_min=order.eta_min,
        price_ghs=order.price_ghs,
        assigned_rider_id=order.assigned_rider_id,
        created_at=order.created_at,
        assigned_at=order.assigned_at,
        delivered_at=order.delivered_at,
        tracking_link=order.tracking.tracking_link if order.tracking else None
    )

# ==================== List Orders ====================

@app.get("/orders")
async def list_orders(
    status: Optional[str] = None,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List orders for current user (merchant, rider, or admin)."""
    query = db.query(Order)
    
    # Filter by user role
    if current_user.role == "merchant":
        # orders.merchant_id = merchants.id (FK), look up profile first
        from shared.models import Merchant as _Merchant
        merchant_rec = db.query(_Merchant).filter(_Merchant.user_id == current_user.user_id).first()
        if merchant_rec:
            query = query.filter(Order.merchant_id == merchant_rec.id)
        else:
            return []
    elif current_user.role == "rider":
        rider_rec = db.query(Rider).filter(Rider.user_id == current_user.user_id).first()
        if rider_rec:
            query = query.filter(Order.assigned_rider_id == rider_rec.id)
        else:
            return []
    elif current_user.role == "company_admin":
        query = query.filter(Order.company_id == current_user.company_id)
    # superadmin can see all orders
    
    # Filter by status
    if status:
        try:
            status_enum = OrderStatus[status.upper()]
            query = query.filter(Order.status == status_enum)
        except KeyError:
            pass
    
    orders = query.order_by(Order.created_at.desc()).all()
    
    return [
        OrderResponse(
            id=o.id,
            status=o.status.value,
            pickup_address=o.pickup_address,
            dropoff_address=o.dropoff_address,
            distance_km=o.distance_km,
            eta_min=o.eta_min,
            price_ghs=o.price_ghs,
            assigned_rider_id=o.assigned_rider_id,
            created_at=o.created_at,
            assigned_at=o.assigned_at,
            delivered_at=o.delivered_at,
            tracking_link=o.tracking.tracking_link if o.tracking else None
        )
        for o in orders
    ]

# ==================== Order Cancellation ====================

class CancelOrderRequest(BaseModel):
    """Request to cancel an order."""
    reason: str = "customer_request"  # customer_request, merchant_cancel, system_failure, rider_unavailable
    notes: Optional[str] = None

class CancelOrderResponse(BaseModel):
    """Response for cancellation request."""
    order_id: str
    previous_status: str
    new_status: str
    cancellation_reason: str
    refund_amount_ghs: float
    refund_status: str
    cancelled_at: datetime

@app.post("/orders/{order_id}/cancel", response_model=CancelOrderResponse)
async def cancel_order(
    order_id: str,
    request: CancelOrderRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel an order and initiate refund."""
    
    # Get order
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Verify authorization
    # order.merchant_id = merchants.id (profile UUID), current_user.user_id = users.id
    # Must look up the merchant profile to compare properly
    is_owner = False
    if current_user.role in ("merchant", "MERCHANT"):
        from shared.models import Merchant as _MerchModel
        mp = db.query(_MerchModel).filter(_MerchModel.user_id == current_user.user_id).first()
        is_owner = mp is not None and order.merchant_id == mp.id
    elif current_user.role in ("superadmin", "SUPERADMIN"):
        is_owner = True
    if not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only order creator or admin can cancel"
        )
    
    # Check if order can be cancelled
    if not OrderStateMachine.is_valid_transition(order.status, OrderStatus.CANCELLED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order with status {order.status.value}"
        )
    
    try:
        previous_status = order.status
        
        # Calculate refund amount (penalties if rider already picked up)
        refund_amount = order.price_ghs
        penalty_percentage = 0
        
        if order.status == OrderStatus.PICKED_UP:
            penalty_percentage = 10  # 10% penalty if rider picked up
        elif order.status == OrderStatus.IN_TRANSIT:
            penalty_percentage = 25  # 25% penalty if in transit
        
        refund_amount = refund_amount * (1 - penalty_percentage / 100)
        
        # Update order status
        order.status = OrderStatus.CANCELLED
        order.cancelled_at = datetime.utcnow()
        order.cancellation_reason = request.reason
        order.refund_amount = refund_amount
        order.refund_status = "pending"
        
        db.commit()
        
        logger.info(f"Order cancelled: {order_id} (reason={request.reason}, refund={refund_amount})")
        
        # Initiate refund via payment service
        payment = db.query(Payment).filter(Payment.id == order.payment_id).first()
        if payment:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    refund_response = await client.post(
                        f"{PAYMENT_SERVICE_URL}/payments/refund",
                        json={
                            "payment_id": payment.id,
                            "refund_amount": refund_amount,
                            "reason": request.reason,
                            "order_id": order_id
                        },
                        timeout=10.0
                    )
                    if refund_response.status_code == 200:
                        order.refund_status = "processing"
                        db.commit()
            except Exception as e:
                logger.error(f"Failed to initiate refund: {e}")
                order.refund_status = "failed"
                db.commit()
        
        # Notify merchant
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"{NOTIFICATION_SERVICE_URL}/notify/email",
                    json={
                        "user_id": order.merchant_id,
                        "subject": "Order Cancelled",
                        "message": f"Your order {order_id} has been cancelled. Refund: {refund_amount} GHS"
                    },
                    timeout=5.0
                )
        except Exception as e:
            logger.error(f"Failed to notify merchant: {e}")
        
        # Notify rider if assigned
        if order.assigned_rider_id:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.post(
                        f"{NOTIFICATION_SERVICE_URL}/notify/sms",
                        json={
                            "rider_id": order.assigned_rider_id,
                            "message": f"Order {order_id} has been cancelled."
                        },
                        timeout=5.0
                    )
            except Exception as e:
                logger.error(f"Failed to notify rider: {e}")
        
        return CancelOrderResponse(
            order_id=order_id,
            previous_status=previous_status.value,
            new_status=order.status.value,
            cancellation_reason=request.reason,
            refund_amount_ghs=refund_amount,
            refund_status=order.refund_status,
            cancelled_at=order.cancelled_at
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to cancel order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel order"
        )

# ==================== Refund Status ====================

@app.get("/orders/{order_id}/refund-status")
async def get_refund_status(
    order_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get refund status for cancelled order."""
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Verify authorization
    if order.merchant_id != current_user.user_id and current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    if order.status != OrderStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order not cancelled"
        )
    
    return {
        "order_id": order_id,
        "refund_amount": order.refund_amount,
        "refund_status": order.refund_status,
        "cancellation_reason": order.cancellation_reason,
        "cancelled_at": order.cancelled_at
    }

# ==================== Admin: Refund Management ====================

@app.post("/admin/refunds/{order_id}/retry")
async def retry_refund(
    order_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retry failed refund (admin only)."""
    
    if current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only"
        )
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.status != OrderStatus.CANCELLED or order.refund_status != "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must be cancelled with failed refund"
        )
    
    try:
        order.refund_status = "pending"
        db.commit()
        
        payment = db.query(Payment).filter(Payment.id == order.payment_id).first()
        if payment:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(
                    f"{PAYMENT_SERVICE_URL}/payments/refund",
                    json={
                        "payment_id": payment.id,
                        "refund_amount": order.refund_amount,
                        "reason": order.cancellation_reason,
                        "order_id": order_id
                    },
                    timeout=10.0
                )
        
        logger.info(f"Refund retry initiated for order {order_id}")
        
        return {"ok": True, "message": "Refund retry initiated"}
    
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to retry refund: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retry refund"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8400)
