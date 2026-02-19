# Rider Document Management Service (MVP)

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Dict, List, Optional
import time
import os

app = FastAPI(title="Rider Document Management Service (MVP)")

# In-memory doc store: rider_id -> list of docs
RIDER_DOCS: Dict[str, List[dict]] = {}
UPLOAD_DIR = "/tmp/rider_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class DocMeta(BaseModel):
    rider_id: str
    doc_type: str  # license, insurance, id, etc.
    expires_at: Optional[int] = None
    filename: str
    uploaded_at: int

@app.post("/docs/upload")
async def upload_doc(rider_id: str = Form(...), doc_type: str = Form(...), expires_at: Optional[int] = Form(None), file: UploadFile = File(...)):
    fname = f"{rider_id}_{int(time.time())}_{file.filename}"
    fpath = os.path.join(UPLOAD_DIR, fname)
    with open(fpath, "wb") as f:
        f.write(await file.read())
    meta = {
        "rider_id": rider_id,
        "doc_type": doc_type,
        "expires_at": expires_at,
        "filename": fname,
        "uploaded_at": int(time.time()),
    }
    RIDER_DOCS.setdefault(rider_id, []).append(meta)
    return {"ok": True, "doc": meta}

@app.get("/docs/{rider_id}")
def get_docs(rider_id: str):
    return {"docs": RIDER_DOCS.get(rider_id, [])}

@app.get("/docs/expiring/{company_id}")
def get_expiring_docs(company_id: str, days: int = 14):
    now = int(time.time())
    soon = now + days*86400
    expiring = []
    for docs in RIDER_DOCS.values():
        for d in docs:
            if d.get("expires_at") and now < d["expires_at"] < soon:
                expiring.append(d)
    return {"expiring": expiring}
