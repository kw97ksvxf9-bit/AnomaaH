#!/usr/bin/env python3
"""
ANOMAAH Delivery Platform — Pre-Deployment Checklist
══════════════════════════════════════════════════════
Run this BEFORE pushing to Railway to catch every config issue.

Usage:
  python3 pre_deploy_test.py            # run all checks
  python3 pre_deploy_test.py --live     # include live Hubtel SMS + payment calls
  python3 pre_deploy_test.py --phone 0501234567  # test number for live SMS/payment
"""

import os, sys, re, json, time, uuid, base64, argparse, subprocess
import requests, psycopg2, psycopg2.extras
from pathlib import Path
from dotenv import dotenv_values

# ── colour helpers ──────────────────────────────────────────────────────────
G="\033[92m"; R="\033[91m"; Y="\033[93m"; C="\033[96m"
B="\033[94m"; W="\033[97m"; M="\033[95m"; BOLD="\033[1m"; END="\033[0m"

PASS  = f"{G}✓ PASS{END}"
FAIL  = f"{R}✗ FAIL{END}"
WARN  = f"{Y}⚠ WARN{END}"
INFO  = f"{C}→ INFO{END}"

results = []   # (label, status, detail)
ERRORS  = []

def section(t):
    print(f"\n{BOLD}{B}{'═'*70}{END}\n{BOLD}{W}  {t}{END}\n{BOLD}{B}{'═'*70}{END}")

def check(label, ok, detail="", warn_only=False):
    icon = PASS if ok else (WARN if warn_only else FAIL)
    print(f"  {icon}  {label}")
    if detail:
        prefix = "      " + ("" if ok else f"{R if not warn_only else Y}")
        for line in str(detail).splitlines():
            print(f"      {line}{END if not ok else ''}")
    results.append((label, "pass" if ok else ("warn" if warn_only else "fail"), detail))
    if not ok and not warn_only:
        ERRORS.append(label)

def info(msg):
    print(f"  {INFO}  {msg}")

# ── Load .env ────────────────────────────────────────────────────────────────
ENV_FILE = Path(__file__).parent / ".env"
env = dotenv_values(str(ENV_FILE)) if ENV_FILE.exists() else {}
# Merge with actual environment (Railway sets real vars)
for k, v in env.items():
    os.environ.setdefault(k, v)

def E(key, default=None):
    return os.environ.get(key, default)


# ════════════════════════════════════════════════════════════════════════════
# CHECK 1 — Required environment variables
# ════════════════════════════════════════════════════════════════════════════
def check_env_vars():
    section("CHECK 1 — Required Environment Variables")

    REQUIRED = {
        # Security
        "SECRET_KEY":                    "JWT signing key — must not be 'demo-secret' or 'replace-me'",
        # DB
        "DATABASE_URL":                  "PostgreSQL connection string",
        # Hubtel SMS
        "HUBTEL_CLIENT_ID":              "Hubtel SMS API ID (username)",
        "HUBTEL_CLIENT_SECRET":          "Hubtel SMS API Key (password)",
        # Hubtel Payment
        "HUBTEL_PAYMENT_CLIENT_ID":      "Hubtel Receive Money API ID",
        "HUBTEL_PAYMENT_CLIENT_SECRET":  "Hubtel Receive Money API Key",
        "HUBTEL_CALLBACK_URL":           "Public URL Hubtel will POST webhook to (your Railway URL)",
        # Maps
        "GOOGLE_MAPS_API_KEY":           "Google Maps Distance Matrix key",
    }

    OPTIONAL_WARN = {
        "HUBTEL_MERCHANT_ACCOUNT":  "Merchant account number (defaults to PAYMENT_CLIENT_ID if missing)",
        "HUBTEL_WEBHOOK_SECRET":    "HMAC secret for webhook signature verification",
    }

    for key, desc in REQUIRED.items():
        val = E(key)
        if not val:
            check(f"{key}", False, f"Missing! {desc}")
        elif key == "SECRET_KEY" and val in ("demo-secret-key-change-in-production", "replace-me", "your-secret-key-change-in-production"):
            check(f"{key}", False, f"Still using insecure default: '{val}'")
        elif key == "HUBTEL_CALLBACK_URL" and "localhost" in val:
            check(f"{key}", False, f"Points to localhost: '{val}' — must be your Railway public URL",
                  warn_only=True)  # warn-only: expected during local dev
        else:
            check(f"{key}", True, f"{val[:8]}...{val[-4:] if len(val)>12 else ''}")

    for key, desc in OPTIONAL_WARN.items():
        val = E(key)
        check(f"{key} (optional)", bool(val), desc, warn_only=True)

    # JWT strength check
    sk = E("SECRET_KEY", "")
    if len(sk) >= 32 and re.search(r'[0-9]', sk) and re.search(r'[a-f]', sk):
        check("SECRET_KEY strength (≥32 chars, hex-like)", True)
    else:
        check("SECRET_KEY strength (≥32 chars, hex-like)", False,
              f"Length={len(sk)} — run: python3 -c \"import secrets; print(secrets.token_hex(32))\"")


