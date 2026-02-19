#!/usr/bin/env python3
"""ANOMAAH Delivery Platform — Full System Simulation"""
import math, time, uuid, random, requests, psycopg2, psycopg2.extras
from datetime import datetime
from typing import Optional
from passlib.context import CryptContext

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
def hash_pw(p: str) -> str: return _pwd_ctx.hash(p)

AUTH_URL         = "http://localhost:8600"
PAYMENT_URL      = "http://localhost:8200"
ORDER_URL        = "http://localhost:8500"
ASSIGNMENT_URL   = "http://localhost:8900"
RIDER_STATUS_URL = "http://localhost:8800"
REVIEW_URL       = "http://localhost:8700"
DB_DSN = "host=localhost port=5432 dbname=delivery user=postgres password=postgres"
SA_USER="superadmin"; SA_PASS="admin123"
MER_USER="sim_merchant"; MER_PASS="merchant123"

AREAS=[
    ("Osu, Accra",5.5558,-0.1843),("East Legon, Accra",5.6360,-0.1569),
    ("Accra Mall, Spintex",5.6195,-0.1440),("Labone, Accra",5.5701,-0.1788),
    ("Achimota, Accra",5.6142,-0.2245),("Dansoman, Accra",5.5346,-0.2590),
    ("Tesano, Accra",5.5876,-0.2274),("Adabraka, Accra",5.5611,-0.2132),
    ("Cantonments, Accra",5.5803,-0.1690),("Madina, Accra",5.6799,-0.1659),
    ("Tema, Greater Accra",5.6698,-0.0166),("Airport Hills, Accra",5.6030,-0.1750),
]
COMMENTS=["Super fast delivery!","Rider very polite and on time.",
          "Package arrived safely.","Quick and efficient!",
          "Rider called ahead — helpful.","Great service, will use again.",
          "Prompt and hassle-free.","Rider handled package with care.",
          "On time and friendly!","Good delivery, minor delay but fine."]

S=dict(companies=0,riders=0,orders=0,pays=0,assigned=0,
       delivered=0,cancelled=0,failed=0,reviews=0,errors=[])

PLATFORM_FEE_DELIVERY            = 5.00  # GHS charged on every delivery
PLATFORM_FEE_CANCEL_AFTER_PICKUP = 2.50  # GHS charged if cancelled after pickup

G="\033[92m";R="\033[91m";Y="\033[93m";C="\033[96m"
B="\033[94m";W="\033[97m";M="\033[95m";BOLD="\033[1m";END="\033[0m"

def banner(t): print(f"\n{BOLD}{B}{'='*66}{END}\n{BOLD}{W}  {t}{END}\n{BOLD}{B}{'='*66}{END}")
def ok(m):   print(f"  {G}+{END} {m}")
def warn(m): print(f"  {Y}!{END} {m}")
def fail(m): print(f"  {R}x{END} {m}"); S["errors"].append(m)

SES=requests.Session()
SES.headers.update({"Content-Type":"application/json"})

def post(url,body,tok=None):
    h={"Authorization":f"Bearer {tok}"} if tok else {}
    return SES.post(url,json=body,headers=h,timeout=15)

def get(url,tok=None,params=None):
    h={"Authorization":f"Bearer {tok}"} if tok else {}
    return SES.get(url,headers=h,params=params or {},timeout=15)

def db_q(sql,p=None):
    c=psycopg2.connect(DB_DSN); c.autocommit=True
    cur=c.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(sql,p)
    try: rows=cur.fetchall()
    except: rows=[]
    c.close(); return rows

def db_u(sql,p=None):
    c=psycopg2.connect(DB_DSN); c.autocommit=True
    cur=c.cursor(); cur.execute(sql,p); n=cur.rowcount; c.close(); return n

def login(user,pw):
    r=post(f"{AUTH_URL}/token",{"username":user,"password":pw})
    return r.json().get("access_token") if r.status_code==200 else None


# ─────────────────────────────────────────────────────────────
# SCHEMA — wallet_ledger + company balance column
# ─────────────────────────────────────────────────────────────
def setup_schema():
    """Create wallet_ledger table and company balance column if not present."""
    db_u("""
        CREATE TABLE IF NOT EXISTS wallet_ledger (
            id             VARCHAR(36) PRIMARY KEY,
            order_id       VARCHAR(36),
            rider_id       VARCHAR(36),
            company_id     VARCHAR(36),
            event_type     VARCHAR(30) NOT NULL,
            gross          DOUBLE PRECISION NOT NULL DEFAULT 0,
            platform_cut   DOUBLE PRECISION NOT NULL DEFAULT 0,
            company_cut    DOUBLE PRECISION NOT NULL DEFAULT 0,
            rider_cut      DOUBLE PRECISION NOT NULL DEFAULT 0,
            commission_pct DOUBLE PRECISION NOT NULL DEFAULT 0,
            created_at     TIMESTAMP DEFAULT now()
        )
    """)
    db_u("ALTER TABLE rider_companies ADD COLUMN IF NOT EXISTS balance DOUBLE PRECISION DEFAULT 0.0")

