"""
Automatic Rider Assignment Service

Endpoints for automatic and semi-automatic rider assignment with scoring.
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import logging
import asyncio
import httpx

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database import get_db, engine, Base
from shared.models import Order, OrderStatus, Rider, RiderCompany
from shared.auth import get_current_user, TokenPayload
from shared.security import setup_security_middleware
from shared.assignment import (
    AssignmentEngine, AssignmentStrategy, RiderRecommender,
    haversine_distance
)

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Automatic Rider Assignment Service")
setup_security_middleware(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize assignment engine
assignment_engine = AssignmentEngine(strategy=AssignmentStrategy.HYBRID)
recommender = RiderRecommender(assignment_engine)

# Service URLs
TRACKING_SERVICE_URL      = os.environ.get("TRACKING_SERVICE_URL",      "http://localhost:8300")
NOTIFICATION_SERVICE_URL  = os.environ.get("NOTIFICATION_SERVICE_URL",  "http://localhost:8400")

ACCEPTANCE_TIMEOUT_SECS   = 90   # seconds before we cascade to next rider
MAX_ASSIGNMENT_ATTEMPTS   = 3    # after this, order returns to PENDING

# ==================== Background: Acceptance Timeout Watcher ====================

async def acceptance_timeout_watcher():
    """
    Runs every 10 seconds.
    Finds AWAITING_ACCEPTANCE orders whose deadline has passed and either:
      - Cascades to the next best rider (up to MAX_ASSIGNMENT_ATTEMPTS), or
      - Resets to PENDING and logs if all attempts exhausted.
    Increments rider.miss_count for the rider who ignored the request.
    """
    from shared.database import SessionLocal
    while True:
        await asyncio.sleep(10)
        try:
            db = SessionLocal()
            now = datetime.utcnow()
            expired = db.query(Order).filter(
                Order.status == OrderStatus.AWAITING_ACCEPTANCE,
                Order.acceptance_deadline <= now
            ).all()

            for order in expired:
                ignoring_rider_id = order.assigned_rider_id

                # Penalise the rider who ignored
                if ignoring_rider_id:
                    db.query(Rider).filter(Rider.id == ignoring_rider_id).update(
                        {"miss_count": Rider.miss_count + 1}
                    )
                    logger.info(f"Rider {ignoring_rider_id[:8]} missed order {order.id[:8]} — miss_count +1")

                if (order.assignment_attempts or 0) < MAX_ASSIGNMENT_ATTEMPTS:
                    # Reset to PENDING briefly so find_best_rider can re-score
                    # (exclude the ignoring rider by temporarily tagging)
                    order.status               = OrderStatus.PENDING
                    order.assigned_rider_id    = None
                    order.acceptance_deadline  = None
                    db.commit()

                    # Try again — exclude the rider who ignored
                    result = assignment_engine.find_best_rider(
                        order.pickup_lat, order.pickup_lng, db,
                        company_id=order.company_id,
                        exclude_rider_id=ignoring_rider_id
                    )
                    if result:
                        rider, score = result
                        order.assigned_rider_id  = rider.id
                        order.status             = OrderStatus.AWAITING_ACCEPTANCE
                        order.acceptance_deadline = datetime.utcnow() + timedelta(seconds=ACCEPTANCE_TIMEOUT_SECS)
                        order.assignment_attempts = (order.assignment_attempts or 0) + 1
                        db.commit()
                        logger.info(f"Order {order.id[:8]} re-sent to rider {rider.id[:8]} (attempt {order.assignment_attempts})")
                    else:
                        order.status              = OrderStatus.PENDING
                        order.assignment_attempts = (order.assignment_attempts or 0) + 1
                        db.commit()
                        logger.warning(f"Order {order.id[:8]} — no riders available on attempt {order.assignment_attempts}")
                else:
                    # All attempts exhausted — return to PENDING for admin/re-queue
                    order.status              = OrderStatus.PENDING
                    order.assigned_rider_id   = None
                    order.acceptance_deadline = None
                    db.commit()
                    logger.warning(f"Order {order.id[:8]} returned to PENDING — exhausted {MAX_ASSIGNMENT_ATTEMPTS} attempts")

            db.close()
        except Exception as e:
            logger.error(f"Acceptance watcher error: {e}")


@app.on_event("startup")
async def start_background_tasks():
    asyncio.create_task(acceptance_timeout_watcher())

# ==================== Pydantic Models ====================

class RiderScoreDetail(BaseModel):
    rider_id: str
    rider_name: str
    distance_km: float
    score: float
    components: dict  # Score breakdown

class AutoAssignRequest(BaseModel):
    order_id: str
    order_lat: float
    order_lng: float
    company_id: Optional[str] = None
    strategy: Optional[str] = "hybrid"  # proximity, balanced_load, highest_rating, fastest_delivery, hybrid

class AutoAssignResponse(BaseModel):
    success: bool
    message: str
    rider_id: Optional[str] = None
    rider_name: Optional[str] = None
    distance_km: Optional[float] = None
    score: Optional[float] = None
    score_breakdown: Optional[dict] = None

class RiderRecommendationResponse(BaseModel):
    order_id: str
    order_location: dict  # {"lat": 5.6, "lng": -0.18}
    recommendations: List[RiderScoreDetail]
    top_rider: Optional[RiderScoreDetail] = None

# ==================== Health Check ====================

@app.get("/health")
async def health():
    return {"status": "ok", "service": "assignment"}

# ==================== Automatic Assignment ====================

@app.post("/orders/auto-assign", response_model=AutoAssignResponse)
async def auto_assign_order(
    request: AutoAssignRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Automatically assign order to best available rider.
    
    Uses proximity, rating, load balancing, and speed metrics
    to find optimal match.
    """
    
    try:
        # Validate strategy
        try:
            strategy = AssignmentStrategy(request.strategy.lower())
        except ValueError:
            return AutoAssignResponse(
                success=False,
                message=f"Invalid strategy: {request.strategy}. "
                        f"Valid: proximity, balanced_load, highest_rating, fastest_delivery, hybrid"
            )
        
        # Get order to verify it exists
        order = db.query(Order).filter(Order.id == request.order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        if order.status != OrderStatus.PENDING:
            return AutoAssignResponse(
                success=False,
                message=f"Order status is {order.status.value}, cannot auto-assign"
            )
        
        # Perform assignment
        success, message, details = assignment_engine.assign_order(
            order_id=request.order_id,
            order_lat=request.order_lat,
            order_lng=request.order_lng,
            db=db,
            company_id=request.company_id or order.company_id,
            strategy=strategy
        )
        
        if success and details:
            # Start tracking
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{TRACKING_SERVICE_URL}/tracking/start",
                        json={
                            "order_id": request.order_id,
                            "rider_id": details["rider_id"]
                        },
                        timeout=5.0
                    )
            except Exception as e:
                logger.warning(f"Failed to start tracking: {str(e)}")
            
            # Send notification
            try:
                async with httpx.AsyncClient() as client:
                    merchant = order.merchant
                    if merchant and merchant.phone:
                        await client.post(
                            f"{NOTIFICATION_SERVICE_URL}/notify/event",
                            json={
                                "phone": merchant.phone,
                                "event": "rider_assigned_auto",
                                "order_id": request.order_id,
                                "rider_name": details["rider_name"]
                            },
                            timeout=5.0
                        )
            except Exception as e:
                logger.warning(f"Failed to send notification: {str(e)}")
            
            return AutoAssignResponse(
                success=True,
                message=message,
                rider_id=details["rider_id"],
                rider_name=details["rider_name"],
                distance_km=details["distance_km"],
                score=details["score"],
                score_breakdown=details["components"]
            )
        
        return AutoAssignResponse(
            success=False,
            message=message
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auto-assign failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auto-assignment failed"
        )

