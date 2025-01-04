"""
Admin tools for managing users in the Gratitude Journaling Bot.
Provides functions to add, remove, list, and modify users.
run python admin_tools.py
Gratitude Bot Admin Tools
1. List all users
2. Add new user
3. Update user
4. Delete user
5. Exit
"""

from mvp_service import is_replit_env
import sqlite3
from datetime import datetime
import pytz
import json

try:
    from replit import db as repl_db
    USING_REPLDB = True
except ImportError:
    print("Warning: Not running in Replit environment")
    USING_REPLDB = False

def validate_phone(phone):
    """Validate phone number format."""
    if not phone.startswith('+'):
        raise ValueError("Phone number must start with '+' and country code (e.g., '+1234567890')")
    if not phone[1:].isdigit():
        raise ValueError("Phone number must contain only digits after the '+' sign")
    return True

def validate_timezone(timezone):
    """Validate timezone exists."""
    if timezone not in pytz.all_timezones:
        raise ValueError(f"Invalid timezone. Must be one of: {', '.join(pytz.common_timezones)}")
    return True

def validate_time(preferred_time):
    """Validate time format (HH:MM)."""
    try:
        datetime.strptime(preferred_time, "%H:%M")
        return True
    except ValueError:
        raise ValueError("Time must be in 24-hour format (HH:MM), e.g., '20:00'")

def add_user(phone, email, timezone='America/New_York', preferred_time='20:00'):
    """
    Add a new user to the database.
    
    Args:
        phone (str): Phone number with country code (e.g., '+1234567890')
        email (str): Email address for weekly summaries
        timezone (str): Valid timezone (e.g., 'America/New_York')
        preferred_time (str): Time in 24-hour format (e.g., '20:00')
    """
    # Validate inputs
    validate_phone(phone)
    validate_timezone(timezone)
    validate_time(preferred_time)
    
    if USING_REPLDB:
        users = repl_db.get('users', {})
        if phone in users:
            raise ValueError(f"User with phone {phone} already exists!")
            
        users[phone] = {
            'email': email,
            'timezone': timezone,
            'preferred_time': preferred_time,
            'active': True
        }
        repl_db['users'] = users
        print(f"Added user: {phone} ({email})")
    else:
        conn = sqlite3.connect("gratitude.db")
        c = conn.cursor()
        try:
            c.execute("""
            INSERT INTO users (phone_number, email, timezone, preferred_time, active)
            VALUES (?, ?, ?, ?, ?)
            """, (phone, email, timezone, preferred_time, True))
            conn.commit()
            print(f"Added user: {phone} ({email})")
        except sqlite3.IntegrityError:
            raise ValueError(f"User with phone {phone} already exists!")
        finally:
            conn.close()

def list_users():
    """List all users and their settings."""
    if USING_REPLDB:
        users = repl_db.get('users', {})
        if not users:
            print("No users found.")
            return
        
        print("\nCurrent Users:")
        print("-" * 80)
        for phone, data in users.items():
            status = "Active" if data['active'] else "Inactive"
            print(f"Phone: {phone}")
            print(f"Email: {data['email']}")
            print(f"Timezone: {data['timezone']}")
            print(f"Preferred Time: {data['preferred_time']}")
            print(f"Status: {status}")
            print("-" * 80)
    else:
        conn = sqlite3.connect("gratitude.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users")
        users = c.fetchall()
        conn.close()
        
        if not users:
            print("No users found.")
            return
            
        print("\nCurrent Users:")
        print("-" * 80)
        for user in users:
            status = "Active" if user[4] else "Inactive"
            print(f"Phone: {user[0]}")
            print(f"Email: {user[1]}")
            print(f"Timezone: {user[2]}")
            print(f"Preferred Time: {user[3]}")
            print(f"Status: {status}")
            print("-" * 80)

def update_user(phone, **kwargs):
    """
    Update user settings.
    
    Args:
        phone (str): User's phone number
        **kwargs: Fields to update (email, timezone, preferred_time, active)
    """
    # Validate any provided fields
    if 'timezone' in kwargs:
        validate_timezone(kwargs['timezone'])
    if 'preferred_time' in kwargs:
        validate_time(kwargs['preferred_time'])
        
    if USING_REPLDB:
        users = repl_db.get('users', {})
        if phone not in users:
            raise ValueError(f"User with phone {phone} not found!")
            
        user_data = users[phone]
        user_data.update(kwargs)
        users[phone] = user_data
        repl_db['users'] = users
        print(f"Updated user: {phone}")
    else:
        conn = sqlite3.connect("gratitude.db")
        c = conn.cursor()
        
        # Build update query dynamically
        fields = []
        values = []
        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)
        values.append(phone)
        
        query = f"UPDATE users SET {', '.join(fields)} WHERE phone_number = ?"
        c.execute(query, values)
        
        if c.rowcount == 0:
            conn.close()
            raise ValueError(f"User with phone {phone} not found!")
            
        conn.commit()
        conn.close()
        print(f"Updated user: {phone}")

def delete_user(phone):
    """Delete a user from the database."""
    if USING_REPLDB:
        users = repl_db.get('users', {})
        if phone not in users:
            raise ValueError(f"User with phone {phone} not found!")
            
        del users[phone]
        repl_db['users'] = users
        print(f"Deleted user: {phone}")
    else:
        conn = sqlite3.connect("gratitude.db")
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE phone_number = ?", (phone,))
        
        if c.rowcount == 0:
            conn.close()
            raise ValueError(f"User with phone {phone} not found!")
            
        conn.commit()
        conn.close()
        print(f"Deleted user: {phone}")

if __name__ == "__main__":
    while True:
        print("\nGratitude Bot Admin Tools")
        print("1. List all users")
        print("2. Add new user")
        print("3. Update user")
        print("4. Delete user")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        try:
            if choice == "1":
                list_users()
            
            elif choice == "2":
                phone = input("Enter phone number (with country code, e.g., +1234567890): ")
                email = input("Enter email: ")
                timezone = input("Enter timezone (press Enter for America/New_York): ") or "America/New_York"
                preferred_time = input("Enter preferred time (24-hour format, press Enter for 20:00): ") or "20:00"
                add_user(phone, email, timezone, preferred_time)
            
            elif choice == "3":
                phone = input("Enter phone number to update: ")
                print("\nLeave blank to keep current value")
                email = input("New email (or Enter to skip): ")
                timezone = input("New timezone (or Enter to skip): ")
                preferred_time = input("New preferred time (or Enter to skip): ")
                active = input("Active status (true/false, or Enter to skip): ")
                
                updates = {}
                if email: updates['email'] = email
                if timezone: updates['timezone'] = timezone
                if preferred_time: updates['preferred_time'] = preferred_time
                if active: updates['active'] = active.lower() == 'true'
                
                if updates:
                    update_user(phone, **updates)
                else:
                    print("No updates provided")
            
            elif choice == "4":
                phone = input("Enter phone number to delete: ")
                confirm = input(f"Are you sure you want to delete user {phone}? (yes/no): ")
                if confirm.lower() == 'yes':
                    delete_user(phone)
                else:
                    print("Deletion cancelled")
            
            elif choice == "5":
                print("Goodbye!")
                break
            
            else:
                print("Invalid choice. Please enter a number between 1 and 5.")
                
        except Exception as e:
            print(f"Error: {e}")
            
        input("\nPress Enter to continue...") 