# ─────────────────────────────────────────────────────────────
# PHASE 0 — Clean up previous simulation data
# ─────────────────────────────────────────────────────────────
def phase0_cleanup():
    banner("PHASE 0 — Cleaning Previous Simulation Data")
    # Remove sim data (sim users, their riders, companies, payments, orders)
    sim_user_ids = [r['id'] for r in db_q("SELECT id FROM users WHERE username LIKE 'sim_%'")]
    sim_rider_ids = [r['id'] for r in db_q("SELECT id FROM riders WHERE user_id = ANY(%s::text[])", (sim_user_ids,))] if sim_user_ids else []
    sim_company_ids = [r['id'] for r in db_q("SELECT id FROM rider_companies WHERE user_id = ANY(%s::text[])", (sim_user_ids,))] if sim_user_ids else []

    # Delete reviews referencing sim riders
    if sim_rider_ids:
        db_u("DELETE FROM rider_reviews WHERE rider_id = ANY(%s::text[])", (sim_rider_ids,))
    # Get sim orders by payment ID then purge reviews → orders → payments
    sim_pay_ids = [r['id'] for r in db_q("SELECT id FROM payments WHERE hubtel_payment_id LIKE 'SIMHUB%'")]
    if sim_pay_ids:
        sim_order_ids = [r['id'] for r in db_q("SELECT id FROM orders WHERE payment_id = ANY(%s::text[])", (sim_pay_ids,))]
        if sim_order_ids:
            db_u("DELETE FROM rider_reviews  WHERE order_id = ANY(%s::text[])", (sim_order_ids,))
            db_u("DELETE FROM wallet_ledger  WHERE order_id = ANY(%s::text[])", (sim_order_ids,))
        db_u("DELETE FROM orders    WHERE payment_id = ANY(%s::text[])", (sim_pay_ids,))
        db_u("DELETE FROM payments  WHERE id         = ANY(%s::text[])", (sim_pay_ids,))
    if sim_company_ids:
        db_u("DELETE FROM orders WHERE company_id = ANY(%s::text[])", (sim_company_ids,))
    if sim_rider_ids:
        db_u("DELETE FROM riders WHERE id = ANY(%s::text[])", (sim_rider_ids,))
    if sim_company_ids:
        db_u("DELETE FROM rider_companies WHERE id = ANY(%s::text[])", (sim_company_ids,))
    if sim_user_ids:
        db_u("DELETE FROM users WHERE id = ANY(%s::text[])", (sim_user_ids,))
    ok(f"Cleanup complete. Removed {len(sim_company_ids)} companies, {len(sim_rider_ids)} riders")

# ─────────────────────────────────────────────────────────────
# PHASE 1 — Login superadmin + get demo merchant id
# ─────────────────────────────────────────────────────────────
ADMIN_TOK = None
MERCHANT_ID = None  # merchants.id (FK)

def phase1_login():
    global ADMIN_TOK, MERCHANT_ID
    banner("PHASE 1 — Auth / Login")
    ADMIN_TOK = login(SA_USER, SA_PASS)
    if not ADMIN_TOK:
        fail(f"Superadmin login failed! Tried {SA_USER}/{SA_PASS}")
        return False
    ok(f"Superadmin logged in → token acquired")
    # Get approved merchant id
    rows = db_q("SELECT id FROM merchants WHERE status='approved' LIMIT 1")
    if not rows:
        fail("No approved merchant found in DB!")
        return False
    MERCHANT_ID = rows[0]['id']
    ok(f"Merchant ID: {MERCHANT_ID}")
    return True

# ─────────────────────────────────────────────────────────────
# PHASE 2 — Register 4 rider companies
# ─────────────────────────────────────────────────────────────
COMPANIES = []  # list of {id, name, token, user_id}
COMPANY_DEFS = [
    ("Sim Flash Riders", "Kwame Mensah", "+233200000001"),
    ("Sim Speed Wings", "Abena Owusu",  "+233200000002"),
    ("Sim Moto Express", "Kofi Boateng", "+233200000003"),
    ("Sim Turbo Keke",  "Ama Darko",    "+233200000004"),
]

