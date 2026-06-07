from database import conn, cursor

cursor.execute(
    """
    INSERT OR REPLACE INTO vehicles
    (plate_number,bay_number)
    VALUES(?,?)
    """,
    (
        "KL01CA2555",
        "A01"
    )
)

conn.commit()

cursor.execute(
    "SELECT * FROM vehicles"
)

rows = cursor.fetchall()

print(rows)