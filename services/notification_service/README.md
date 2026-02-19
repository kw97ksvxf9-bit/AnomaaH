Notification Service (Hubtel SMS)

Endpoints:
- POST /sms/send  -> send a raw SMS via Hubtel
- POST /notify/event -> send event-based SMS (order_placed, rider_assigned, pickup_confirmed, delivery_completed, tracking_link)

Configuration via environment variables:
- HUBTEL_CLIENT_ID
- HUBTEL_CLIENT_SECRET
- HUBTEL_SMS_SENDER (default: DELIVERY)
- HUBTEL_SMS_API (default: https://api.hubtel.com/v1/messages/sms)

Notes:
- This service uses Hubtel's SMS API. For production, add retry/backoff, rate limiting, and delivery status callbacks.
- Store messages & delivery status in a DB for auditing in production.
