Tracking Service (MVP)

Endpoints:
- POST /tracking/start -> start a tracking session (returns `tracking_id` and public link)
- POST /tracking/update/{tracking_id} -> rider app posts GPS updates and status
- GET /tracking/public/{tracking_id} -> public view (no auth) with last location, ETA, status
- GET /tracking/internal/{tracking_id} -> internal debug view (tenant auth to add later)

Notes:
- Uses an in-memory store for sessions (MVP). Replace with persistent DB or Redis for scale.
- Public link expires after `TRACKING_TTL_SECONDS`.
- ETA is a simple estimate based on straight-line distance and assumed speed.
