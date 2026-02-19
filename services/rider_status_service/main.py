"""
Rider Status Service — DB-backed rider online/offline/break status management.
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import logging

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database import get_db, engine, Base
from shared.models import Rider, RiderStatus as RiderStatusEnum, RiderCompany

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Rider Status Service")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StatusUpdate(BaseModel):
    rider_id: str
    status: str  # online|offline|break
    set_by: str = "self"  # admin or self

@app.get("/health")
def health():
    return {"status": "ok", "service": "rider_status"}

@app.post("/status/update")
def update_status(req: StatusUpdate, db: Session = Depends(get_db)):
    """Update rider status in the database."""
    if req.status not in ("online", "offline", "break"):
        raise HTTPException(status_code=400, detail="Invalid status. Must be: online, offline, break")

    rider = db.query(Rider).filter(Rider.id == req.rider_id).first()
    if not rider:
        raise HTTPException(status_code=404, detail=f"Rider {req.rider_id} not found")

    status_map = {
        "online": RiderStatusEnum.ONLINE,
        "offline": RiderStatusEnum.OFFLINE,
        "break": RiderStatusEnum.BREAK,
    }
    rider.status = status_map[req.status]
    db.commit()

    logger.info(f"Rider {req.rider_id} status → {req.status} (set_by: {req.set_by})")
    return {"ok": True, "rider_id": req.rider_id, "status": req.status}

@app.get("/status/{rider_id}")
def get_status(rider_id: str, db: Session = Depends(get_db)):
    """Get a single rider's status."""
    rider = db.query(Rider).filter(Rider.id == rider_id).first()
    if not rider:
        return {"rider_id": rider_id, "status": "offline"}
    return {
        "rider_id": rider.id,
        "status": rider.status.value if hasattr(rider.status, 'value') else str(rider.status),
    }

@app.get("/status/company/{company_id}")
def get_company_status(company_id: str, db: Session = Depends(get_db)):
    """Get all rider statuses for a company."""
    riders = db.query(Rider).filter(Rider.company_id == company_id).all()
    return {
        "statuses": [
            {
                "rider_id": r.id,
                "status": r.status.value if hasattr(r.status, 'value') else str(r.status),
                "current_lat": r.current_lat,
                "current_lng": r.current_lng,
            }
            for r in riders
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8800)