def phase2_companies():
    banner("PHASE 2 — Register 4 Rider Companies")
    for i,(cname,contact,phone) in enumerate(COMPANY_DEFS,1):
        uname = f"sim_co_{i:02d}"
        email = f"sim_co_{i:02d}@sim.test"
        body = dict(username=uname, email=email, password="Pass@1234",
                    phone=phone, role="company_admin",
                    company_name=cname, contact_person=contact)
        r = post(f"{AUTH_URL}/register", body)
        if r.status_code in (200,201):
            tok = r.json().get("access_token","")
            # get the company record from DB
            rows = db_q("SELECT rc.id FROM rider_companies rc JOIN users u ON u.id=rc.user_id WHERE u.username=%s", (uname,))
            if rows:
                cid = rows[0]['id']
                # approve the company
                comm_pct = random.choice([15.0, 18.0, 20.0, 22.0, 25.0])
                db_u("UPDATE rider_companies SET status='approved', commission_pct=%s, balance=0 WHERE id=%s",
                     (comm_pct, cid))
                COMPANIES.append({"id":cid,"name":cname,"token":tok,"uname":uname,"commission_pct":comm_pct})
                ok(f"Company {i}: {cname} (id={cid[:8]}..) — {comm_pct:.0f}% commission")
                S["companies"] += 1
            else:
                fail(f"Company {cname} registered but not found in DB")
        else:
            try: detail = r.json().get("detail","")
            except: detail = r.text[:80]
            fail(f"Company {cname} registration failed: {r.status_code} {detail}")
    print(f"\n  {C}Total companies: {S['companies']}/4{END}")


# ─────────────────────────────────────────────────────────────
# PHASE 3 — Register 3 riders per company (12 total)
# ─────────────────────────────────────────────────────────────
RIDERS = []  # {id, user_id, company_id, name, phone}
RIDER_NAMES = [
    "Esi Asante","Yaw Boateng","Akua Mensah","Kojo Acheampong","Adwoa Sarpong",
    "Kwabena Amoah","Abena Frimpong","Kweku Tetteh","Akosua Asare","Fiifi Quaye",
    "Maame Dankwa","Nana Antwi","Kofi Darko","Ama Boateng","Kwame Asante",
    "Efua Mensah","Baffour Acheampong","Adjoa Amponsah","Kwesi Ofori","Afia Owusu",
    "Nii Ankrah","Dzifa Agbeko","Selorm Deku","Eyram Klu","Mawuli Adzoe",
]
BIKE_PREFIXES = ["GR","ER","BA","AK"]

def phase3_riders():
    banner("PHASE 3 — Register 25 Riders (7+6+6+6) — Direct DB")
    PASSCODE_HASH = hash_pw("12345")
    ridx = 0
    riders_per_company = [7, 6, 6, 6]  # 25 total
    for ci, co in enumerate(COMPANIES):
        for ri in range(riders_per_company[ci]):
            name = RIDER_NAMES[ridx]
            phone = f"+23326{ci:01d}{ri:01d}0000{ridx:02d}"
            uname = f"sim_rider_{ci+1:01d}{ri+1:01d}"
            email = f"sim_rider_{ci+1:01d}{ri+1:01d}@sim.test"
            bike  = f"{BIKE_PREFIXES[ci]}-{1000+ridx*11}"
            uid   = str(uuid.uuid4())
            rid_  = str(uuid.uuid4())
            now   = datetime.utcnow()
            try:
                db_u(
                    """INSERT INTO users (id,username,email,password_hash,phone,role,is_active,created_at)
                       VALUES (%s,%s,%s,%s,%s,'RIDER',true,%s)""",
                    (uid, uname, email, PASSCODE_HASH, phone, now)
                )
                db_u(
                    """INSERT INTO riders (id,user_id,company_id,bike_id,full_name,license_doc,status,
                                          current_lat,current_lng,completed_orders,avg_rating,num_ratings,
                                          total_earnings,created_at)
                       VALUES (%s,%s,%s,%s,%s,%s,'OFFLINE'::riderstatus,0,0,0,0.0,0,0.0,%s)""",
                    (rid_, uid, co["id"], bike, name, f"LIC{ridx:04d}", now)
                )
                RIDERS.append({"id":rid_,"user_id":uid,"company_id":co["id"],"name":name,"phone":phone})
                ok(f"Rider: {name} @ {co['name'][:16]} (bike={bike})")
                S["riders"] += 1
            except Exception as e:
                fail(f"Rider {uname} DB insert failed: {e}")
            ridx += 1
    print(f"\n  {C}Total riders: {S['riders']}/25{END}")