# ==================== Rider Recommendations ====================

@app.get("/orders/{order_id}/recommendations", response_model=RiderRecommendationResponse)
async def get_rider_recommendations(
    order_id: str,
    limit: int = Query(5, ge=1, le=10),
    strategy: str = Query("hybrid"),
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get ranked list of rider recommendations for an order.
    
    Does not perform assignment - just provides recommendations.
    Useful for manual selection with insights.
    """
    
    try:
        # Get order
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Validate strategy
        try:
            strat = AssignmentStrategy(strategy.lower())
        except ValueError:
            strat = AssignmentStrategy.HYBRID
        
        # Get recommendations
        recommendations = recommender.get_recommendations(
            order_lat=order.pickup_lat,
            order_lng=order.pickup_lng,
            db=db,
            limit=limit,
            company_id=order.company_id,
            strategy=strat
        )
        
        recs = [
            RiderScoreDetail(
                rider_id=r.rider_id,
                rider_name=r.rider_name,
                distance_km=r.distance_km,
                score=r.score,
                components=r.components
            )
            for r in recommendations
        ]
        
        top_rider = recs[0] if recs else None
        
        return RiderRecommendationResponse(
            order_id=order_id,
            order_location={
                "lat": order.pickup_lat,
                "lng": order.pickup_lng
            },
            recommendations=recs,
            top_rider=top_rider
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recommendations"
        )

# ==================== Rider Availability Check ====================

@app.get("/riders/{rider_id}/available")
async def check_rider_availability(
    rider_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if a specific rider is available for assignment."""
    
    rider = db.query(Rider).filter(Rider.id == rider_id).first()
    if not rider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rider not found"
        )
    
    is_available = assignment_engine.availability_checker.is_available(rider, db)
    
    # Get rider stats
    from shared.models import RiderReview, Order
    
    avg_rating = db.query(func.avg(RiderReview.rating)).filter(
        RiderReview.rider_id == rider_id
    ).scalar() or 0
    
    active_orders = db.query(Order).filter(
        Order.assigned_rider_id == rider_id,
        Order.status.in_(['assigned', 'picked_up', 'in_transit'])
    ).count()
    
    from sqlalchemy import func
    avg_delivery_time = db.query(func.avg(Order.eta_min)).filter(
        Order.assigned_rider_id == rider_id
    ).scalar()
    
    return {
        "rider_id": rider_id,
        "rider_name": rider.user.username if rider.user else "Unknown",
        "available": is_available,
        "rating": round(avg_rating, 1),
        "active_orders": active_orders,
        "avg_delivery_time_min": avg_delivery_time
    }

