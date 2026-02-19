Delivery Rider SaaS (MVP)

Overview

A multi-tenant delivery infrastructure SaaS (MVP) supporting:
- Public 1-page booking (no accounts)
- Hubtel payments
- Manual rider assignment per tenant
- Live public tracking links
- CedCast SMS notifications

Quickstart (local, development)

1. Copy environment example:

   cp .env.example .env

2. Start Postgres and services (docker-compose):

```bash
docker-compose up --build
```

3. Open the API gateway:

- API Gateway: http://localhost:8000
- Booking service: http://localhost:8100

MVP Roadmap

- Enforce strict tenant isolation middleware
- Booking service: Google Maps distance/ETA + price calc
- Payment service: Hubtel integration & webhook verification
- Order service: state machine and tenant-aware models
- Tracking service: public tracking links + session expiry
- Notification service: CedCast SMS event hooks

Repository layout

- ARCHITECTURE_DELIVERY_RIDER_SAAS.md  (system architecture)
- docker-compose.yml
- .env.example
- services/
  - api_gateway/
  - booking_service/
  - payment_service/
  - order_service/
  - auth_service/
  - tracking_service/
  - notification_service/
  - shared/  (tenant middleware, common models)

Next steps

- Implement tenant middleware and tests
- Scaffold simple DB models and migrations
- Implement Booking → Payment flow