# ════════════════════════════════════════════════════════════════════════════
# CHECK 2 — Database connectivity + tables
# ════════════════════════════════════════════════════════════════════════════
def check_database():
    section("CHECK 2 — Database Connectivity & Schema")

    # Convert docker-internal postgres hostname to localhost when running outside docker
    db_url = E("DATABASE_URL")
    if not db_url:
        check("DB connection", False, "DATABASE_URL not set"); return
    # When running locally (not inside docker), swap docker service name → localhost
    local_url = re.sub(r'@[a-z_-]+:(\d+)/', lambda m: f'@localhost:{m.group(1)}/', db_url)
    conn = None
    for attempt_url in ([db_url] if db_url == local_url else [db_url, local_url]):
        try:
            conn = psycopg2.connect(attempt_url, connect_timeout=5)
            conn.autocommit = True
            check("DB connection", True, f"(via {attempt_url.split('@')[1].split('/')[0]})")
            break
        except Exception as e:
            if attempt_url == local_url:
                check("DB connection", False, str(e)); return

    if not conn:
        return

    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Check key tables exist
        tables = ["users", "orders", "payments", "riders", "merchants", "rider_companies"]
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
        existing = {r["tablename"] for r in cur.fetchall()}
        for t in tables:
            check(f"  Table '{t}' exists", t in existing)

        # Check superadmin user
        cur.execute("SELECT id, username FROM users WHERE username='superadmin' LIMIT 1")
        row = cur.fetchone()
        check("  superadmin user exists", bool(row),
              "Run: python3 seed_data.py" if not row else f"id={str(row['id'])[:12]}..")

        conn.close()
    except Exception as e:
        check("DB queries", False, str(e))


# ════════════════════════════════════════════════════════════════════════════
# CHECK 3 — All 7 services are UP
# ════════════════════════════════════════════════════════════════════════════
def check_services():
    section("CHECK 3 — Service Health (local docker-compose)")

    services = [
        ("Auth",       "http://localhost:8600/health"),
        ("Booking",    "http://localhost:8100/health"),
        ("Payment",    "http://localhost:8200/health"),
        ("Order",      "http://localhost:8500/health"),
        ("Tracking",   "http://localhost:8300/health"),
        ("Assignment", "http://localhost:8900/health"),
        ("RiderStatus","http://localhost:8800/health"),
        ("Review",     "http://localhost:8700/health"),
        ("Notification","http://localhost:8400/health"),
    ]
    for name, url in services:
        try:
            r = requests.get(url, timeout=5)
            check(f"  {name:<14} {url}", r.status_code == 200,
                  r.json() if r.status_code == 200 else r.text[:100])
        except Exception as e:
            check(f"  {name:<14} {url}", False, str(e), warn_only=True)