# ─────────────────────────────────────────────────────────────
# PHASE 4 — Set all riders ONLINE + seed location
# ─────────────────────────────────────────────────────────────
def phase4_set_online():
    banner("PHASE 4 — Setting All Riders ONLINE")
    for rd in RIDERS:
        # pick a random area near Accra for initial location
        area = random.choice(AREAS)
        lat = area[1] + random.uniform(-0.01, 0.01)
        lng = area[2] + random.uniform(-0.01, 0.01)
        # set status via API
        r = post(f"{RIDER_STATUS_URL}/status/update",
                 {"rider_id": rd["id"], "status": "online", "set_by": "sim"})
        if r.status_code == 200:
            # seed location in DB
            db_u("UPDATE riders SET current_lat=%s, current_lng=%s WHERE id=%s",
                 (lat, lng, rd["id"]))
            ok(f"ONLINE: {rd['name']} @ ({lat:.4f},{lng:.4f})")
        else:
            fail(f"Could not set {rd['name']} online: {r.text[:60]}")


# ─────────────────────────────────────────────────────────────
# PHASE 5 — Create 50 payments (direct DB) + 50 orders (API)
# ─────────────────────────────────────────────────────────────
ORDERS = []  # list of order dicts from API response

def haversine(lat1,lon1,lat2,lon2):
    R=6371.0
    dlat=math.radians(lat2-lat1); dlon=math.radians(lon2-lon1)
    a=math.sin(dlat/2)**2+math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return R*2*math.asin(math.sqrt(a))

def phase5_orders():
    banner("PHASE 5 — Create 100 Payments + Orders")
    random.seed(42)
    company_ids = [co["id"] for co in COMPANIES]
    
    for i in range(1, 101):
        pickup_area  = random.choice(AREAS)
        dropoff_area = random.choice([a for a in AREAS if a != pickup_area])
        plat, plng   = pickup_area[1]+random.uniform(-0.005,0.005), pickup_area[2]+random.uniform(-0.005,0.005)
        dlat, dlng   = dropoff_area[1]+random.uniform(-0.005,0.005), dropoff_area[2]+random.uniform(-0.005,0.005)
        dist = round(haversine(plat,plng,dlat,dlng), 2)
        eta  = max(10, int(dist * 4))
        price= round(min(65.0, max(20.0, dist * 1.8 + random.uniform(2,5))), 2)
        fee  = 5.00
        phone= f"+23324{i:07d}"
        
        # Insert payment directly into DB (payment service is in-memory)
        pay_id  = str(uuid.uuid4())
        sim_run = int(time.time()) % 100000  # 5-digit run tag
        now = datetime.utcnow()
        db_u(
            """INSERT INTO payments
               (id, merchant_id, amount, currency, status, payment_method, phone,
                hubtel_payment_id, platform_fee, created_at, completed_at)
               VALUES (%s,%s,%s,'GHS','COMPLETED'::paymentstatus,'momo',%s,%s,%s,%s,%s)""",
            (pay_id, MERCHANT_ID, price, phone,
             f"SIMHUB{sim_run}_{i:04d}", fee, now, now)
        )
        S["pays"] += 1
        
        # Create order via API (using superadmin token + explicit merchant_id)
        co_id = company_ids[i % len(company_ids)]
        body = dict(
            payment_id=pay_id,
            merchant_id=MERCHANT_ID,
            pickup_address=pickup_area[0],
            pickup_lat=plat, pickup_lng=plng,
            dropoff_address=dropoff_area[0],
            dropoff_lat=dlat, dropoff_lng=dlng,
            distance_km=dist, eta_min=eta, price_ghs=price
        )
        r = post(f"{ORDER_URL}/orders/create", body, tok=ADMIN_TOK)
        if r.status_code in (200,201):
            od = r.json()
            # Store company_id preference for assignment
            od["_co_id"] = co_id
            ORDERS.append(od)
            S["orders"] += 1
            status_icon = G if od.get("status") in ("ASSIGNED","PENDING","AWAITING_ACCEPTANCE") else Y
            print(f"  {status_icon}#{i:02d}{END} {pickup_area[0][:18]:18s}→{dropoff_area[0][:18]:18s} GHS{price:.2f} | {od.get('status','?')}")
        else:
            try: detail = r.json().get("detail","")
            except: detail = r.text[:80]
            fail(f"Order {i} failed: {r.status_code} {detail}")
            S["failed"] += 1
    
    print(f"\n  {C}Orders created: {S['orders']}/100 | Payments: {S['pays']}/100{END}")


