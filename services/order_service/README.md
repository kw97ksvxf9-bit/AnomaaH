Order & Assignment Service (MVP)

Endpoints:
- POST /orders/create -> create an order after payment (called by Payment service)
- GET /orders/{order_id} -> get order details
- GET /orders/tenant -> list orders for tenant (requires `X-Tenant-ID` header)
- POST /orders/{order_id}/assign -> assign a rider (requires `X-Tenant-ID` header). Starts tracking and notifies user.

Notes:
- Uses in-memory store for MVP. Replace with persistent DB in production.
- Assignment requires tenant header to enforce tenant isolation (MVP simple enforcement).
- When assigning, if `TRACKING_SERVICE_URL` is configured, order service will start a tracking session and attach tracking info to the order.
