"""
Real-Time Tracking Service with WebSocket Support

Provides live location tracking for deliveries with WebSocket connections
for real-time updates, ETA calculation, and order status transitions.
"""

import os
import sys
import time
import uuid
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Set
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict

from fastapi import FastAPI, HTTPException, status, Depends, WebSocket, WebSocketDisconnect, Header, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import jwt
import httpx

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.auth import get_current_user, TokenPayload
from shared.security import setup_security_middleware
from starlette.middleware.cors import CORSMiddleware

app = FastAPI(title="Real-Time Tracking Service")

# NOTE: We deliberately skip BaseHTTPMiddleware (SecurityHeadersMiddleware) here
# because BaseHTTPMiddleware in Starlette 0.40+ breaks WebSocket routing.
# CORS is still applied (needed for browser clients).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
JWT_SECRET = os.environ.get("JWT_SECRET", "replace-me")
JWT_ALGO = "HS256"
ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_URL", "http://localhost:8400")
NOTIFICATION_SERVICE_URL = os.environ.get("NOTIFICATION_SERVICE_URL", "http://localhost:8600")
TRACKING_TTL_SECONDS = int(os.environ.get("TRACKING_TTL_SECONDS", 60 * 60 * 24))  # 24 hours

# ==================== Data Models ====================

class OrderStatus(str, Enum):
    """Order statuses."""
    ASSIGNED = "ASSIGNED"
    PICKED_UP = "PICKED_UP"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"

class StartTrackingRequest(BaseModel):
    """Start tracking for an order."""
    order_id: str
    rider_id: str
    dropoff_lat: float = Field(..., ge=-90, le=90)
    dropoff_lng: float = Field(..., ge=-180, le=180)
    phone: Optional[str] = None

class LocationUpdate(BaseModel):
    """Location and status update."""
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    status: Optional[OrderStatus] = None
    timestamp: Optional[int] = None

class TrackingSession(BaseModel):
    """Active tracking session."""
    tracking_id: str
    order_id: str
    rider_id: str
    current_location: Optional[Dict] = None
    dropoff: Dict
    status: OrderStatus
    eta_seconds: Optional[int] = None
    started_at: int
    updated_at: int
    expires_at: int

class TrackingResponse(BaseModel):
    """Response for tracking queries."""
    tracking_id: str
    order_id: str
    rider_id: str
    status: str
    current_location: Optional[Dict]
    dropoff: Dict
    eta_seconds: Optional[int]
    updated_at: int

