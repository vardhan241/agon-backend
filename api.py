from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def db():
    c = sqlite3.connect("plates.db", check_same_thread=False)
    c.execute("CREATE TABLE IF NOT EXISTS vehicles (car_number TEXT PRIMARY KEY, bay_number TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
    c.commit()
    return c

class Vehicle(BaseModel):
    car_number: str
    bay_number: str

@app.get("/")
def root(): return {"status": "ANPR Running"}

@app.post("/scan_plate")
async def scan(file: UploadFile = File(...)): return {"success": True, "plate_number": "DEMO-1234"}

@app.post("/park_vehicle")
def park(v: Vehicle):
    c = db()
    c.execute("INSERT OR REPLACE INTO vehicles (car_number, bay_number) VALUES (?,?)", (v.car_number.upper(), v.bay_number.upper()))
    c.commit()
    return {"success": True}

@app.get("/vehicle/{plate}")
def find(plate: str):
    r = db().execute("SELECT car_number, bay_number FROM vehicles WHERE car_number=?", (plate.upper(),)).fetchone()
    return {"found": bool(r), "car_number": r[0] if r else None, "bay_number": r[1] if r else None}

@app.get("/vehicles")
def vehicles():
    rows = db().execute("SELECT car_number, bay_number, created_at FROM vehicles ORDER BY created_at DESC").fetchall()
    return {"success": True, "vehicles": [{"car_number": r[0], "bay_number": r[1], "created_at": r[2]} for r in rows]}

@app.delete("/vehicle/{plate}")
def delete(plate: str):
    c = db(); c.execute("DELETE FROM vehicles WHERE car_number=?", (plate.upper(),)); c.commit()
    return {"success": True}

@app.get("/stats")
def stats():
    total = db().execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
    return {"success": True, "total_vehicles": total, "today_entries": total, "free_bays": 32-total, "total_bays": 32}

@app.get("/history")
def history(): return {"success": True, "history": []}
