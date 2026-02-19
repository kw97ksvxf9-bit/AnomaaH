import os
from fastapi import FastAPI, Request, Depends
import httpx
from shared.tenant import TenantMiddleware

app = FastAPI(title="API Gateway")

BOOKING_URL = os.environ.get("BOOKING_SERVICE_URL", "http://localhost:8100")


@app.middleware("http")
async def tenant_middleware(request: Request, call_next):
    # Allow public endpoints to be called without tenant header
    public_paths = {"/health", "/book"}
    if request.url.path in public_paths:
        # mark as no tenant (public)
        request.state.tenant_id = None
        request.state.is_super_admin = False
    else:
        await TenantMiddleware.attach_tenant(request)
    response = await call_next(request)
    return response


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/book")
async def book(request: Request):
    payload = await request.json()
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{BOOKING_URL}/book", json=payload)
        return r.json()