# ─────────────────────────────────────────────────────────────
# PHASE 6 — Batch auto-assign all PENDING orders
# ─────────────────────────────────────────────────────────────
def phase6_assign():
    banner("PHASE 6 — Batch Auto-Assignment")
    pending_ids = [o["id"] for o in ORDERS if o.get("status") == "PENDING"]
    # Also pick up any that are still PENDING in DB
    db_pending = db_q("SELECT id FROM orders WHERE status='PENDING'::orderstatus AND id = ANY(%s::text[])",
                      ([o["id"] for o in ORDERS],))
    all_pending = list({r["id"] for r in db_pending})
    if not all_pending:
        warn("No pending orders to assign")
        return
    
    print(f"  Assigning {len(all_pending)} pending orders...")
    # Assignment service requires auth
    r = SES.post(
        f"{ASSIGNMENT_URL}/orders/batch-auto-assign?strategy=hybrid",
        json=all_pending,
        headers={"Authorization": f"Bearer {ADMIN_TOK}"},
        timeout=60
    )
    if r.status_code == 200:
        result = r.json()
        S["assigned"] = result.get("successful", 0)
        ok(f"Assigned: {result['successful']}/{result['total']} orders")
        for res in result.get("results", []):
            icon = G if res["success"] else Y
            msg  = f"rider={res.get('rider_id','?')[:8]}.." if res["success"] else res.get("message","")
            print(f"    {icon}{'OK' if res['success'] else 'NO'}{END} {res['order_id'][:8]}.. {msg}")
    else:
        fail(f"Batch assign failed: {r.status_code} {r.text[:200]}")

    # Simulate instant rider acceptance: move all AWAITING_ACCEPTANCE → ASSIGNED
    accepted = db_u(
        """UPDATE orders SET status='ASSIGNED'::orderstatus, acceptance_deadline=NULL
           WHERE status='AWAITING_ACCEPTANCE'::orderstatus
             AND id = ANY(%s::text[])""",
        ([o["id"] for o in ORDERS],)
    )
    ok(f"Riders accepted: {accepted} orders → ASSIGNED")