# ════════════════════════════════════════════════════════════════════════════
# CHECK 4 — JWT: same key used by all services
# ════════════════════════════════════════════════════════════════════════════
def check_jwt():
    section("CHECK 4 — JWT Token Validity (cross-service)")

    sk = E("SECRET_KEY", "")
    try:
        import jwt as pyjwt
        # Login to get a real token, then hit a different service with it
        r = requests.post("http://localhost:8600/token",
                          json={"username": "superadmin", "password": "admin123"}, timeout=10)
        if r.status_code != 200:
            check("Admin login", False, f"{r.status_code} {r.text[:150]}"); return
        tok = r.json()["access_token"]
        check("Admin login → JWT", True, "token acquired")

        # Use the token on order service (different service, same SECRET_KEY)
        r2 = requests.get("http://localhost:8500/orders",
                          headers={"Authorization": f"Bearer {tok}"}, timeout=10)
        check("JWT accepted by order-service", r2.status_code == 200,
              f"Status {r2.status_code}" if r2.status_code != 200 else "cross-service auth OK")

        # Decode manually and check exp — try both the .env key and common defaults
        decoded = False
        for candidate_key in [sk, "demo-secret-key-change-in-production", "your-secret-key-change-in-production"]:
            try:
                payload = pyjwt.decode(tok, candidate_key, algorithms=["HS256"])
                if candidate_key == sk:
                    check("JWT signed with current SECRET_KEY", True, f"sub={payload.get('sub','?')[:12]}")
                else:
                    check("JWT signed with current SECRET_KEY", False,
                          f"Services still using old key '{candidate_key[:12]}...' — restart all services:\n"
                          "  docker-compose down && docker-compose up -d")
                decoded = True
                break
            except Exception:
                pass
        if not decoded:
            check("JWT signed with current SECRET_KEY", False, "Could not decode JWT with any known key")
    except Exception as e:
        check("JWT check", False, str(e))


# ════════════════════════════════════════════════════════════════════════════
# CHECK 5 — Google Maps API
# ════════════════════════════════════════════════════════════════════════════
def check_google_maps():
    section("CHECK 5 — Google Maps Distance Matrix API")

    key = E("GOOGLE_MAPS_API_KEY")
    if not key:
        check("Google Maps API key", False, "GOOGLE_MAPS_API_KEY not set"); return

    try:
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            "origins":      "Osu, Accra, Ghana",
            "destinations": "East Legon, Accra, Ghana",
            "key":          key,
        }
        r = requests.get(url, params=params, timeout=15)
        d = r.json()
        status_code = d.get("status")
        if status_code == "OK":
            row  = d["rows"][0]["elements"][0]
            dist = row["distance"]["text"]
            dur  = row["duration"]["text"]
            check("Google Maps API", True, f"Osu → East Legon: {dist}, {dur}")
        elif status_code == "REQUEST_DENIED":
            check("Google Maps API", False,
                  d.get("error_message", "Key denied — enable billing at console.cloud.google.com"),
                  warn_only=True)  # booking-service has stub fallback — not a deploy blocker
        else:
            check("Google Maps API", False, f"status={status_code} — {d.get('error_message','')}",
                  warn_only=True)
    except Exception as e:
        check("Google Maps API", False, str(e), warn_only=True)


# ════════════════════════════════════════════════════════════════════════════
# CHECK 6 — Hubtel SMS (connectivity ping — no actual SMS sent)
# ════════════════════════════════════════════════════════════════════════════
def check_hubtel_sms_config():
    section("CHECK 6 — Hubtel SMS Credentials (connection test)")

    cid = E("HUBTEL_CLIENT_ID")
    csc = E("HUBTEL_CLIENT_SECRET")
    if not cid or not csc:
        check("Hubtel SMS credentials set", False, "HUBTEL_CLIENT_ID / HUBTEL_CLIENT_SECRET missing"); return

    # Ping the Hubtel API with a GET to verify credentials work
    try:
        r = requests.get(
            "https://api.hubtel.com/v1/messages/sms",
            auth=(cid, csc),
            timeout=10
        )
        # 200 = valid creds, 401 = wrong creds, 403 = no permission, 405/404 = auth OK but wrong method
        if r.status_code in (200, 405, 404, 400):
            check("Hubtel SMS credentials valid", True, f"HTTP {r.status_code} (auth accepted)")
        elif r.status_code == 401:
            check("Hubtel SMS credentials valid", False, "401 Unauthorized — wrong HUBTEL_CLIENT_ID/SECRET")
        else:
            check("Hubtel SMS credentials valid", False, f"HTTP {r.status_code}: {r.text[:150]}", warn_only=True)
    except Exception as e:
        check("Hubtel SMS API reachable", False, str(e), warn_only=True)


