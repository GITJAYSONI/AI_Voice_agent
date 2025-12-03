import sqlite3
import datetime

DB_NAME = "appointments.db"

def init_db():
    """Initialize the database with the bookings table."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            booking_time TEXT NOT NULL UNIQUE,
            status TEXT DEFAULT 'confirmed'
        )
    ''')
    conn.commit()
    conn.close()

def add_booking(customer_name, booking_time):
    """Add a new booking to the database."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO bookings (customer_name, booking_time) VALUES (?, ?)', 
                       (customer_name, booking_time))
        conn.commit()
        booking_id = cursor.lastrowid
        conn.close()
        return {"success": True, "booking_id": booking_id, "message": "Booking confirmed."}
    except sqlite3.IntegrityError:
        return {"success": False, "message": "Slot already booked."}
    except Exception as e:
        return {"success": False, "message": str(e)}

def get_booking(booking_id):
    """Retrieve booking details by ID."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM bookings WHERE id = ?', (booking_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "customer_name": row[1],
            "booking_time": row[2],
            "status": row[3]
        }
    return None

def check_availability(booking_time):
    """Check if a slot is available."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM bookings WHERE booking_time = ?', (booking_time,))
    row = cursor.fetchone()
    conn.close()
    return row is None

def get_all_bookings():
    """Get all bookings (for debugging/listing)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM bookings')   
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": r[0], "customer_name": r[1], "booking_time": r[2], "status": r[3]}
        for r in rows
    ]

# Initialize the DB when this module is imported (or run explicitly)
if __name__ == "__main__":
    init_db()
    print("Database initialized.")
