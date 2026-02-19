from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, ForeignKey, Enum, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from shared.database import Base

# Enums
class UserRole(str, enum.Enum):
    SUPERADMIN = "superadmin"
    COMPANY_ADMIN = "company_admin"
    MERCHANT = "merchant"
    RIDER = "rider"

class OrderStatus(str, enum.Enum):
    PENDING              = "PENDING"
    AWAITING_ACCEPTANCE  = "AWAITING_ACCEPTANCE"
    ASSIGNED             = "ASSIGNED"
    PICKED_UP            = "PICKED_UP"
    IN_TRANSIT           = "IN_TRANSIT"
    DELIVERED            = "DELIVERED"
    CANCELLED            = "CANCELLED"

class PaymentStatus(str, enum.Enum):
    INITIATED = "INITIATED"
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class RiderStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BREAK = "break"
    BUSY = "busy"

# ==================== User Models ====================
class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.MERCHANT)
    is_active = Column(Boolean, default=True)
    is_suspended = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    merchant = relationship("Merchant", back_populates="user", uselist=False)
    company = relationship("RiderCompany", back_populates="user", uselist=False)
    rider = relationship("Rider", back_populates="user", uselist=False)

class Merchant(Base):
    __tablename__ = "merchants"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True)
    store_name = Column(String(255), nullable=False)
    store_address = Column(String(500), nullable=True)
    momo_number = Column(String(20), nullable=True)
    status = Column(String(20), default="pending", index=True)  # pending, approved, suspended, banned
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="merchant")
    orders = relationship("Order", back_populates="merchant")

class RiderCompany(Base):
    __tablename__ = "rider_companies"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True)
    company_name = Column(String(255), nullable=False, index=True)
    contact_person = Column(String(255), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    operating_cities = Column(JSON, default=[])  # list of cities
    status = Column(String(20), default="pending", index=True)  # pending, approved, suspended, banned
    commission_pct = Column(Float, default=15.0)  # % company keeps per delivery; rider gets (100 - this)
    active_subscription = Column(Boolean, default=False)
    monthly_sub_paid = Column(Boolean, default=False)
    max_active_jobs = Column(Integer, default=100)
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="company")
    riders = relationship("Rider", back_populates="company")

class Rider(Base):
    __tablename__ = "riders"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True)
    company_id = Column(String(36), ForeignKey("rider_companies.id"), nullable=True)
    bike_id = Column(String(100), nullable=True)
    license_doc = Column(Text, nullable=True)  # base64 encoded ID/license image
    full_name = Column(String(255), nullable=True)
    status = Column(Enum(RiderStatus), default=RiderStatus.OFFLINE)
    current_lat = Column(Float, nullable=True)
    current_lng = Column(Float, nullable=True)
    completed_orders = Column(Integer, default=0)
    avg_rating       = Column(Float,   default=0.0)
    num_ratings      = Column(Integer, default=0)
    total_earnings   = Column(Float,   default=0.0)
    miss_count       = Column(Integer, default=0)   # times rider ignored an AWAITING_ACCEPTANCE
    created_at       = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="rider")
    company = relationship("RiderCompany", back_populates="riders")
    orders = relationship("Order", back_populates="assigned_rider")
    documents = relationship("RiderDocument", back_populates="rider")
    reviews = relationship("RiderReview", back_populates="rider")