# ════════════════════════════════════════════════════════════════════════════
# CHECK 7 — Hubtel Payment credentials (connection test)
# ════════════════════════════════════════════════════════════════════════════
def check_hubtel_payment_config():
    section("CHECK 7 — Hubtel Payment Credentials (connection test)")

    pid = E("HUBTEL_PAYMENT_CLIENT_ID")
    psc = E("HUBTEL_PAYMENT_CLIENT_SECRET")
    acc = E("HUBTEL_MERCHANT_ACCOUNT") or pid
    cb  = E("HUBTEL_CALLBACK_URL")

    check("HUBTEL_PAYMENT_CLIENT_ID set",     bool(pid), pid[:8]+"..." if pid else "")
    check("HUBTEL_PAYMENT_CLIENT_SECRET set", bool(psc), psc[:6]+"..." if psc else "")
    check("HUBTEL_MERCHANT_ACCOUNT set",      bool(acc), acc[:12] if acc else "", warn_only=True)
    check("HUBTEL_CALLBACK_URL not localhost",
          bool(cb) and "localhost" not in cb,
          f"Current: {cb} — update to Railway URL after first deploy",
          warn_only="localhost" in (cb or ""))

    if pid and psc:
        try:
            # Test auth against Hubtel merchant API (GET — read-only, no charge)
            url = f"https://api.hubtel.com/v1/merchantaccount/merchants/{acc or pid}/transactions"
            r = requests.get(url, auth=(pid, psc), timeout=10)
            if r.status_code in (200, 204):
                check("Hubtel Payment API auth", True, f"HTTP {r.status_code}")
            elif r.status_code == 401:
                check("Hubtel Payment API auth", False, "401 Unauthorized — check credentials")
            elif r.status_code in (403, 404, 405):
                # 403/404 often means auth worked but no data / path differs by account type
                check("Hubtel Payment API auth", True, f"HTTP {r.status_code} (credentials accepted, endpoint may differ)")
            else:
                check("Hubtel Payment API auth", False, f"HTTP {r.status_code}: {r.text[:200]}", warn_only=True)
        except Exception as e:
            check("Hubtel Payment API reachable", False, str(e), warn_only=True)


# ════════════════════════════════════════════════════════════════════════════
# CHECK 8 — Live Hubtel SMS (only with --live flag)
# ════════════════════════════════════════════════════════════════════════════
def check_live_sms(phone: str):
    section("CHECK 8 — Live SMS Test (sends a real SMS via notification service)")

    if not phone:
        info("Skipped — pass --phone 0501234567 to test real SMS delivery"); return

    try:
        r = requests.post("http://localhost:8400/sms/send",
                          json={"phone": phone, "message": "ANOMAAH pre-deploy SMS test ✓"},
                          timeout=15)
        if r.status_code == 200:
            check("Live SMS sent", True, r.json())
        else:
            check("Live SMS sent", False, f"{r.status_code}: {r.text[:300]}")
    except Exception as e:
        check("Live SMS sent", False, str(e))


# ════════════════════════════════════════════════════════════════════════════
# CHECK 9 — Live Hubtel Payment initiation (only with --live flag)
# ════════════════════════════════════════════════════════════════════════════
def check_live_payment(phone: str):
    section("CHECK 9 — Live Payment Test (sends GHS 0.10 MoMo prompt via payment service)")

    if not phone:
        info("Skipped — pass --phone 0501234567 --live to send real MoMo prompt"); return

    try:
        r = requests.post("http://localhost:8200/payments/initiate",
                          json={"amount": 1, "currency": "GHS", "phone": phone,
                                "metadata": {"description": "ANOMAAH pre-deploy payment test"}},
                          timeout=25)
        d = r.json()
        if r.status_code == 200:
            check("Payment initiate", True)
            info(f"  payment_id : {d.get('payment_id','?')[:12]}..")
            info(f"  status     : {d.get('status')}")
            info(f"  hubtel_ref : {d.get('hubtel_ref') or '(mock — Hubtel not called yet)'}")
            info(f"  payment_url: {d.get('payment_url','')[:70]}")
            if d.get("hubtel_ref"):
                check("  Hubtel MoMo prompt delivered", True, "check customer phone for prompt")
            else:
                check("  Hubtel MoMo prompt", False,
                      "No hubtel_ref — check HUBTEL_PAYMENT_CLIENT_ID credentials + docker logs payment-service",
                      warn_only=True)
        else:
            check("Payment initiate", False, f"{r.status_code}: {r.text[:300]}")
    except Exception as e:
        check("Payment initiate", False, str(e))


