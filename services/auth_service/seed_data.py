#!/usr/bin/env python3
"""
Seed Data Script — Populates the database with demo data for testing.

Usage:
    # From host (requires DATABASE_URL pointing to postgres):
    pip install sqlalchemy psycopg2-binary passlib[bcrypt]
    python seed_data.py

    # Or via docker exec into any service container:
    docker exec -it r1-auth-service-1 python -c "exec(open('/app/../../seed_data.py').read())"
"""

import os
import sys
import uuid
from datetime import datetime, timedelta

# Add shared module to path
sys.path.insert(0, os.path.dirname(__file__))

from shared.database import engine, Base, SessionLocal
from shared.models import (
    User, UserRole, Merchant, RiderCompany, Rider, RiderStatus,
    Order, OrderStatus, Payment, PaymentStatus, OrderTracking
)
from shared.auth import hash_password

def seed():
    """Create demo data."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if already seeded
        existing = db.query(User).filter(User.username == "superadmin").first()
        if existing:
            print("⚠️  Database already seeded (superadmin exists). Skipping.")
            return
        
        print("🌱 Seeding database with demo data...")
        
        # ==================== 1. Superadmin ====================
        superadmin = User(
            id=str(uuid.uuid4()),
            username="superadmin",
            email="admin@packnet.com",
            password_hash=hash_password("admin123"),
            phone="+233200000000",
            role=UserRole.SUPERADMIN,
            is_active=True
        )
        db.add(superadmin)
        print("  ✅ Superadmin: superadmin / admin123")
        
        # ==================== 2. Merchant ====================
        merchant_user = User(
            id=str(uuid.uuid4()),
            username="demo_merchant",
            email="merchant@packnet.com",
            password_hash=hash_password("merchant123"),
            phone="+233201111111",
            role=UserRole.MERCHANT,
            is_active=True
        )
        db.add(merchant_user)
        db.flush()
        
        merchant = Merchant(
            id=str(uuid.uuid4()),
            user_id=merchant_user.id,
            store_name="QuickMart Accra",
            store_address="123 Oxford St, Osu, Accra",
            momo_number="+233201111111",
            status="approved",
            approved_at=datetime.utcnow()
        )
        db.add(merchant)
        db.flush()
        print("  ✅ Merchant: demo_merchant / merchant123 (QuickMart Accra)")
        
        # ==================== 3. Company Admin ====================
        company_user = User(
            id=str(uuid.uuid4()),
            username="demo_company",
            email="company@packnet.com",
            password_hash=hash_password("company123"),
            phone="+233202222222",
            role=UserRole.COMPANY_ADMIN,
            is_active=True
        )
        db.add(company_user)
        db.flush()
        
        company = RiderCompany(
            id=str(uuid.uuid4()),
            user_id=company_user.id,
            company_name="SwiftRide Delivery",
            contact_person="Kwame Asante",
            contact_phone="+233202222222",
            status="approved",
            active_subscription=True,
            monthly_sub_paid=True,
            approved_at=datetime.utcnow()
        )
        db.add(company)
        db.flush()
        print("  ✅ Company: demo_company / company123 (SwiftRide Delivery)")
        
        # ==================== 4. Riders ====================
        riders = []
        rider_phones = ["+233203333333", "+233204444444", "+233205555555"]
        rider_names = ["Kofi Rider", "Ama Rider", "Yaw Rider"]
        rider_lats = [5.6037, 5.6100, 5.5950]
        rider_lngs = [-0.1870, -0.1920, -0.1800]
        
        for i, (phone, name, lat, lng) in enumerate(zip(rider_phones, rider_names, rider_lats, rider_lngs)):
            rider_user = User(
                id=str(uuid.uuid4()),
                username=f"rider_{phone[-4:]}",
                email=f"rider{i+1}@packnet.com",
                password_hash=hash_password("12345"),
                phone=phone,
                role=UserRole.RIDER,
                is_active=True
            )
            db.add(rider_user)
            db.flush()
            
            rider = Rider(
                id=str(uuid.uuid4()),
                user_id=rider_user.id,
                company_id=company.id,
                bike_id=f"GR-{1000 + i}",
                status=RiderStatus.ONLINE if i < 2 else RiderStatus.OFFLINE,
                current_lat=lat,
                current_lng=lng,
                completed_orders=10 + i * 5,
                avg_rating=4.0 + i * 0.3,
                num_ratings=5 + i * 3,
                total_earnings=150.0 + i * 75.0
            )
            db.add(rider)
            db.flush()
            riders.append(rider)
            print(f"  ✅ Rider: {name} / phone: {phone} / OTP: 123456 (company: SwiftRide)")
        
        # ==================== 5. Sample Orders ====================
        order_data = [
            {
                "pickup_address": "123 Oxford St, Osu, Accra",
                "pickup_lat": 5.5600, "pickup_lng": -0.1820,
                "dropoff_address": "45 Ring Road, Accra",
                "dropoff_lat": 5.5700, "dropoff_lng": -0.2050,
                "status": OrderStatus.DELIVERED,
                "price": 25.50, "distance": 5.2, "eta": 15,
                "rider_idx": 0
            },
            {
                "pickup_address": "Makola Market, Accra",
                "pickup_lat": 5.5480, "pickup_lng": -0.2110,
                "dropoff_address": "East Legon, Accra",
                "dropoff_lat": 5.6350, "dropoff_lng": -0.1600,
                "status": OrderStatus.IN_TRANSIT,
                "price": 35.00, "distance": 12.1, "eta": 30,
                "rider_idx": 1
            },
            {
                "pickup_address": "Airport City, Accra",
                "pickup_lat": 5.6050, "pickup_lng": -0.1700,
                "dropoff_address": "Tema Community 1",
                "dropoff_lat": 5.6700, "dropoff_lng": -0.0100,
                "status": OrderStatus.ASSIGNED,
                "price": 45.00, "distance": 22.5, "eta": 45,
                "rider_idx": 0
            },
            {
                "pickup_address": "Achimota Mall, Accra",
                "pickup_lat": 5.6150, "pickup_lng": -0.2300,
                "dropoff_address": "Spintex Road, Accra",
                "dropoff_lat": 5.6400, "dropoff_lng": -0.1100,
                "status": OrderStatus.PENDING,
                "price": 30.00, "distance": 15.0, "eta": 35,
                "rider_idx": None
            },
            {
                "pickup_address": "Labone, Accra",
                "pickup_lat": 5.5550, "pickup_lng": -0.1750,
                "dropoff_address": "Dansoman, Accra",
                "dropoff_lat": 5.5350, "dropoff_lng": -0.2650,
                "status": OrderStatus.PENDING,
                "price": 20.00, "distance": 8.0, "eta": 20,
                "rider_idx": None
            },
        ]
        
        for i, od in enumerate(order_data):
            # Create payment
            payment = Payment(
                id=str(uuid.uuid4()),
                merchant_id=merchant.id,
                amount=od["price"],
                currency="GHS",
                status=PaymentStatus.COMPLETED if od["status"] in [OrderStatus.DELIVERED, OrderStatus.IN_TRANSIT, OrderStatus.ASSIGNED] else PaymentStatus.PENDING,
                payment_method="momo",
                phone="+233201111111",
                platform_fee=od["price"] * 0.10,
            )
            db.add(payment)
            db.flush()
            
            rider_id = riders[od["rider_idx"]].id if od["rider_idx"] is not None else None
            
            order = Order(
                id=str(uuid.uuid4()),
                payment_id=payment.id,
                merchant_id=merchant.id,
                company_id=company.id,
                assigned_rider_id=rider_id,
                pickup_address=od["pickup_address"],
                pickup_lat=od["pickup_lat"],
                pickup_lng=od["pickup_lng"],
                dropoff_address=od["dropoff_address"],
                dropoff_lat=od["dropoff_lat"],
                dropoff_lng=od["dropoff_lng"],
                status=od["status"],
                distance_km=od["distance"],
                eta_min=od["eta"],
                price_ghs=od["price"],
                created_at=datetime.utcnow() - timedelta(hours=5 - i),
                assigned_at=datetime.utcnow() - timedelta(hours=4 - i) if rider_id else None,
                delivered_at=datetime.utcnow() - timedelta(hours=1) if od["status"] == OrderStatus.DELIVERED else None,
            )
            db.add(order)
            db.flush()
            
            # Create tracking for assigned/in-transit orders
            if rider_id and od["status"] in [OrderStatus.ASSIGNED, OrderStatus.IN_TRANSIT]:
                tracking = OrderTracking(
                    id=str(uuid.uuid4()),
                    order_id=order.id,
                    tracking_link=f"http://localhost:8300/track/{order.id}",
                    current_lat=riders[od["rider_idx"]].current_lat,
                    current_lng=riders[od["rider_idx"]].current_lng,
                    is_active=True,
                    last_updated_at=datetime.utcnow()
                )
                db.add(tracking)
            
            print(f"  ✅ Order #{i+1}: {od['pickup_address']} → {od['dropoff_address']} ({od['status'].value}) GH₵{od['price']}")
        
        db.commit()
        print("")
        print("=" * 60)
        print("🎉 SEED DATA COMPLETE!")
        print("=" * 60)
        print("")
        print("Demo Credentials:")
        print("─────────────────────────────────────────")
        print("  Admin UI (http://localhost:9000):")
        print("    Superadmin:  superadmin / admin123")
        print("    Merchant:    demo_merchant / merchant123")
        print("    Company:     demo_company / company123")
        print("")
        print("  Rider App (OTP login, code: 123456):")
        print("    Rider 1:     +233203333333")
        print("    Rider 2:     +233204444444")
        print("    Rider 3:     +233205555555")
        print("─────────────────────────────────────────")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Seed error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
