#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# ensure .env exists (will overwrite)
cp .env.example .env
cat > .env <<'EOF'
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=delivery
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/delivery
BOOKING_SERVICE_URL=http://booking-service:8100
PAYMENT_SERVICE_URL=http://payment-service:8200
GOOGLE_MAPS_API_KEY=
HUBTEL_CLIENT_ID=test-client
HUBTEL_CLIENT_SECRET=test-secret
HUBTEL_SMS_SENDER=DELIVERY
HUBTEL_SMS_API=https://api.hubtel.com/v1/messages/sms
PLATFORM_FEE_PERCENT=10
API_HOST=0.0.0.0
API_PORT=8000
NOTIFICATION_SERVICE_URL=http://notification-service:8400
ORDER_SERVICE_URL=http://order-service:8500
TRACKING_SERVICE_URL=http://tracking-service:8300
EOF


echo "Bringing up stack..."
if docker compose version >/dev/null 2>&1; then
  docker compose up -d
elif docker-compose version >/dev/null 2>&1; then
  docker-compose up -d
else
  echo "ERROR: Neither 'docker compose' nor 'docker-compose' is available."
  exit 1
fi

echo "Waiting for services..."
sleep 8

echo "API gateway health:"
curl -sS http://localhost:8000/health || true
echo

# booking payload
cat > /tmp/book_payload.json <<'JSON'
{
  "pickup_address": "Pickup A",
  "pickup_lat": 6.5244,
  "pickup_lng": 3.3792,
  "dropoff_address": "Dropoff B",
  "dropoff_lat": 6.435,
  "dropoff_lng": 3.4475,
  "phone": "08012345678"
}
JSON

echo "Calling gateway /book..."
curl -sS -X POST "http://localhost:8000/book" -H "Content-Type: application/json" -d @/tmp/book_payload.json -o /tmp/book_resp.json || true
echo "Booking response:"
python3 - <<'PY'
import json,pprint
try:
    r=json.load(open('/tmp/book_resp.json'))
    pprint.pprint(r)
except Exception as e:
    print("No booking response:", e)
PY

PAY_ID=$(python3 - <<'PY'
import json,sys
try:
    r=json.load(open('/tmp/book_resp.json'))
    pp=r.get('payment_payload') or {}
    if isinstance(pp, dict):
        pid=pp.get('payment_id') or pp.get('token') or ''
        print(pid)
except:
    pass
PY
)

echo "Extracted payment_id: $PAY_ID"

if [ -n "$PAY_ID" ]; then
  echo "Simulating payment notify for $PAY_ID..."
  curl -sS -X POST "http://localhost:8200/payments/mock_notify/$PAY_ID" -o /tmp/mock_notify.json || true
  echo "Mock notify response:"
  python3 - <<'PY'
import json
try:
    print(json.load(open('/tmp/mock_notify.json')))
except:
    print("no mock notify response")
PY
  echo "Payment status:"
  curl -sS http://localhost:8200/payments/status/$PAY_ID | python3 -m json.tool || true
else
  echo "No payment id returned by booking; check /tmp/book_resp.json"
fi

echo "Listing orders (tenant endpoint requires X-Tenant-ID):"
curl -sS -H "X-Tenant-ID: tenant_1" http://localhost:8500/orders/tenant | python3 -m json.tool || true

echo "Creating a manual order (if none exists)..."
ORDER_RESP=$(curl -sS -X POST "http://localhost:8500/orders/create" -H "Content-Type: application/json" -d '{"payment_id":"'"${PAY_ID:-manual}"'","amount":1000,"currency":"GHS","phone":"08012345678","metadata":{"tenant_id":"tenant_1","dropoff":{"lat":6.435,"lng":3.4475}}}')
echo "$ORDER_RESP" | python3 -m json.tool || true
ORDER_ID=$(python3 - <<'PY'
import json,sys
r=json.loads('''$ORDER_RESP''')
print(r.get('order_id',''))
PY
)

echo "Order ID: $ORDER_ID"

if [ -n "$ORDER_ID" ]; then
  echo "Assigning rider to order..."
  curl -sS -X POST "http://localhost:8500/orders/$ORDER_ID/assign" \
    -H "Content-Type: application/json" -H "X-Tenant-ID: tenant_1" \
    -d '{"rider_id":"rider_1","bike_id":"bike_1"}' -o /tmp/assign_resp.json || true
  echo "Assign response:"
  python3 - <<'PY'
import json,pprint
try:
    r=json.load(open('/tmp/assign_resp.json'))
    pprint.pprint(r)
except:
    print("no assign response")
PY

  # If tracking started, show the public link info
  python3 - <<'PY'
import json,sys
try:
    r=json.load(open('/tmp/assign_resp.json'))
    order=r.get('order') or {}
    tracking=order.get('tracking') or r.get('tracking') or {}
    print("tracking:", tracking)
except:
    print("no tracking info")
PY
fi

echo "Smoke test complete. If you want logs for debugging, run:"
echo "  docker compose logs api-gateway --tail=200"
echo "  docker compose logs booking-service --tail=200"
echo "  docker compose logs payment-service --tail=200"
echo "  docker compose logs order-service --tail=200"
echo "  docker compose logs tracking-service --tail=200"
echo "  docker compose logs notification-service --tail=200"