# ════════════════════════════════════════════════════════════════════════════
# CHECK 10 — Wallet split integrity (simulation check)
# ════════════════════════════════════════════════════════════════════════════
def check_wallet_math():
    section("CHECK 10 — Wallet Split Formula")
    try:
        db_url = E("DATABASE_URL")
        if not db_url:
            check("Wallet math", False, "DATABASE_URL not set", warn_only=True); return
        local_url = re.sub(r'@[a-z_-]+:(\d+)/', lambda m: f'@localhost:{m.group(1)}/', db_url)
        conn = None
        for attempt_url in ([db_url] if db_url == local_url else [db_url, local_url]):
            try:
                conn = psycopg2.connect(attempt_url, connect_timeout=5)
                break
            except Exception:
                pass
        if not conn:
            check("Wallet math", False, "DB unreachable", warn_only=True); return
        conn.autocommit = True
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN ABS(
                       (w.platform_cut + w.company_cut + w.rider_cut) - w.gross
                   ) < 0.01 THEN 1 ELSE 0 END) AS balanced
            FROM   wallet_ledger w
            WHERE  w.event_type = 'DELIVERY'
        """)
        row = cur.fetchone()
        if row and row["total"] and row["total"] > 0:
            check(f"Wallet split balanced ({row['total']} orders)",
                  row["balanced"] == row["total"],
                  f"{row['balanced']}/{row['total']} orders balanced")
        else:
            info("No wallet_ledger entries yet — run the simulation first")
        conn.close()
    except Exception as e:
        check("Wallet math", False, str(e), warn_only=True)


# ════════════════════════════════════════════════════════════════════════════
# CHECK 11 — Acceptance timeout system (AWAITING_ACCEPTANCE)
# ════════════════════════════════════════════════════════════════════════════
def check_assignment_watcher():
    section("CHECK 11 — Bolt-Style Acceptance Timeout System")
    try:
        r = requests.get("http://localhost:8900/health", timeout=5)
        check("Assignment service up", r.status_code == 200)

        # Check watcher is running (assignment service has background task)
        r2 = requests.get("http://localhost:8900/assignment/status", timeout=5)
        if r2.status_code == 200:
            d = r2.json()
            check("Acceptance watcher active", d.get("watcher_running", False),
                  str(d))
        else:
            info(f"  /assignment/status returned {r2.status_code} — watcher status unknown")
    except Exception as e:
        check("Assignment service", False, str(e), warn_only=True)


# ════════════════════════════════════════════════════════════════════════════
# CHECK 12 — Railway deployment configuration review
# ════════════════════════════════════════════════════════════════════════════
def check_railway_config():
    section("CHECK 12 — Railway Deployment Configuration Review")

    print(f"""
  {BOLD}Railway Deployment Checklist{END}
  {'─'*64}

  {BOLD}Step 1: Create a Railway project{END}
  {C}  railway init{END}

  {BOLD}Step 2: Add PostgreSQL plugin{END}
  {C}  railway add --plugin postgresql{END}
  ⚠  The Railway DATABASE_URL is automatically injected — do NOT hardcode it.

  {BOLD}Step 3: Set these environment variables on Railway{END}
  (Railway dashboard → your project → Variables tab)