# ==================== Bulk Auto-Assignment ====================

@app.post("/orders/batch-auto-assign")
async def batch_auto_assign(
    order_ids: List[str],
    strategy: str = Query("hybrid"),
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Automatically assign multiple orders in bulk.
    
    Useful for batch processing pending orders.
    """
    
    if len(order_ids) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 orders per batch"
        )
    
    try:
        strat = AssignmentStrategy(strategy.lower())
    except ValueError:
        strat = AssignmentStrategy.HYBRID
    
    results = []
    
    for order_id in order_ids:
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order or order.status != OrderStatus.PENDING:
                results.append({
                    "order_id": order_id,
                    "success": False,
                    "message": "Order not found or not pending"
                })
                continue
            
            success, message, details = assignment_engine.assign_order(
                order_id=order_id,
                order_lat=order.pickup_lat,
                order_lng=order.pickup_lng,
                db=db,
                company_id=order.company_id,
                strategy=strat
            )
            
            results.append({
                "order_id": order_id,
                "success": success,
                "message": message,
                "rider_id": details.get("rider_id") if details else None
            })
        
        except Exception as e:
            logger.error(f"Failed to assign {order_id}: {str(e)}")
            results.append({
                "order_id": order_id,
                "success": False,
                "message": str(e)
            })
    
    # Summary
    successful = sum(1 for r in results if r["success"])
    
    return {
        "total": len(results),
        "successful": successful,
        "failed": len(results) - successful,
        "results": results
    }

# ==================== Assignment Statistics ====================

@app.get("/stats/assignment")
async def get_assignment_stats(
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get assignment statistics."""
    from sqlalchemy import func
    
    # Orders assigned vs pending
    total_pending = db.query(Order).filter(Order.status == OrderStatus.PENDING).count()
    total_assigned = db.query(Order).filter(Order.status == OrderStatus.ASSIGNED).count()
    
    # Riders online
    from shared.models import Rider, RiderStatus
    active_riders = db.query(Rider).filter(Rider.status == RiderStatus.ONLINE).count()
    
    return {
        "pending_orders": total_pending,
        "assigned_orders": total_assigned,
        "active_riders": active_riders,
        "assignment_rate": round(
            (total_assigned / (total_assigned + total_pending) * 100) if (total_assigned + total_pending) > 0 else 0,
            1
        )
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8600)
