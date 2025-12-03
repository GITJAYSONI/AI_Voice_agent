import database
from datetime import datetime

# Ensure DB is initialized
database.init_db()

def book_meeting(customer_name, booking_time):
    """
    Book a meeting slot.
    booking_time should be in format 'YYYY-MM-DD HH:MM'
    """
    # Validate time format
    try:
        datetime.strptime(booking_time, "%Y-%m-%d %H:%M")
    except ValueError:
        return {"error": "Invalid time format. Please use YYYY-MM-DD HH:MM"}

    if not database.check_availability(booking_time):
        return {"error": f"Slot {booking_time} is already booked."}
    
    result = database.add_booking(customer_name, booking_time)
    return result

def check_availability(booking_time):
    """
    Check if a slot is available.
    booking_time should be in format 'YYYY-MM-DD HH:MM'
    """
    try:
        datetime.strptime(booking_time, "%Y-%m-%d %H:%M")
    except ValueError:
        return {"error": "Invalid time format. Please use YYYY-MM-DD HH:MM"}

    is_available = database.check_availability(booking_time)
    if is_available:
        return {"available": True, "message": f"Slot {booking_time} is available."}
    else:
        return {"available": False, "message": f"Slot {booking_time} is not available."}

FUNCTION_MAP = {
    'book_meeting': book_meeting,
    'check_availability': check_availability
}
