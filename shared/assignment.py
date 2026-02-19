"""
Automatic Rider Assignment Engine

Uses proximity-based matching, rider availability, and performance metrics
to automatically assign orders to the best available rider.
"""

import math
from typing import List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# ==================== Data Models ====================

class AssignmentStrategy(str, Enum):
    """Order assignment strategies."""
    PROXIMITY = "proximity"              # Closest rider
    BALANCED_LOAD = "balanced_load"     # Balanced workload distribution
    HIGHEST_RATING = "highest_rating"   # Best-rated riders first
    FASTEST_DELIVERY = "fastest_delivery"  # Fastest historical delivery time
    HYBRID = "hybrid"                    # Combination (proximity + rating + load)


@dataclass
class RiderScore:
    """Scored rider with ranking information."""
    rider_id: str
    rider_name: str
    distance_km: float
    score: float
    components: dict  # Score breakdown: {"proximity": 0.8, "rating": 0.9, "load": 0.7}
    
    def __lt__(self, other):
        """For sorting - higher score is better."""
        return self.score > other.score


# ==================== Geographic Utilities ====================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two lat/lon coordinates in kilometers.
    
    Uses Haversine formula for accurate great-circle distance.
    
    Args:
        lat1, lon1: Start coordinates (degrees)
        lat2, lon2: End coordinates (degrees)
        
    Returns:
        Distance in kilometers
    """
    # Earth's radius in kilometers
    R = 6371.0
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


# ==================== Rider Availability ====================

class RiderAvailabilityChecker:
    """Checks if a rider is available for assignment."""
    
    # Maximum active orders per rider
    MAX_ACTIVE_ORDERS = 3
    
    # Minimum rating to receive assignments (out of 5.0)
    MIN_RATING = 3.5
    
    # Minimum response time (seconds to wait for rider response)
    ASSIGNMENT_TIMEOUT = 120  # 2 minutes
    
    @staticmethod
    def is_available(
        rider,
        db: Session,
        min_rating: float = 3.5,
        max_active: int = 3
    ) -> bool:
        """
        Check if rider is available for new assignment.
        
        Args:
            rider: Rider model instance
            db: Database session
            min_rating: Minimum rating threshold
            max_active: Maximum active orders allowed
            
        Returns:
            True if rider can accept new orders
        """
        from shared.models import Order, OrderStatus, RiderReview
        
        # Check 1: Account status (Rider uses status enum, not is_active)
        from shared.models import RiderStatus as _RS
        if rider.status not in (_RS.ONLINE,):
            logger.debug(f"Rider {rider.id} status={rider.status} — not ONLINE")
            return False
        
        # Check 2: Minimum rating
        avg_rating = db.query(func.avg(RiderReview.rating)).filter(
            RiderReview.rider_id == rider.id
        ).scalar() or 0
        
        # Only enforce rating threshold if rider has enough ratings
        if avg_rating < min_rating and rider.num_ratings > 5:
            logger.debug(f"Rider {rider.id} rating {avg_rating} < {min_rating}")
            return False
        
        # Check 3: Active order count
        active_orders = db.query(Order).filter(
            and_(
                Order.assigned_rider_id == rider.id,
                Order.status.in_([
                    OrderStatus.AWAITING_ACCEPTANCE,
                    OrderStatus.ASSIGNED,
                    OrderStatus.PICKED_UP,
                    OrderStatus.IN_TRANSIT
                ])
            )
        ).count()
        
        if active_orders >= max_active:
            logger.debug(f"Rider {rider.id} has {active_orders} active orders")
            return False
        
        return True


# ==================== Scoring Engine ====================

class RiderScoringEngine:
    """Computes rider scores for assignment based on multiple factors."""
    
    @staticmethod
    def proximity_score(
        distance_km: float,
        max_distance_km: float = 50.0
    ) -> float:
        """
        Proximity score: 1.0 (closest) to 0.0 (furthest).
        
        Uses inverse exponential decay.
        
        Args:
            distance_km: Distance to rider
            max_distance_km: Distance at which score = 0.1
            
        Returns:
            Score 0.0-1.0 (higher is better)
        """
        if distance_km <= 0:
            return 1.0
        
        # Exponential decay: score = e^(-k*distance)
        # Choose k so that score(max_distance) = 0.1
        k = math.log(10) / max_distance_km
        score = math.exp(-k * distance_km)
        
        return min(1.0, max(0.0, score))
    
    @staticmethod
    def rating_score(average_rating: float) -> float:
        """
        Rating score: based on historical 5-star ratings.
        
        Args:
            average_rating: Average rating 0.0-5.0
            
        Returns:
            Score 0.0-1.0
        """
        if average_rating < 0:
            return 0.0
        # Normalize 5-star rating to 0-1 scale
        return min(1.0, average_rating / 5.0)
    
    @staticmethod
    def load_balance_score(
        active_orders: int,
        max_orders: int = 3
    ) -> float:
        """
        Load balance score: prioritize less busy riders.
        
        Args:
            active_orders: Current active orders for rider
            max_orders: Maximum orders rider can handle
            
        Returns:
            Score 0.0-1.0 (higher = less busy)
        """
        if active_orders <= 0:
            return 1.0
        if active_orders >= max_orders:
            return 0.0
        
        # Linear: 1.0 when empty, 0.0 when full
        return 1.0 - (active_orders / max_orders)
    
    @staticmethod
    def speed_score(
        avg_delivery_time_min: Optional[float],
        target_time_min: float = 60.0
    ) -> float:
        """
        Speed score: based on average delivery time.
        
        Args:
            avg_delivery_time_min: Average delivery time in minutes
            target_time_min: Target delivery time (reference point)
            
        Returns:
            Score 0.0-1.0 (higher = faster)
        """
        if avg_delivery_time_min is None or avg_delivery_time_min <= 0:
            return 0.5  # Unknown = neutral
        
        if avg_delivery_time_min <= target_time_min:
            return 1.0
        
        # Penalty for slower than target
        ratio = avg_delivery_time_min / target_time_min
        return max(0.1, 1.0 / ratio)


# ==================== Assignment Algorithms ====================

class AssignmentEngine:
    """Main engine for automatic rider assignment."""
    
    def __init__(self, strategy: AssignmentStrategy = AssignmentStrategy.HYBRID):
        self.strategy = strategy
        self.scorer = RiderScoringEngine()
        self.availability_checker = RiderAvailabilityChecker()
    
    def find_best_rider(
        self,
        order_lat: float,
        order_lng: float,
        db: Session,
        company_id: Optional[str] = None,
        strategy: Optional[AssignmentStrategy] = None,
        exclude_rider_id: Optional[str] = None
    ) -> Optional[Tuple]:
        """
        Find the best rider for an order.

        Args:
            order_lat, order_lng: Order location coordinates
            db: Database session
            company_id: Restrict to specific company (optional)
            strategy: Assignment strategy (uses default if None)
            exclude_rider_id: Skip this rider (used during cascade after timeout)

        Returns:
            Tuple of (rider, score_details) or None if no riders available
        """
        from shared.models import Rider, RiderCompany, RiderReview, Order, OrderStatus

        # Determine strategy
        strat = strategy or self.strategy

        # Get available riders
        query = db.query(Rider)
        if company_id:
            query = query.filter(Rider.company_id == company_id)

        riders = query.all()
        available_riders = [
            r for r in riders
            if self.availability_checker.is_available(r, db)
            and r.id != exclude_rider_id
        ]

        if not available_riders:
            logger.warning(f"No available riders for order at ({order_lat}, {order_lng})")
            return None
        
        # Score all available riders
        scored_riders = []
        
        for rider in available_riders:
            # Calculate distance
            distance = haversine_distance(
                order_lat, order_lng,
                rider.current_lat or 0, rider.current_lng or 0
            )
            
            # Get rider stats
            avg_rating = db.query(func.avg(RiderReview.rating)).filter(
                RiderReview.rider_id == rider.id
            ).scalar() or 3.5
            
            active_orders = db.query(Order).filter(
                and_(
                    Order.assigned_rider_id == rider.id,
                    Order.status.in_([OrderStatus.AWAITING_ACCEPTANCE, OrderStatus.ASSIGNED, OrderStatus.PICKED_UP, OrderStatus.IN_TRANSIT])
                )
            ).count()
            
            avg_delivery_time_raw = db.query(func.avg(Order.eta_min)).filter(
                Order.assigned_rider_id == rider.id
            ).scalar()
            avg_delivery_time = float(avg_delivery_time_raw) if avg_delivery_time_raw is not None else None
            avg_rating = float(avg_rating)
            if strat == AssignmentStrategy.PROXIMITY:
                score = self.scorer.proximity_score(distance)
                components = {"proximity": score}
            
            elif strat == AssignmentStrategy.HIGHEST_RATING:
                score = self.scorer.rating_score(avg_rating)
                components = {"rating": score}
            
            elif strat == AssignmentStrategy.BALANCED_LOAD:
                score = self.scorer.load_balance_score(active_orders)
                components = {"load_balance": score}
            
            elif strat == AssignmentStrategy.FASTEST_DELIVERY:
                score = self.scorer.speed_score(avg_delivery_time)
                components = {"speed": score}
            
            else:  # HYBRID (default)
                # Weighted combination
                proximity = self.scorer.proximity_score(distance)
                rating = self.scorer.rating_score(avg_rating)
                load = self.scorer.load_balance_score(active_orders)
                speed = self.scorer.speed_score(avg_delivery_time)
                
                # Weights: proximity=40%, rating=30%, load=20%, speed=10%
                score = (
                    0.40 * proximity +
                    0.30 * rating +
                    0.20 * load +
                    0.10 * speed
                )
                
                components = {
                    "proximity": proximity,
                    "rating": rating,
                    "load_balance": load,
                    "speed": speed
                }
            
            rider_score = RiderScore(
                rider_id=rider.id,
                rider_name=rider.user.username if rider.user else "Unknown",
                distance_km=distance,
                score=score,
                components=components
            )
            scored_riders.append(rider_score)
        
        if not scored_riders:
            return None
        
        # Sort by score (highest first)
        scored_riders.sort()
        best = scored_riders[0]
        
        logger.info(
            f"Best rider: {best.rider_name} "
            f"(distance={best.distance_km:.1f}km, score={best.score:.3f})"
        )
        
        return db.query(Rider).filter(Rider.id == best.rider_id).first(), best
    
    def assign_order(
        self,
        order_id: str,
        order_lat: float,
        order_lng: float,
        db: Session,
        company_id: Optional[str] = None,
        strategy: Optional[AssignmentStrategy] = None
    ) -> Tuple[bool, str, Optional[dict]]:
        """
        Automatically assign an order to best available rider.
        
        Args:
            order_id: Order ID to assign
            order_lat, order_lng: Order location
            db: Database session
            company_id: Restrict to specific company
            strategy: Assignment strategy
            
        Returns:
            Tuple of (success, message, assignment_details)
        """
        from shared.models import Order, OrderStatus
        
        # Find best rider
        result = self.find_best_rider(
            order_lat, order_lng, db,
            company_id=company_id,
            strategy=strategy
        )
        
        if not result:
            return False, "No available riders found", None
        
        rider, score = result
        
        try:
            # Update order
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                return False, "Order not found", None
            
            if order.status != OrderStatus.PENDING:
                return False, f"Order status is {order.status.value}, cannot assign", None
            
            order.assigned_rider_id  = rider.id
            order.company_id          = rider.company_id
            order.status              = OrderStatus.AWAITING_ACCEPTANCE
            order.assigned_at         = datetime.utcnow()
            order.acceptance_deadline = datetime.utcnow() + __import__('datetime').timedelta(seconds=90)
            order.assignment_attempts = (order.assignment_attempts or 0) + 1

            db.commit()

            logger.info(f"Order {order_id} awaiting acceptance by rider {rider.id} (attempt {order.assignment_attempts})")
            
            return True, "Order sent to rider — awaiting acceptance (90s)", {
                "rider_id": rider.id,
                "rider_name": score.rider_name,
                "distance_km": score.distance_km,
                "score": score.score,
                "components": score.components
            }
        
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to assign order: {str(e)}")
            return False, f"Assignment failed: {str(e)}", None


# ==================== Pre-Scoring & Recommendations ====================

class RiderRecommender:
    """Generates rider recommendations without performing assignment."""
    
    def __init__(self, engine: AssignmentEngine):
        self.engine = engine
    
    def get_recommendations(
        self,
        order_lat: float,
        order_lng: float,
        db: Session,
        limit: int = 5,
        company_id: Optional[str] = None,
        strategy: AssignmentStrategy = AssignmentStrategy.HYBRID
    ) -> List[RiderScore]:
        """
        Get ranked list of recommended riders.
        
        Args:
            order_lat, order_lng: Order location
            db: Database session
            limit: Number of recommendations
            company_id: Filter by company
            strategy: Assignment strategy
            
        Returns:
            List of RiderScore objects ranked by score
        """
        from shared.models import Rider, RiderReview, Order
        
        # Get available riders
        query = db.query(Rider)
        if company_id:
            query = query.filter(Rider.company_id == company_id)
        
        riders = query.all()
        available_riders = [
            r for r in riders
            if self.engine.availability_checker.is_available(r, db)
        ]
        
        if not available_riders:
            return []
        
        # Score all riders
        scored_riders = []
        
        for rider in available_riders:
            distance = haversine_distance(
                order_lat, order_lng,
                rider.current_lat or 0, rider.current_lng or 0
            )
            
            avg_rating = db.query(func.avg(RiderReview.rating)).filter(
                RiderReview.rider_id == rider.id
            ).scalar() or 3.5
            
            active_orders = db.query(Order).filter(
                Order.assigned_rider_id == rider.id
            ).count()
            
            avg_delivery_time_raw2 = db.query(func.avg(Order.eta_min)).filter(
                Order.assigned_rider_id == rider.id
            ).scalar()
            avg_delivery_time = float(avg_delivery_time_raw2) if avg_delivery_time_raw2 is not None else None
            avg_rating = float(avg_rating)
            
            # Compute score
            proximity = scorer.proximity_score(distance)
            rating = scorer.rating_score(avg_rating)
            load = scorer.load_balance_score(active_orders)
            speed = scorer.speed_score(avg_delivery_time)
            
            score = 0.40 * proximity + 0.30 * rating + 0.20 * load + 0.10 * speed
            
            scored_riders.append(RiderScore(
                rider_id=rider.id,
                rider_name=rider.user.username if rider.user else "Unknown",
                distance_km=distance,
                score=score,
                components={
                    "proximity": proximity,
                    "rating": rating,
                    "load_balance": load,
                    "speed": speed
                }
            ))
        
        # Sort and return top N
        scored_riders.sort()
        return scored_riders[:limit]


# ==================== Initialization ====================

# Global assignment engine instance
assignment_engine = AssignmentEngine(strategy=AssignmentStrategy.HYBRID)
recommender = RiderRecommender(assignment_engine)
