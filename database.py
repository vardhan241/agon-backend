import sqlite3
import threading

DB_PATH = 'plates.db'
_local = threading.local()

def get_conn():
    if not hasattr(_local, 'conn'):
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
    return _local.conn

def get_cursor():
    return get_conn().cursor()

# Initialize tables
_init_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
_init_cursor = _init_conn.cursor()
_init_cursor.execute('''
    CREATE TABLE IF NOT EXISTS vehicles (
        plate_number TEXT PRIMARY KEY,
        bay_number TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
_init_cursor.execute('''
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plate_number TEXT,
        bay_number TEXT,
        action TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
_init_conn.commit()
_init_conn.close()

# Legacy aliases so api.py works without changes
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()