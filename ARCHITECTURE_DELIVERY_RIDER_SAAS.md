📐 SYSTEM ARCHITECTURE – DELIVERY RIDER SAAS (MVP)

🧠 PLATFORM OVERVIEW

A multi-tenant delivery infrastructure SaaS where:

Multiple rider companies (tenants) operate independently

End users book deliveries via a single public booking page

Payments are processed before assignment

Riders are manually assigned

Live tracking is shared via a public link

Platform owner provides infra only (no operations)

---

🏗️ HIGH-LEVEL COMPONENTS

[ PUBLIC USER ]
      |
      v
[ 1-PAGE BOOKING PAGE ]
      |
      v
[ API GATEWAY / BACKEND ]
      |
      |-------------------------------|
      |                               |
      v                               v
[ ORDER SERVICE ]              [ PAYMENT SERVICE ]
      |                               |
      v                               v
[ TENANT-AWARE DATABASE ]      [ HUBTEL API ]
      |
      |
      |--------------------------------------------|
      |                                            |
      v                                            v
[ RIDER COMPANY DASHBOARD ]               [ SMS SERVICE ]
      |                                            |
      v                                            v
[ RIDER APP / RIDER VIEW ]                [ CEDCAST API ]
      |
      v
[ LIVE TRACKING SERVICE ]
      |
      v
[ PUBLIC TRACKING LINK ]


---

🧩 CORE SERVICES (MVP)

1️⃣ Auth & Tenant Service

Purpose:

Authenticate Super Admin

Authenticate Rider Company Managers

Authenticate Riders

Enforce tenant isolation


Rules:

Every rider, bike, and order belongs to one tenant

Super Admin bypasses tenant restriction


---

2️⃣ Booking Service (Public)

Purpose:

Handle 1-page booking

Accept pickup & dropoff locations

Calculate:

Distance

ETA

Price


Uses:

Google Maps API (distance + traffic)


Rules:

No user accounts

Phone number is the user identifier


---

3️⃣ Order Service

Purpose:

Create and manage delivery orders


Order States:

CREATED
PAID
ASSIGNED
PICKED_UP
DELIVERED
CANCELLED
REFUNDED


Rules:

Orders are created only after payment

Refund allowed ONLY if status < PICKED_UP


---

4️⃣ Payment Service

Purpose:

Handle payment initiation

Verify Hubtel callbacks

Hold funds until delivery completion


Rules:

Platform fee deducted per order

Payout handled by Hubtel

No internal wallet in MVP


---

5️⃣ Rider Assignment Service

Purpose:

Allow manual assignment by rider companies


Rules:

Only tenant owner can assign their riders

One rider → one active order at a time (MVP)


---

6️⃣ Tracking Service

Purpose:

Track rider GPS location during active delivery

Generate public tracking link


Tracking Link Shows:

Live rider position

ETA

Order status


Rules:

No login required

Link expires after delivery


---

7️⃣ Notification Service

Purpose:

Send SMS notifications


Events:

Order placed

Rider assigned

Pickup confirmed

Delivery completed

Tracking link sent


Uses:

CedCast SMS API


---

8️⃣ Review Service (Basic)

Purpose:

Allow users to rate completed deliveries


Rules:

One review per order

Tied to rider & rider company

No moderation in MVP


---

🗄️ DATA MODEL (CONCEPTUAL – NO SCHEMA YET)

Entities:

Tenant (Rider Company)
User (Admin, Manager, Rider)
Bike
Order
Payment
TrackingSession
Review

Key Relationships:

Tenant → has many Riders

Tenant → has many Bikes

Tenant → has many Orders

Order → assigned to one Rider + Bike

Order → has one TrackingSession

Order → has one Payment

Order → may have one Review


---

🔐 TENANCY ENFORCEMENT (CRITICAL)

Every request must answer:

Which tenant does this belong to?

Rules:

Tenant ID attached to:

Orders

Riders

Bikes


Queries always filtered by tenant

Super Admin bypasses filters


---

🌍 REGIONAL LOGIC (MVP SIMPLE)

Cities are not tenants

Tenants declare supported cities
