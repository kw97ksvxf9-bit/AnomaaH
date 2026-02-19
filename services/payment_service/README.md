Payment Service (MVP)

Endpoints:
- POST /payments/initiate  -> initiate a payment (returns payment_url)
- GET /payments/mock_pay/{payment_id} -> simulate a payment page
- POST /payments/mock_notify/{payment_id} -> simulate Hubtel callback
- POST /payments/callback -> webhook for Hubtel to notify payment status
- GET /payments/status/{payment_id} -> check payment status

Notes:
- This service uses an in-memory store for payments (MVP). Replace with persistent DB for production.
- Implement proper Hubtel signature verification when wiring real credentials.