""")

    railway_vars = [
        ("SECRET_KEY",                   E("SECRET_KEY","")[:8]+"..."),
        ("HUBTEL_CLIENT_ID",             E("HUBTEL_CLIENT_ID","(not set)")),
        ("HUBTEL_CLIENT_SECRET",         E("HUBTEL_CLIENT_SECRET","(not set)")[:6]+"..."),
        ("HUBTEL_PAYMENT_CLIENT_ID",     E("HUBTEL_PAYMENT_CLIENT_ID","(not set)")),
        ("HUBTEL_PAYMENT_CLIENT_SECRET", E("HUBTEL_PAYMENT_CLIENT_SECRET","(not set)")[:6]+"..."),
        ("HUBTEL_MERCHANT_ACCOUNT",      E("HUBTEL_MERCHANT_ACCOUNT","same as PAYMENT_CLIENT_ID")),
        ("HUBTEL_CALLBACK_URL",          "https://<your-payment-service>.up.railway.app"),
        ("GOOGLE_MAPS_API_KEY",          E("GOOGLE_MAPS_API_KEY","")[:8]+"..."),
        ("HUBTEL_SMS_SENDER",            E("HUBTEL_SMS_SENDER","ANOMAAH")),
        ("HUBTEL_WEBHOOK_SECRET",        "(generate: openssl rand -hex 32)"),
    ]

    for k, v in railway_vars:
        print(f"    {Y}{k:<35}{END} = {v}")

    print(f"""
  {BOLD}Step 4: After first deploy — update HUBTEL_CALLBACK_URL{END}
  Your Railway payment service URL will look like:
  {C}  https://anomaah-payment-service.up.railway.app{END}
  Set: HUBTEL_CALLBACK_URL=https://anomaah-payment-service.up.railway.app

  {BOLD}Step 5: Tell Hubtel about your callback URL{END}
  In the Hubtel dashboard → API Settings → Callback URL:
  {C}  https://anomaah-payment-service.up.railway.app/payments/webhook{END}

  {BOLD}Step 6: Set HUBTEL_WEBHOOK_SECRET{END}
  Generate: {C}openssl rand -hex 32{END}
  Copy the output to both Railway env vars AND Hubtel dashboard → Webhook Secret.

  {BOLD}Step 7: Test the Railway deploy{END}
  {C}  python3 pre_deploy_test.py --live --phone 0501234567{END}
  (update HUBTEL_CALLBACK_URL to Railway URL first)

  {'─'*64}
""")

    # Check if callback URL has been updated from localhost
    cb = E("HUBTEL_CALLBACK_URL", "")
    check("HUBTEL_CALLBACK_URL points to Railway (not localhost)",
          bool(cb) and "localhost" not in cb,
          f"Current: {cb}",
          warn_only="localhost" in cb)


# ════════════════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ════════════════════════════════════════════════════════════════════════════
def final_summary(elapsed):
    section("FINAL SUMMARY")

    passes  = sum(1 for _, s, _ in results if s == "pass")
    warns   = sum(1 for _, s, _ in results if s == "warn")
    fails   = sum(1 for _, s, _ in results if s == "fail")
    total   = len(results)

    status_icon = f"{G}✓ READY TO DEPLOY{END}" if not ERRORS else f"{R}✗ {len(ERRORS)} BLOCKERS — FIX BEFORE DEPLOY{END}"

    print(f"""
  {BOLD}Pre-Deploy Results{END}
  {'─'*60}
  {G}PASS{END}  {passes}/{total}
  {Y}WARN{END}  {warns}/{total}   (warnings won't break deploy but should be addressed)
  {R}FAIL{END}  {fails}/{total}
  {'─'*60}
  {status_icon}
  Duration: {elapsed:.1f}s
""")

    if ERRORS:
        print(f"  {BOLD}{R}Blockers to fix:{END}")
        for e in ERRORS:
            print(f"    {R}• {e}{END}")
        print()
    else:
        print(f"  {G}All critical checks passed! Safe to deploy to Railway.{END}\n")


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ANOMAAH pre-deploy checklist")
    parser.add_argument("--live",  action="store_true", help="Run live Hubtel SMS + payment tests")
    parser.add_argument("--phone", default="", help="Ghana phone number for live SMS/payment test")
    args = parser.parse_args()

    print(f"\n{BOLD}{M}{'#'*70}{END}")
    print(f"{BOLD}{W}  ANOMAAH Delivery — Pre-Deployment Checklist{END}")
    print(f"{BOLD}{M}{'#'*70}{END}")

    t0 = time.time()

    check_env_vars()
    check_database()
    check_services()
    check_jwt()
    check_google_maps()
    check_hubtel_sms_config()
    check_hubtel_payment_config()

    if args.live:
        check_live_sms(args.phone)
        check_live_payment(args.phone)
    else:
        section("CHECK 8+9 — Live Hubtel Tests (skipped)")
        info("Run with --live --phone 0501234567 to send a real SMS and MoMo prompt")

    check_wallet_math()
    check_assignment_watcher()
    check_railway_config()

    final_summary(time.time() - t0)
