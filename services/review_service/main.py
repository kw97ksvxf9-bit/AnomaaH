"""
Review & Rating Service

Post-delivery reviews and ratings for riders, merchants, and orders.
Includes rating aggregation, filtering, and moderation.
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, timedelta
from enum import Enum
import logging

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database import get_db, engine, Base
from shared.models import (
    RiderReview, Order, OrderStatus, Rider, User, UserRole, Merchant
)
from shared.auth import get_current_user, TokenPayload
from shared.security import setup_security_middleware, sanitize_string

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Review & Rating Service")
setup_security_middleware(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== Pydantic Models ====================

class ReviewFilter(str, Enum):
    """Filter reviews by rating."""
    ALL = "all"
    POSITIVE = "positive"     # 4-5 stars
    NEUTRAL = "neutral"       # 3 stars
    NEGATIVE = "negative"     # 1-2 stars

class CreateReviewRequest(BaseModel):
    """Create a new review."""
    order_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=500)
    is_anonymous: bool = False
    
    @validator('rating')
    def validate_rating(cls, v):
        if not (1 <= v <= 5):
            raise ValueError('Rating must be between 1 and 5')
        return v
    
    @validator('comment')
    def validate_comment(cls, v):
        if v:
            v = sanitize_string(v)
            if len(v) < 5 and len(v) > 0:
                raise ValueError('Comment must be at least 5 characters')
        return v

class ReviewResponse(BaseModel):
    """Review response model."""
    id: str
    order_id: str
    rider_id: str
    rating: int
    comment: Optional[str]
    is_anonymous: bool
    created_at: datetime
    helpful_count: int = 0
    
    class Config:
        from_attributes = True

class RiderRatingResponse(BaseModel):
    """Rider rating summary."""
    rider_id: str
    rider_name: str
    average_rating: float
    total_reviews: int
    rating_breakdown: dict  # {"5": 10, "4": 5, "3": 2, "2": 1, "1": 0}
    recent_reviews: List[ReviewResponse]

class RiderRatingStatsResponse(BaseModel):
    """Detailed rider rating statistics."""
    rider_id: str
    rider_name: str
    average_rating: float
    total_reviews: int
    rating_trend: dict  # {"week": 4.5, "month": 4.3, "all_time": 4.2}
    completion_rate: float  # % of orders completed
    response_time_avg_min: float  # Avg response time to assignments
    delivery_speed_avg_min: float  # Avg delivery time

class ReviewListResponse(BaseModel):
    """List of reviews with pagination."""
    reviews: List[ReviewResponse]
    total: int
    page: int
    per_page: int
    pages: int

# ==================== Health Check ====================

@app.get("/health")
async def health():
    return {"status": "ok", "service": "review"}

# ==================== Create Review ====================

@app.post("/reviews/create", response_model=ReviewResponse)
async def create_review(
    request: CreateReviewRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a review for a delivered order.
    
    Only merchant/customer who placed order can review.
    Can only review after order is DELIVERED.
    """
    
    # Get order
    order = db.query(Order).filter(Order.id == request.order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Verify order is delivered
    if order.status != OrderStatus.DELIVERED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Can only review delivered orders. Current status: {order.status.value}"
        )
    
    # Verify requester is the merchant/customer who placed the order
    # orders.merchant_id = merchants.id (profile UUID), current_user.user_id = users.id
    if current_user.role != "superadmin":
        requester_merchant = db.query(Merchant).filter(
            Merchant.user_id == current_user.user_id
        ).first()
        if not requester_merchant or order.merchant_id != requester_merchant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only order creator can review"
            )
    
    # Check if already reviewed
    existing = db.query(RiderReview).filter(
        and_(
            RiderReview.order_id == request.order_id,
            RiderReview.reviewer_id == current_user.user_id
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this order"
        )
    
    try:
        # Create review
        review = RiderReview(
            order_id=request.order_id,
            rider_id=order.assigned_rider_id,
            reviewer_id=current_user.user_id,
            rating=request.rating,
            comment=request.comment,
            is_anonymous=request.is_anonymous,
            created_at=datetime.utcnow()
        )
        db.add(review)
        db.commit()
        
        logger.info(
            f"Review created: {review.id} "
            f"(order={order.id}, rider={order.assigned_rider_id}, rating={request.rating})"
        )
        
        return ReviewResponse(
            id=review.id,
            order_id=review.order_id,
            rider_id=review.rider_id,
            rating=review.rating,
            comment=review.comment,
            is_anonymous=review.is_anonymous,
            created_at=review.created_at,
            helpful_count=0
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create review: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create review"
        )

# ==================== Get Reviews ====================

@app.get("/riders/{rider_id}/rating", response_model=RiderRatingResponse)
async def get_rider_rating(
    rider_id: str,
    recent_limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Get rider's rating summary."""
    
    # Get rider
    rider = db.query(Rider).filter(Rider.id == rider_id).first()
    if not rider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rider not found"
        )
    
    # Get all reviews
    reviews = db.query(RiderReview).filter(
        RiderReview.rider_id == rider_id
    ).all()
    
    if not reviews:
        return RiderRatingResponse(
            rider_id=rider_id,
            rider_name=rider.user.username if rider.user else "Unknown",
            average_rating=0.0,
            total_reviews=0,
            rating_breakdown={"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
            recent_reviews=[]
        )
    
    # Calculate stats
    ratings = [r.rating for r in reviews]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    
    # Breakdown
    breakdown = {
        "1": len([r for r in reviews if r.rating == 1]),
        "2": len([r for r in reviews if r.rating == 2]),
        "3": len([r for r in reviews if r.rating == 3]),
        "4": len([r for r in reviews if r.rating == 4]),
        "5": len([r for r in reviews if r.rating == 5])
    }
    
    # Recent reviews
    recent = sorted(reviews, key=lambda r: r.created_at, reverse=True)[:recent_limit]
    recent_responses = [
        ReviewResponse(
            id=r.id,
            order_id=r.order_id,
            rider_id=r.rider_id,
            rating=r.rating,
            comment=r.comment,
            is_anonymous=r.is_anonymous,
            created_at=r.created_at
        )
        for r in recent
    ]
    
    return RiderRatingResponse(
        rider_id=rider_id,
        rider_name=rider.user.username if rider.user else "Unknown",
        average_rating=round(avg_rating, 2),
        total_reviews=len(reviews),
        rating_breakdown=breakdown,
        recent_reviews=recent_responses
    )

# ==================== Get Rider Rating Stats ====================

@app.get("/riders/{rider_id}/rating/stats", response_model=RiderRatingStatsResponse)
async def get_rider_rating_stats(
    rider_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed rider rating statistics."""
    
    # Get rider
    rider = db.query(Rider).filter(Rider.id == rider_id).first()
    if not rider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rider not found"
        )
    
    # Get reviews by time period
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    all_reviews = db.query(RiderReview).filter(
        RiderReview.rider_id == rider_id
    ).all()
    
    week_reviews = [r for r in all_reviews if r.created_at >= week_ago]
    month_reviews = [r for r in all_reviews if r.created_at >= month_ago]
    
    # Calculate averages
    avg_all = sum(r.rating for r in all_reviews) / len(all_reviews) if all_reviews else 0
    avg_month = sum(r.rating for r in month_reviews) / len(month_reviews) if month_reviews else 0
    avg_week = sum(r.rating for r in week_reviews) / len(week_reviews) if week_reviews else 0
    
    # Completion rate
    assigned_orders = db.query(Order).filter(
        Order.assigned_rider_id == rider_id
    ).count()
    delivered_orders = db.query(Order).filter(
        and_(
            Order.assigned_rider_id == rider_id,
            Order.status == OrderStatus.DELIVERED
        )
    ).count()
    completion_rate = (delivered_orders / assigned_orders * 100) if assigned_orders > 0 else 0
    
    # Response time (from assignment to pickup)
    response_times = []
    for order in db.query(Order).filter(Order.assigned_rider_id == rider_id).all():
        if order.assigned_at and order.picked_up_at:
            delta = (order.picked_up_at - order.assigned_at).total_seconds() / 60
            response_times.append(delta)
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    # Delivery speed (from pickup to delivery)
    delivery_times = []
    for order in db.query(Order).filter(Order.assigned_rider_id == rider_id).all():
        if order.picked_up_at and order.delivered_at:
            delta = (order.delivered_at - order.picked_up_at).total_seconds() / 60
            delivery_times.append(delta)
    avg_delivery_time = sum(delivery_times) / len(delivery_times) if delivery_times else 0
    
    return RiderRatingStatsResponse(
        rider_id=rider_id,
        rider_name=rider.user.username if rider.user else "Unknown",
        average_rating=round(avg_all, 2),
        total_reviews=len(all_reviews),
        rating_trend={
            "week": round(avg_week, 2),
            "month": round(avg_month, 2),
            "all_time": round(avg_all, 2)
        },
        completion_rate=round(completion_rate, 1),
        response_time_avg_min=round(avg_response_time, 1),
        delivery_speed_avg_min=round(avg_delivery_time, 1)
    )

# ==================== List Reviews ====================

@app.get("/riders/{rider_id}/reviews", response_model=ReviewListResponse)
async def list_rider_reviews(
    rider_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    filter: ReviewFilter = Query(ReviewFilter.ALL),
    db: Session = Depends(get_db)
):
    """List all reviews for a rider with pagination."""
    
    # Get rider
    rider = db.query(Rider).filter(Rider.id == rider_id).first()
    if not rider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rider not found"
        )
    
    # Build query
    query = db.query(RiderReview).filter(RiderReview.rider_id == rider_id)
    
    # Apply filter
    if filter == ReviewFilter.POSITIVE:
        query = query.filter(RiderReview.rating >= 4)
    elif filter == ReviewFilter.NEUTRAL:
        query = query.filter(RiderReview.rating == 3)
    elif filter == ReviewFilter.NEGATIVE:
        query = query.filter(RiderReview.rating <= 2)
    
    # Get total count
    total = query.count()
    
    # Paginate
    offset = (page - 1) * per_page
    reviews = query.order_by(desc(RiderReview.created_at)).offset(offset).limit(per_page).all()
    
    review_responses = [
        ReviewResponse(
            id=r.id,
            order_id=r.order_id,
            rider_id=r.rider_id,
            rating=r.rating,
            comment=r.comment,
            is_anonymous=r.is_anonymous,
            created_at=r.created_at
        )
        for r in reviews
    ]
    
    pages = (total + per_page - 1) // per_page
    
    return ReviewListResponse(
        reviews=review_responses,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )

# ==================== Get Single Review ====================

@app.get("/reviews/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: str,
    db: Session = Depends(get_db)
):
    """Get a single review by ID."""
    
    review = db.query(RiderReview).filter(RiderReview.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    return ReviewResponse(
        id=review.id,
        order_id=review.order_id,
        rider_id=review.rider_id,
        rating=review.rating,
        comment=review.comment,
        is_anonymous=review.is_anonymous,
        created_at=review.created_at
    )

# ==================== Delete Review ====================

@app.delete("/reviews/{review_id}")
async def delete_review(
    review_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a review (only reviewer or admin can delete)."""
    
    review = db.query(RiderReview).filter(RiderReview.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Verify permissions
    if review.reviewer_id != current_user.user_id and current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only reviewer or admin can delete review"
        )
    
    try:
        db.delete(review)
        db.commit()
        
        logger.info(f"Review deleted: {review_id}")
        
        return {"ok": True, "message": "Review deleted"}
    
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete review: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete review"
        )

# ==================== Admin: Get All Reviews ====================

@app.get("/admin/reviews")
async def admin_list_all_reviews(
    current_user: TokenPayload = Depends(get_current_user),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    rider_id: Optional[str] = Query(None),
    min_rating: Optional[int] = Query(None, ge=1, le=5),
    db: Session = Depends(get_db)
):
    """List all reviews (admin only)."""
    
    if current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only"
        )
    
    query = db.query(RiderReview)
    
    if rider_id:
        query = query.filter(RiderReview.rider_id == rider_id)
    
    if min_rating:
        query = query.filter(RiderReview.rating >= min_rating)
    
    total = query.count()
    offset = (page - 1) * per_page
    reviews = query.order_by(desc(RiderReview.created_at)).offset(offset).limit(per_page).all()
    
    review_list = [
        {
            "id": r.id,
            "order_id": r.order_id,
            "rider_id": r.rider_id,
            "reviewer_id": r.reviewer_id,
            "rating": r.rating,
            "comment": r.comment,
            "is_anonymous": r.is_anonymous,
            "created_at": r.created_at
        }
        for r in reviews
    ]
    
    pages = (total + per_page - 1) // per_page
    
    return {
        "reviews": review_list,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages
    }

# ==================== Admin: Flag Review ====================

@app.post("/admin/reviews/{review_id}/flag")
async def flag_review(
    review_id: str,
    reason: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Flag a review for moderation (admin only)."""
    
    if current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only"
        )
    
    review = db.query(RiderReview).filter(RiderReview.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    try:
        review.is_flagged = True
        review.flag_reason = reason
        review.flagged_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Review flagged: {review_id} (reason: {reason})")
        
        return {"ok": True, "message": "Review flagged for review"}
    
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to flag review: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to flag review"
        )

# ==================== Admin: Approve Flagged Review ====================

@app.post("/admin/reviews/{review_id}/approve")
async def approve_flagged_review(
    review_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve a flagged review (admin only)."""
    
    if current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only"
        )
    
    review = db.query(RiderReview).filter(RiderReview.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    try:
        review.is_flagged = False
        review.flag_reason = None
        review.flagged_at = None
        db.commit()
        
        logger.info(f"Review approved: {review_id}")
        
        return {"ok": True, "message": "Review approved"}
    
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to approve review: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve review"
        )

# ==================== Statistics ====================

@app.get("/stats/ratings")
async def get_rating_stats(
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get platform-wide rating statistics."""
    
    total_reviews = db.query(RiderReview).count()
    avg_rating = db.query(func.avg(RiderReview.rating)).scalar() or 0
    
    # Distribution
    rating_1 = db.query(RiderReview).filter(RiderReview.rating == 1).count()
    rating_2 = db.query(RiderReview).filter(RiderReview.rating == 2).count()
    rating_3 = db.query(RiderReview).filter(RiderReview.rating == 3).count()
    rating_4 = db.query(RiderReview).filter(RiderReview.rating == 4).count()
    rating_5 = db.query(RiderReview).filter(RiderReview.rating == 5).count()
    
    # Top riders
    top_riders_query = db.query(
        RiderReview.rider_id,
        func.avg(RiderReview.rating).label('avg_rating'),
        func.count(RiderReview.id).label('review_count')
    ).group_by(RiderReview.rider_id).order_by(desc(func.avg(RiderReview.rating))).limit(5)
    
    top_riders = [
        {
            "rider_id": r[0],
            "average_rating": round(r[1], 2),
            "review_count": r[2]
        }
        for r in top_riders_query.all()
    ]
    
    return {
        "total_reviews": total_reviews,
        "average_rating": round(avg_rating, 2),
        "distribution": {
            "1_star": rating_1,
            "2_star": rating_2,
            "3_star": rating_3,
            "4_star": rating_4,
            "5_star": rating_5
        },
        "top_riders": top_riders
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8700)
