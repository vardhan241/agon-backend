from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3

DB_PATH = 'plates.db'

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Init tables
_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
_conn.execute('''CREATE TABLE IF NOT EXISTS vehicles (
    plate_number TEXT PRIMARY KEY,
    bay_number TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
_conn.execute('''CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plate_number TEXT,
    bay_number TEXT,
    action TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
_conn.commit()
_conn.close()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=['*'],
    allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

class Vehicle(BaseModel):
    plate_number: str
    bay_number: str

@app.get('/')
def home():
    return {'status': 'ANPR Running'}

@app.post('/scan_plate')
async def scan_plate(file: UploadFile = File(...)):
    return {'success': True, 'plate_number': 'DEMO-1234'}

@app.post('/park_vehicle')
def park_vehicle(vehicle: Vehicle):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('INSERT OR REPLACE INTO vehicles (plate_number, bay_number) VALUES (?, ?)',
        (vehicle.plate_number, vehicle.bay_number))
    cur.execute('INSERT INTO history (plate_number, bay_number, action) VALUES (?, ?, ?)',
        (vehicle.plate_number, vehicle.bay_number, 'PARKED'))
    conn.commit()
    conn.close()
    return {'success': True}

@app.get('/vehicle/{plate}')
def find_vehicle(plate: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT plate_number, bay_number FROM vehicles WHERE plate_number = ?', (plate,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return {'found': False}
    return {'found': True, 'car_number': row[0], 'bay_number': row[1]}

@app.get('/vehicles')
def all_vehicles():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT plate_number, bay_number, created_at FROM vehicles ORDER BY created_at DESC')
    rows = cur.fetchall()
    conn.close()
    return {'success': True, 'vehicles': [{'car_number': r[0], 'bay_number': r[1], 'created_at': r[2]} for r in rows]}

@app.delete('/vehicle/{plate}')
def delete_vehicle(plate: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM vehicles WHERE plate_number = ?', (plate,))
    conn.commit()
    conn.close()
    return {'deleted': True}

@app.get('/stats')
def stats():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM vehicles')
    total = cur.fetchone()[0]
    conn.close()
    return {'success': True, 'total_vehicles': total, 'today_entries': total,
            'free_bays': 32 - total, 'total_bays': 32}

@app.get('/history')
def history():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT plate_number, bay_number, action, timestamp FROM history ORDER BY timestamp DESC')
    rows = cur.fetchall()
    conn.close()
    return {'success': True, 'history': [{'car_number': r[0], 'bay_number': r[1],
            'action': r[2], 'timestamp': r[3]} for r in rows]}

@app.delete('/clear')
def clear_yard():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM vehicles')
    conn.commit()
    conn.close()
    return {'success': True}

@app.post('/exit_vehicle')
def exit_vehicle(vehicle: Vehicle):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM vehicles WHERE plate_number = ?', (vehicle.plate_number,))
    cur.execute('INSERT INTO history (plate_number, bay_number, action) VALUES (?, ?, ?)',
        (vehicle.plate_number, vehicle.bay_number, 'EXITED'))
    conn.commit()
    conn.close()
    return {'success': True}