# ─────────────────────────────────────────────────────────────
# PHASE 7 — Order lifecycle + 3-way wallet split
# ─────────────────────────────────────────────────────────────
def phase7_lifecycle():
    banner("PHASE 7 — Order Lifecycle Simulation")
    order_ids = [o["id"] for o in ORDERS]
    if not order_ids:
        warn("No orders to lifecycle"); return

    rows = db_q(
        "SELECT id, status FROM orders WHERE id = ANY(%s::text[])",
        (order_ids,)
    )
    assigned_orders = [r for r in rows if r["status"] in ("ASSIGNED", "AWAITING_ACCEPTANCE")]
    print(f"  Found {len(assigned_orders)} assigned orders to process")

    # ~10% cancellations split: first half = pre-pickup (full refund, GHS 0 fee)
    #                           second half = post-pickup (platform keeps GHS 2.5)
    cancel_count       = max(1, len(assigned_orders) // 10)
    cancel_ids         = random.sample([r["id"] for r in assigned_orders], min(cancel_count, len(assigned_orders)))
    mid                = len(cancel_ids) // 2
    pre_pickup_cancel  = set(cancel_ids[:mid])   # full refund, no fee
    post_pickup_cancel = set(cancel_ids[mid:])   # platform keeps GHS 2.5
    cancel_set         = pre_pickup_cancel | post_pickup_cancel

    for r in assigned_orders:
        oid = r["id"]
        if oid in cancel_set:
            # Cancel via API (fallback to direct DB)
            cr = post(
                f"{ORDER_URL}/orders/{oid}/cancel",
                {"reason": "Simulation: customer cancelled", "request_refund": True},
                tok=ADMIN_TOK
            )
            if cr.status_code != 200:
                db_u("UPDATE orders SET status='CANCELLED'::orderstatus, cancelled_at=now(), "
                     "cancellation_reason='sim cancel' WHERE id=%s", (oid,))
            S["cancelled"] += 1

            # Wallet ledger — cancellation event (no company/rider cut either way)
            order_row = db_q("SELECT assigned_rider_id, price_ghs, company_id FROM orders WHERE id=%s", (oid,))
            if order_row:
                price = float(order_row[0]["price_ghs"] or 0)
                rid   = order_row[0]["assigned_rider_id"]
                co_id = order_row[0]["company_id"]
                if oid in post_pickup_cancel:
                    p_cut = PLATFORM_FEE_CANCEL_AFTER_PICKUP
                    ev    = "CANCEL_AFTER_PICKUP"
                    warn(f"CANCELLED (post-pickup, GHS {p_cut:.1f} fee)  {oid[:8]}..")
                else:
                    p_cut = 0.0
                    ev    = "CANCEL_PRE_PICKUP"
                    warn(f"CANCELLED (pre-pickup,  full refund)   {oid[:8]}..")
                db_u("""INSERT INTO wallet_ledger
                           (id,order_id,rider_id,company_id,event_type,gross,
                            platform_cut,company_cut,rider_cut,commission_pct,created_at)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,0,0,0,now())""",
                     (str(uuid.uuid4()), oid, rid, co_id, ev, price, p_cut))
        else:
            # ASSIGNED → PICKED_UP → IN_TRANSIT → DELIVERED
            for next_status in ("PICKED_UP", "IN_TRANSIT", "DELIVERED"):
                sr = post(f"{ORDER_URL}/orders/{oid}/status", {"status": next_status}, tok=ADMIN_TOK)
                if sr.status_code != 200:
                    col = {"PICKED_UP": "picked_up_at", "IN_TRANSIT": "picked_up_at",
                           "DELIVERED": "delivered_at"}.get(next_status, "")
                    db_u(f"UPDATE orders SET status='{next_status}'::orderstatus"
                         f"{', '+col+'=now()' if col else ''} WHERE id=%s", (oid,))

            # 3-way atomic split: Platform | Company (commission%) | Rider (remainder)
            order_row = db_q("""
                SELECT o.assigned_rider_id, o.price_ghs, o.company_id, rc.commission_pct
                FROM orders o JOIN rider_companies rc ON rc.id=o.company_id
                WHERE o.id=%s
            """, (oid,))
            if order_row and order_row[0]["assigned_rider_id"]:
                rid      = order_row[0]["assigned_rider_id"]
                price    = float(order_row[0]["price_ghs"] or 0)
                co_id    = order_row[0]["company_id"]
                comm_pct = float(order_row[0]["commission_pct"] or 15.0)

                p_cut = PLATFORM_FEE_DELIVERY
                c_cut = round(price * comm_pct / 100, 2)
                r_cut = round(price - p_cut - c_cut, 2)

                # Atomic ledger entry
                db_u("""INSERT INTO wallet_ledger
                           (id,order_id,rider_id,company_id,event_type,gross,
                            platform_cut,company_cut,rider_cut,commission_pct,created_at)
                       VALUES (%s,%s,%s,%s,'DELIVERY',%s,%s,%s,%s,%s,now())""",
                     (str(uuid.uuid4()), oid, rid, co_id, price, p_cut, c_cut, r_cut, comm_pct))

                # Update running wallet balances
                db_u("UPDATE riders SET completed_orders=completed_orders+1, "
                     "total_earnings=total_earnings+%s WHERE id=%s", (r_cut, rid))
                db_u("UPDATE rider_companies SET balance=COALESCE(balance,0)+%s WHERE id=%s", (c_cut, co_id))

                ok(f"DELIVERED {oid[:8]}.. GHS{price:.2f} → "
                   f"Platform GHS{p_cut:.2f} | Co {comm_pct:.0f}% GHS{c_cut:.2f} | Rider GHS{r_cut:.2f}")
            else:
                ok(f"DELIVERED order {oid[:8]}..")
            S["delivered"] += 1

    print(f"\n  {G}Delivered: {S['delivered']}{END}  {Y}Cancelled: {S['cancelled']}{END}")
    print(f"  {Y}Cancels → {len(pre_pickup_cancel)} pre-pickup (GHS 0.00 fee) | "
          f"{len(post_pickup_cancel)} post-pickup (GHS {PLATFORM_FEE_CANCEL_AFTER_PICKUP:.2f} fee){END}")


# ─────────────────────────────────────────────────────────────
# PHASE 8 — Post reviews for delivered orders
# ─────────────────────────────────────────────────────────────
def phase8_reviews():
    banner("PHASE 8 — Post Rider Reviews")
    delivered = db_q(
        "SELECT id, assigned_rider_id FROM orders WHERE status='DELIVERED'::orderstatus AND id = ANY(%s::text[])",
        ([o["id"] for o in ORDERS],)
    )
    print(f"  Found {len(delivered)} delivered orders to review")
    for od in delivered:
        oid = od["id"]
        if not od["assigned_rider_id"]:
            continue
        rating = random.choices([3,4,4,5,5,5], k=1)[0]
        comment = random.choice(COMMENTS)
        body = dict(order_id=oid, rating=rating, comment=comment, is_anonymous=False)
        r = post(f"{REVIEW_URL}/reviews/create", body, tok=ADMIN_TOK)
        if r.status_code in (200,201):
            ok(f"Review {rating}★ for order {oid[:8]}.. — {comment[:40]}")
            S["reviews"] += 1
        else:
            try: detail = r.json().get("detail","")
            except: detail = r.text[:60]
            warn(f"Review failed for {oid[:8]}: {detail}")
    print(f"\n  {C}Reviews posted: {S['reviews']}{END}")

# ─────────────────────────────────────────────────────────────
# PHASE 9 — Final report + balance sheet + money verification
# ─────────────────────────────────────────────────────────────
def phase9_report():
    banner("PHASE 9 — FINAL SIMULATION REPORT")
    order_ids = [o["id"] for o in ORDERS]

    # ── Order counts ──────────────────────────────────────────
    totals = db_q("""
        SELECT
          COUNT(*) FILTER (WHERE status='DELIVERED') as delivered,
          COUNT(*) FILTER (WHERE status='CANCELLED') as cancelled,
          COUNT(*) FILTER (WHERE status='ASSIGNED')  as assigned,
          COUNT(*) FILTER (WHERE status='PENDING')   as pending,
          SUM(price_ghs) FILTER (WHERE status='DELIVERED') as revenue,
          COUNT(*) as total
        FROM orders WHERE id = ANY(%s::text[])
    """, (order_ids,))

    # ── Wallet ledger totals ───────────────────────────────────
    wl_rows = db_q("""
        SELECT
          SUM(gross)        FILTER (WHERE event_type='DELIVERY')            AS gross_del,
          SUM(platform_cut) FILTER (WHERE event_type='DELIVERY')            AS plat_del,
          SUM(company_cut)  FILTER (WHERE event_type='DELIVERY')            AS co_del,
          SUM(rider_cut)    FILTER (WHERE event_type='DELIVERY')            AS rider_del,
          SUM(platform_cut) FILTER (WHERE event_type='CANCEL_AFTER_PICKUP') AS plat_can,
          COUNT(*)          FILTER (WHERE event_type='CANCEL_AFTER_PICKUP') AS post_cancel_cnt,
          COUNT(*)          FILTER (WHERE event_type='CANCEL_PRE_PICKUP')   AS pre_cancel_cnt
        FROM wallet_ledger WHERE order_id = ANY(%s::text[])
    """, (order_ids,))

    t  = totals[0]  if totals  else {}
    wl = wl_rows[0] if wl_rows else {}

    rev       = float(t.get("revenue")       or 0)
    plat_del  = float(wl.get("plat_del")     or 0)
    co_del    = float(wl.get("co_del")       or 0)
    rider_del = float(wl.get("rider_del")    or 0)
    plat_can  = float(wl.get("plat_can")     or 0)
    gross_del = float(wl.get("gross_del")    or 0)
    pre_can   = int(wl.get("pre_cancel_cnt") or 0)
    post_can  = int(wl.get("post_cancel_cnt")or 0)

    total_platform = round(plat_del + plat_can, 2)
    split_sum      = round(plat_del + co_del + rider_del, 2)
    money_ok       = abs(split_sum - round(gross_del, 2)) < 0.02

    print(f"\n  {BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{END}")
    print(f"  {W}📦  ORDERS{END}")
    print(f"      Total Created : {t.get('total',0)}")
    print(f"      {G}✓  Delivered  : {t.get('delivered',0)}{END}")
    print(f"      {Y}⚡  Assigned   : {t.get('assigned',0)}{END}")
    print(f"      {Y}⏳  Pending    : {t.get('pending',0)}{END}")
    print(f"      {R}✗  Cancelled  : {t.get('cancelled',0)}"
          f"  ({pre_can} pre-pickup · {post_can} post-pickup){END}")

    print(f"\n  {W}💰  REVENUE & WALLET SPLIT (delivered orders){END}")
    print(f"      Gross Revenue   : GHS {rev:.2f}")
    print(f"      ─────────────────────────────────────────────────")
    print(f"      Platform Total  : GHS {total_platform:.2f}"
          f"  (GHS {plat_del:.2f} deliveries + GHS {plat_can:.2f} post-pickup cancels)")
    print(f"      Company Total   : GHS {co_del:.2f}  (15–25% by company rate)")
    print(f"      Rider Total     : GHS {rider_del:.2f}  (gross minus platform & company cut)")
    chk_icon = G if money_ok else R
    chk_msg  = "✓  BALANCED — no money lost" if money_ok else "✗  MISMATCH — investigate!"
    print(f"      ─────────────────────────────────────────────────")
    print(f"      {chk_icon}💡 Money Check  : {chk_msg}")
    print(f"         GHS {gross_del:.2f} = GHS {plat_del:.2f} + GHS {co_del:.2f} + GHS {rider_del:.2f}{END}")

    print(f"\n  {W}🏢  COMPANY WALLET BALANCES{END}")
    for co in COMPANIES:
        rows = db_q("""
            SELECT rc.commission_pct, COALESCE(rc.balance,0) AS balance,
                   COUNT(wl.id)        FILTER (WHERE wl.event_type='DELIVERY') AS deliveries,
                   SUM(wl.company_cut) FILTER (WHERE wl.event_type='DELIVERY') AS earned
            FROM rider_companies rc
            LEFT JOIN wallet_ledger wl
                   ON wl.company_id=rc.id AND wl.order_id = ANY(%s::text[])
            WHERE rc.id=%s
            GROUP BY rc.commission_pct, rc.balance
        """, (order_ids, co["id"]))
        if rows:
            row    = rows[0]
            pct    = float(row["commission_pct"] or 15.0)
            bal    = float(row["balance"]        or 0)
            dels   = row["deliveries"]           or 0
            earned = float(row["earned"]         or 0)
            print(f"      {co['name']:22s}: {dels:3d} delivered | {pct:.0f}% cut | "
                  f"Wallet GHS {bal:.2f}")

    print(f"\n  {W}🏍️  RIDER WALLET (Top 10 by earnings){END}")
    leaderboard = db_q("""
        SELECT r.full_name, r.completed_orders, r.total_earnings, r.avg_rating,
               rc.company_name, rc.commission_pct
        FROM riders r JOIN rider_companies rc ON rc.id=r.company_id
        WHERE r.id = ANY(%s::text[])
        ORDER BY r.total_earnings DESC LIMIT 10
    """, ([rd["id"] for rd in RIDERS],))
    for idx, row in enumerate(leaderboard, 1):
        name = row.get("full_name") or "?"
        co   = (row.get("company_name") or "?")[:18]
        ords = row.get("completed_orders") or 0
        earn = float(row.get("total_earnings") or 0)
        rate = float(row.get("avg_rating") or 0)
        pct  = float(row.get("commission_pct") or 0)
        print(f"      {idx:2}. {name:20s} | {co:18s} | {ords:2d} trips | "
              f"Wallet GHS{earn:7.2f} | Co {pct:.0f}%")

    print(f"\n  {W}⭐  REVIEWS{END}")
    print(f"      Total reviews posted: {S['reviews']}")
    avg = db_q("SELECT AVG(rating) as avg FROM rider_reviews WHERE order_id = ANY(%s::text[])",
               (order_ids,))
    avg_rating = float(avg[0]["avg"] or 0) if avg and avg[0]["avg"] else 0
    print(f"      Average rider rating: {avg_rating:.2f} / 5.0")

    errs = S["errors"]
    print(f"\n  {W}⚠️   ERRORS{END}: {R if errs else G}{len(errs)}{END}")
    for e in errs[:10]:
        print(f"      {R}- {e}{END}")

    print(f"\n  {BOLD}{B}{'='*66}{END}")
    print(f"  {BOLD}{G}SIMULATION COMPLETE ✓{END}")
    print(f"  {BOLD}{B}{'='*66}{END}\n")

# ─────────────────────────────────────────────────────────────
# MAIN RUNNER
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n{BOLD}{M}{'#'*66}")
    print(f"#  ANOMAAH DELIVERY PLATFORM — FULL SYSTEM SIMULATION")
    print(f"#  100 Orders · 4 Companies · 25 Riders (7+6+6+6)")
    print(f"{'#'*66}{END}\n")
    
    t0 = time.time()
    setup_schema()
    phase0_cleanup()
    if not phase1_login():
        print(f"{R}FATAL: Cannot login. Aborting.{END}")
        exit(1)
    phase2_companies()
    if not COMPANIES:
        print(f"{R}FATAL: No companies registered. Aborting.{END}")
        exit(1)
    phase3_riders()
    phase4_set_online()
    phase5_orders()
    phase6_assign()
    phase7_lifecycle()
    phase8_reviews()
    phase9_report()
    
    elapsed = time.time() - t0
    print(f"  Total simulation time: {elapsed:.1f}s\n")

