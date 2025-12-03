from meeting_functions import book_meeting, check_availability
import database

database.init_db()

print("Checking availability for 2025-12-25 10:00...")
print(check_availability("2025-12-25 10:00"))

print("Booking meeting for John Doe at 2025-12-25 10:00...")
print(book_meeting("John Doe", "2025-12-25 10:00"))

print("Checking availability again...")
print(check_availability("2025-12-25 10:00"))

print("Booking meeting again (should fail)...")
print(book_meeting("Jane Doe", "2025-12-25 10:00"))