# ==================== Order Models ====================
class Order(Base):
    __tablename__ = "orders"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_id = Column(String(36), ForeignKey("payments.id"), nullable=True)
    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=True)
    company_id = Column(String(36), ForeignKey("rider_companies.id"), nullable=True)
    assigned_rider_id = Column(String(36), ForeignKey("riders.id"), nullable=True)
    
    # Order details
    pickup_address = Column(String(500), nullable=False)
    pickup_lat = Column(Float, nullable=False)
    pickup_lng = Column(Float, nullable=False)
    dropoff_address = Column(String(500), nullable=False)
    dropoff_lat = Column(Float, nullable=False)
    dropoff_lng = Column(Float, nullable=False)
    
    # Status tracking
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, index=True)
    distance_km = Column(Float, nullable=True)
    eta_min = Column(Integer, nullable=True)
    price_ghs = Column(Float, nullable=False)
    
    # Cancellation & Refund tracking
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(String(255), nullable=True)
    refund_amount = Column(Float, nullable=True)
    refund_status = Column(String(50), default="none")  # none, pending, processing, completed, failed
    
    # Timestamps
    created_at    = Column(DateTime, default=datetime.utcnow, index=True)
    assigned_at   = Column(DateTime, nullable=True)
    picked_up_at  = Column(DateTime, nullable=True)
    delivered_at  = Column(DateTime, nullable=True)

    # Acceptance timeout (Option 3 — Bolt-style)
    acceptance_deadline = Column(DateTime, nullable=True)   # now() + 90s when sent to rider
    assignment_attempts = Column(Integer, default=0)         # how many riders tried so far
    
    # Relationships
    payment = relationship("Payment", back_populates="order")
    merchant = relationship("Merchant", back_populates="orders")
    company = relationship("RiderCompany")
    assigned_rider = relationship("Rider", back_populates="orders")
    tracking = relationship("OrderTracking", back_populates="order", uselist=False)

class OrderTracking(Base):
    __tablename__ = "order_tracking"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False, unique=True)
    tracking_link = Column(String(500), nullable=False, unique=True)
    link_expires_at = Column(DateTime, nullable=True)
    current_lat = Column(Float, nullable=True)
    current_lng = Column(Float, nullable=True)
    last_updated_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    order = relationship("Order", back_populates="tracking")

# ==================== Payment Models ====================
class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="GHS")
    status = Column(Enum(PaymentStatus), default=PaymentStatus.INITIATED, index=True)
    payment_method = Column(String(50), nullable=False)  # momo, card, wallet
    phone = Column(String(20), nullable=False)
    hubtel_payment_id = Column(String(100), nullable=True, unique=True)
    platform_fee = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    order = relationship("Order", back_populates="payment")
    transaction = relationship("Transaction", back_populates="payment", uselist=False)

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_id = Column(String(36), ForeignKey("payments.id"), nullable=False, unique=True)
    rider_id = Column(String(36), ForeignKey("riders.id"), nullable=True)
    transaction_type = Column(String(50), nullable=False)  # payment, payout, refund
    amount = Column(Float, nullable=False)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    payment = relationship("Payment", back_populates="transaction")

# ==================== Payout Models ====================
class Payout(Base):
    __tablename__ = "payouts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("rider_companies.id"), nullable=False)
    rider_id = Column(String(36), ForeignKey("riders.id"), nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="GHS")
    status = Column(String(50), default="REQUESTED", index=True)  # REQUESTED, SENT, COMPLETED, FAILED
    hubtel_ref = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime, nullable=True)

# ==================== Rider Document Models ====================
class RiderDocument(Base):
    __tablename__ = "rider_documents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rider_id = Column(String(36), ForeignKey("riders.id"), nullable=False)
    doc_type = Column(String(50), nullable=False)  # license, insurance, id
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    expires_at = Column(DateTime, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True)
    
    # Relationships
    rider = relationship("Rider", back_populates="documents")

# ==================== Review Models ====================
class RiderReview(Base):
    __tablename__ = "rider_reviews"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rider_id = Column(String(36), ForeignKey("riders.id"), nullable=False, index=True)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=True, index=True)
    reviewer_id = Column(String(36), ForeignKey("users.id"), nullable=False)  # Who wrote review (merchant/customer)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    is_anonymous = Column(Boolean, default=False)
    is_flagged = Column(Boolean, default=False)  # For moderation
    flag_reason = Column(String(255), nullable=True)
    flagged_at = Column(DateTime, nullable=True)
    helpful_count = Column(Integer, default=0)  # Number of people who found helpful
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    rider = relationship("Rider", back_populates="reviews")

# ==================== Messaging Models ====================
class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("rider_companies.id"), nullable=False)
    rider_id = Column(String(36), ForeignKey("riders.id"), nullable=False)
    sender = Column(String(50), nullable=False)  # admin, rider
    content = Column(Text, nullable=False)
    is_alert = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