class ConnectionManager:
    """Manage WebSocket connections for real-time tracking."""
    
    def __init__(self):
        # tracking_id -> set of connected websocket clients
        self.active_connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        self.user_subscriptions: Dict[str, Set[str]] = defaultdict(set)  # user_id -> tracking_ids
    
    async def connect(self, tracking_id: str, websocket: WebSocket, user_id: str):
        """Register a WebSocket connection."""
        await websocket.accept()
        self.active_connections[tracking_id].add(websocket)
        self.user_subscriptions[user_id].add(tracking_id)
        logger.info(f"Client {user_id} connected to tracking {tracking_id}")
    
    def disconnect(self, tracking_id: str, websocket: WebSocket, user_id: str):
        """Unregister a WebSocket connection."""
        self.active_connections[tracking_id].discard(websocket)
        self.user_subscriptions[user_id].discard(tracking_id)
        if not self.active_connections[tracking_id]:
            del self.active_connections[tracking_id]
        logger.info(f"Client {user_id} disconnected from tracking {tracking_id}")
    
    async def broadcast(self, tracking_id: str, data: dict):
        """Broadcast update to all connected clients."""
        if tracking_id not in self.active_connections:
            return
        
        disconnected = set()
        for connection in self.active_connections[tracking_id]:
            try:
                await connection.send_json(data)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")
                disconnected.add(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.active_connections[tracking_id].discard(connection)
    
    async def broadcast_to_user(self, user_id: str, data: dict):
        """Broadcast to all trackings subscribed by a user."""
        for tracking_id in self.user_subscriptions.get(user_id, set()):
            await self.broadcast(tracking_id, data)

# ==================== Connection Manager ====================

connection_manager = ConnectionManager()

# ==================== In-Memory Storage ====================

tracking_sessions: Dict[str, dict] = {}

# ==================== Helper Functions ====================

def _now_ts() -> int:
    """Get current timestamp in seconds."""
    return int(time.time())

def _haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance in kilometers using Haversine formula."""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371  # Earth radius in km
    
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c

def _calculate_eta(current_lat: float, current_lng: float, dropoff_lat: float, dropoff_lng: float) -> int:
    """Calculate ETA in seconds assuming 30 km/h average speed."""
    distance_km = _haversine_distance(current_lat, current_lng, dropoff_lat, dropoff_lng)
    # 30 km/h = 0.5 km/min = 0.00833 km/sec
    speed_km_per_sec = 30 / 3600
    eta_seconds = int(distance_km / speed_km_per_sec) if speed_km_per_sec > 0 else 0
    return max(60, eta_seconds)  # Minimum 60 seconds

def _get_session_data(session: dict) -> dict:
    """Format session data for response."""
    current_loc = session.get("current_location") or {}
    lat = current_loc.get("lat")
    lng = current_loc.get("lng")
    dropoff = session.get("dropoff", {})
    
    eta = None
    if lat is not None and lng is not None:
        eta = _calculate_eta(lat, lng, dropoff.get("lat", 0), dropoff.get("lng", 0))
    
    return {
        "tracking_id": session["tracking_id"],
        "order_id": session["order_id"],
        "rider_id": session["rider_id"],
        "status": session["status"].value,
        "current_location": session.get("current_location"),
        "dropoff": dropoff,
        "eta_seconds": eta,
        "updated_at": session["updated_at"]
    }

# ==================== Health Check ====================

@app.get("/health")
async def health():
    return {"status": "ok", "service": "tracking"}

# ==================== Start Tracking ====================

@app.post("/tracking/start", response_model=TrackingResponse)
async def start_tracking(
    request: StartTrackingRequest,
    current_user: TokenPayload = Depends(get_current_user)
):
    """Start tracking for a delivery order."""
    
    tracking_id = str(uuid.uuid4())
    expires_at = _now_ts() + TRACKING_TTL_SECONDS
    
    session = {
        "tracking_id": tracking_id,
        "order_id": request.order_id,
        "rider_id": request.rider_id,
        "rider_user_id": current_user.user_id,  # users.id — for update auth check
        "current_location": None,
        "dropoff": {
            "lat": request.dropoff_lat,
            "lng": request.dropoff_lng
        },
        "status": OrderStatus.ASSIGNED,
        "started_at": _now_ts(),
        "updated_at": _now_ts(),
        "expires_at": expires_at
    }
    
    tracking_sessions[tracking_id] = session
    
    logger.info(f"Tracking started: {tracking_id} (order={request.order_id}, rider={request.rider_id})")
    
    # Notify via SMS if phone provided
    if request.phone and NOTIFICATION_SERVICE_URL:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"{NOTIFICATION_SERVICE_URL}/notify/sms",
                    json={
                        "phone": request.phone,
                        "message": f"Your delivery is on the way. Track here: {tracking_id}"
                    },
                    timeout=5.0
                )
        except Exception as e:
            logger.error(f"Failed to send tracking notification: {e}")
    
    return _get_session_data(session)

# ==================== Update Location & Status ====================

@app.post("/tracking/update/{tracking_id}", response_model=TrackingResponse)
async def update_tracking(
    tracking_id: str,
    update: LocationUpdate,
    current_user: TokenPayload = Depends(get_current_user)
):
    """Update location and optionally status for a tracking session."""
    
    session = tracking_sessions.get(tracking_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tracking session not found"
        )
    
    if _now_ts() > session["expires_at"]:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Tracking session expired"
        )
    
    # Verify authorization (rider or superadmin)
    # session["rider_user_id"] is users.id; session["rider_id"] is riders profile id
    authorized = (
        current_user.user_id == session.get("rider_user_id")
        or current_user.user_id == session.get("rider_id")  # fallback
        or current_user.role in ("superadmin", "SUPERADMIN")
    )
    if not authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this tracking"
        )
    
    # Update location
    session["current_location"] = {
        "lat": update.lat,
        "lng": update.lng,
        "timestamp": update.timestamp or _now_ts()
    }
    
    # Update status if provided
    if update.status:
        old_status = session["status"]
        session["status"] = update.status
        
        logger.info(f"Order {session['order_id']} status: {old_status.value} → {update.status.value}")
        
        # Notify order service of status change
        if update.status == OrderStatus.DELIVERED:
            session["expires_at"] = _now_ts() + 3600  # Expire in 1 hour after delivery
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.put(
                        f"{ORDER_SERVICE_URL}/orders/{session['order_id']}/status",
                        json={"status": "DELIVERED"},
                        timeout=5.0
                    )
            except Exception as e:
                logger.error(f"Failed to update order service: {e}")
    
    session["updated_at"] = _now_ts()
    
    # Broadcast to all connected clients
    response_data = _get_session_data(session)
    await connection_manager.broadcast(tracking_id, {
        "type": "location_update",
        "data": response_data
    })
    
    return response_data

# ==================== Get Tracking Status ====================

@app.get("/tracking/{tracking_id}", response_model=TrackingResponse)
async def get_tracking(tracking_id: str):
    """Get current tracking status (public endpoint)."""
    
    session = tracking_sessions.get(tracking_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tracking session not found"
        )
    
    if _now_ts() > session["expires_at"]:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Tracking session expired"
        )
    
    return _get_session_data(session)

# ==================== Get Rider Current Tracking ====================

@app.get("/tracking/rider/{rider_id}", response_model=TrackingResponse)
async def get_rider_tracking(
    rider_id: str,
    current_user: TokenPayload = Depends(get_current_user)
):
    """Get current active tracking for a rider."""
    
    # Find latest active session for this rider
    active_sessions = [
        s for s in tracking_sessions.values()
        if s["rider_id"] == rider_id and _now_ts() <= s["expires_at"]
    ]
    
    if not active_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active tracking session for this rider"
        )
    
    latest = max(active_sessions, key=lambda s: s["updated_at"])
    return _get_session_data(latest)

# ==================== WebSocket Endpoint ====================

@app.websocket("/ws/tracking/{tracking_id}")
async def websocket_endpoint(
    tracking_id: str,
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time tracking updates.
    
    Query Parameters:
    - token: JWT token for authentication
    
    Message Types:
    - location_update: {lat, lng, status}
    - subscribe: {} (for public tracking, no auth needed)
    """
    
    # Verify tracking session exists
    if tracking_id not in tracking_sessions:
        await websocket.close(code=1008, reason="Tracking session not found")
        return
    
    # Verify token if provided
    user_id = "public"
    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
            user_id = payload.get("sub", "public")
        except jwt.ExpiredSignatureError:
            await websocket.close(code=1008, reason="Token expired")
            return
        except Exception:
            await websocket.close(code=1008, reason="Invalid token")
            return
    
    # Accept connection
    await connection_manager.connect(tracking_id, websocket, user_id)
    
    # Send initial state
    session = tracking_sessions.get(tracking_id)
    if session:
        await websocket.send_json({
            "type": "initial_state",
            "data": _get_session_data(session)
        })
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Verify tracking still exists and hasn't expired
            if tracking_id not in tracking_sessions:
                await websocket.send_json({"type": "error", "message": "Tracking expired"})
                break
            
            session = tracking_sessions.get(tracking_id)
            if not session or _now_ts() > session["expires_at"]:
                await websocket.send_json({"type": "error", "message": "Tracking session expired"})
                break
            
            # Handle location update
            if data.get("type") == "location_update":
                try:
                    location = data.get("location", {})
                    update = LocationUpdate(
                        lat=location.get("lat"),
                        lng=location.get("lng"),
                        status=location.get("status")
                    )
                    
                    # Update session
                    session["current_location"] = {
                        "lat": update.lat,
                        "lng": update.lng,
                        "timestamp": update.timestamp or _now_ts()
                    }
                    
                    if update.status:
                        session["status"] = update.status
                    
                    session["updated_at"] = _now_ts()
                    
                    # Broadcast to all subscribers
                    await connection_manager.broadcast(tracking_id, {
                        "type": "location_update",
                        "data": _get_session_data(session)
                    })
                
                except Exception as e:
                    logger.error(f"Error processing location update: {e}")
                    await websocket.send_json({"type": "error", "message": str(e)})
            
            # Handle ping (keep-alive)
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        connection_manager.disconnect(tracking_id, websocket, user_id)
        logger.info(f"Client {user_id} disconnected from tracking {tracking_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(tracking_id, websocket, user_id)

# ==================== Statistics ====================

@app.get("/stats/tracking")
async def get_tracking_stats(
    current_user: TokenPayload = Depends(get_current_user)
):
    """Get tracking statistics (admin only)."""
    
    if current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only"
        )
    
    now = _now_ts()
    active_sessions = [s for s in tracking_sessions.values() if now <= s["expires_at"]]
    
    # Active connections
    total_connections = sum(len(conns) for conns in connection_manager.active_connections.values())
    
    # Status distribution
    status_counts = defaultdict(int)
    for session in active_sessions:
        status_counts[session["status"].value] += 1
    
    # Sessions by age
    sessions_by_age = {
        "last_5_min": 0,
        "last_hour": 0,
        "older": 0
    }
    
    five_min_ago = now - 300
    hour_ago = now - 3600
    
    for session in active_sessions:
        updated = session["updated_at"]
        if updated >= five_min_ago:
            sessions_by_age["last_5_min"] += 1
        elif updated >= hour_ago:
            sessions_by_age["last_hour"] += 1
        else:
            sessions_by_age["older"] += 1
    
    return {
        "total_active_sessions": len(active_sessions),
        "total_websocket_connections": total_connections,
        "status_distribution": dict(status_counts),
        "sessions_by_recency": sessions_by_age
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8500)
