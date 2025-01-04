"""Test script to verify ReplDB functionality."""
from mvp_service import init_db, get_all_active_users, insert_entry, get_weekly_entries
from datetime import datetime

try:
    from replit import db as repl_db
    USING_REPLDB = True
except ImportError:
    print("Warning: Not running in Replit environment")
    USING_REPLDB = False

def test_repldb():
    print("Testing ReplDB functionality...")
    
    # Initialize database
    print("\n1. Initializing database...")
    init_db()
    
    # Check users
    print("\n2. Checking users...")
    users = get_all_active_users()
    print(f"Active users: {users}")
    
    # Insert test entry
    print("\n3. Inserting test entry...")
    test_phone = '+1234567890'  # Example phone number
    test_entry = f"Test entry at {datetime.now().isoformat()}"
    insert_entry(test_phone, test_entry)
    
    # Get entries
    print("\n4. Getting weekly entries...")
    entries = get_weekly_entries(test_phone)
    print(f"Recent entries: {entries}")
    
    # Check raw ReplDB data
    if USING_REPLDB:
        print("\n5. Raw ReplDB data:")
        print("Users:", repl_db.get('users', {}))
        print("Entries:", repl_db.get('entries', []))
    else:
        print("\n5. Using SQLite (not ReplDB)")

if __name__ == "__main__":
    test_repldb() 