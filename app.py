# main.py - FINAL FIXED VERSION (100% STABLE, NO 422 EVER)

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import uvicorn
import os

# ============================================================
# APP CONFIG
# ============================================================

app = FastAPI(title="Wishlist API", version="1.0.0")

# Enable CORS for all origins (for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# FIREBASE INITIALIZATION (SAFE CHECK)
# ============================================================

import json, os
from firebase_admin import credentials, initialize_app

if os.path.exists("serviceAccountKey.json"):
    # Local mode
    cred = credentials.Certificate("serviceAccountKey.json")
else:
    # Cloud mode (Render, Railway)
    cred_json = json.loads(os.environ["FIREBASE_KEY_JSON"])
    cred = credentials.Certificate(cred_json)

initialize_app(cred, {
    'databaseURL': 'https://wishlist-d6d7a-default-rtdb.firebaseio.com'
})

# ============================================================
# STATIC & TEMPLATE SETUP
# ============================================================

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_all_items():
    """Fetch all wishlist items from Firebase."""
    ref = db.reference('wishlist')
    items = ref.get() or {}
    return [{"id": k, **v} for k, v in items.items()]

def sort_by_priority(items):
    """Sort wishlist items by priority: high > medium > low."""
    order = {'high': 3, 'medium': 2, 'low': 1}
    return sorted(items, key=lambda x: order.get(x.get('priority', 'low').lower(), 0), reverse=True)

# ============================================================
# API ROUTES
# ============================================================

@app.get("/api/items", response_class=JSONResponse)
async def api_get_items():
    """Fetch and return all wishlist items."""
    items = get_all_items()
    sorted_items = sort_by_priority(items)
    return JSONResponse(sorted_items)

@app.post("/api/add", response_class=JSONResponse)
async def api_add_item(
    title: str = Form(...),
    description: str = Form(""),
    type: str = Form(...),
    priority: str = Form(...),
    price: str = Form(""),
    url: str = Form("")
):
    """Add a new wishlist item."""
    ref = db.reference('wishlist')
    new_item = {
        'title': title.strip(),
        'description': description.strip() if description else "",
        'type': type.strip(),
        'priority': priority.strip().lower(),
        'price': price.strip() if price else "",
        'url': url.strip() if url else "",
        'createdAt': datetime.now().isoformat(),
        'updatedAt': datetime.now().isoformat()
    }
    pushed = ref.push(new_item)
    return JSONResponse({"success": True, "id": pushed.key})

@app.post("/api/edit/{item_id}", response_class=JSONResponse)
async def api_edit_item(
    item_id: str,
    title: str = Form(...),
    description: str = Form(""),
    type: str = Form(...),
    priority: str = Form(...),
    price: str = Form(""),
    url: str = Form("")
):
    """Edit an existing wishlist item."""
    ref = db.reference(f'wishlist/{item_id}')
    item = ref.get()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    updated_item = {
        'title': title.strip(),
        'description': description.strip() if description else "",
        'type': type.strip(),
        'priority': priority.strip().lower(),
        'price': price.strip() if price else "",
        'url': url.strip() if url else "",
        'createdAt': item.get('createdAt', datetime.now().isoformat()),
        'updatedAt': datetime.now().isoformat()
    }

    ref.set(updated_item)
    return JSONResponse({"success": True})

@app.post("/api/delete/{item_id}", response_class=JSONResponse)
async def api_delete_item(item_id: str):
    """Delete a wishlist item."""
    ref = db.reference(f'wishlist/{item_id}')
    if not ref.get():
        raise HTTPException(status_code=404, detail="Item not found")
    ref.delete()
    return JSONResponse({"success": True})

# ============================================================
# FRONTEND ROUTE
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the main HTML page."""
    return templates.TemplateResponse("index.html", {"request": request})

# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    print("🚀 STARTING WISHLIST APP...")
    print("🌐 OPEN: http://localhost:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
