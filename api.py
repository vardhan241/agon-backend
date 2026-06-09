from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2, os, base64, httpx

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def db():
    return psycopg2.connect(os.environ["DATABASE_URL"])

def init():
    c = db()
    c.cursor().execute("""CREATE TABLE IF NOT EXISTS vehicles (
        car_number TEXT PRIMARY KEY, bay_number TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW())""")
    c.commit()

@app.on_event("startup")
def startup(): init()

@app.get("/")
def root(): return {"status": "ANPR Running"}

@app.post("/scan_plate")
async def scan(file: UploadFile = File(...)):
    try:
        data = await file.read()
        b64 = base64.b64encode(data).decode()
        mime = file.content_type or "image/jpeg"
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": "claude-haiku-4-5-20251001", "max_tokens": 50,
                      "messages": [{"role": "user", "content": [
                          {"type": "image", "source": {"type": "base64", "media_type": mime, "data": b64}},
                          {"type": "text", "text": "Read the vehicle number plate. Reply with ONLY the plate number, no spaces or punctuation. Example: MH12AB1234"}
                      ]}]}
            )
        plate = r.json()["content"][0]["text"].strip().upper().replace(" ", "").replace("-", "")
        return {"success": True, "plate_number": plate}
    except Exception as e:
        return {"success": False, "plate_number": None, "error": str(e)}

class Vehicle(BaseModel):
    car_number: str = ""
    plate_number: str = ""
    bay_number: str

@app.post("/park_vehicle")
def park(v: Vehicle):
    plate = (v.car_number or v.plate_number).upper()
    if not plate: raise HTTPException(400, "No plate")
    c = db(); cur = c.cursor()
    cur.execute("INSERT INTO vehicles (car_number, bay_number) VALUES (%s,%s) ON CONFLICT (car_number) DO UPDATE SET bay_number=%s, updated_at=NOW()", (plate, v.bay_number.upper(), v.bay_number.upper()))
    c.commit()
    return {"success": True}

@app.get("/vehicle/{plate}")
def find(plate: str):
    cur = db().cursor()
    cur.execute("SELECT car_number, bay_number FROM vehicles WHERE car_number=%s", (plate.upper(),))
    r = cur.fetchone()
    return {"found": bool(r), "car_number": r[0] if r else None, "bay_number": r[1] if r else None}

@app.get("/vehicles")
def vehicles():
    cur = db().cursor()
    cur.execute("SELECT car_number, bay_number, created_at FROM vehicles ORDER BY created_at DESC")
    return {"success": True, "vehicles": [{"car_number": r[0], "bay_number": r[1], "created_at": str(r[2])} for r in cur.fetchall()]}

@app.delete("/vehicle/{plate}")
def delete(plate: str):
    c = db(); c.cursor().execute("DELETE FROM vehicles WHERE car_number=%s", (plate.upper(),)); c.commit()
    return {"success": True}

@app.get("/stats")
def stats():
    cur = db().cursor(); cur.execute("SELECT COUNT(*) FROM vehicles")
    t = cur.fetchone()[0]
    return {"success": True, "total_vehicles": t, "today_entries": t, "free_bays": 32-t, "total_bays": 32}

@app.get("/history")
def history(): return {"success": True, "history": []}
