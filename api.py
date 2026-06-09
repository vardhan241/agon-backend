from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import os

app = FastAPI()

# 1. FIX: CORS Middleware to allow your Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows your Vercel app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database helper (using environment variable from Render)
def get_db_connection():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

class Vehicle(BaseModel):
    car_number: str
    bay_number: str

@app.get("/")
def read_root():
    return {"status": "ANPR Running"}

@app.post("/park_vehicle")
def park_vehicle(vehicle: Vehicle):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Use ON CONFLICT to handle updates/moves smoothly
        cur.execute(
            """INSERT INTO vehicles (car_number, bay_number) 
               VALUES (%s, %s) 
               ON CONFLICT (car_number) DO UPDATE 
               SET bay_number = EXCLUDED.bay_number, updated_at = CURRENT_TIMESTAMP""",
            (vehicle.car_number, vehicle.bay_number)
        )
        conn.commit()
        cur.close()
        conn.close()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vehicles")
def list_vehicles():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT car_number, bay_number FROM vehicles")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {"vehicles": [{"car_number": r[0], "bay_number": r[1]} for r in rows]}