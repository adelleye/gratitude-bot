"""
Main application module for the Gratitude Journaling Bot.
Handles web server setup, webhook endpoints, and scheduling of daily/weekly tasks.
"""

from flask import Flask, request
import schedule
import time
import threading
from mvp_service import (
    init_db, get_daily_prompt, send_sms, insert_entry,
    get_weekly_entries, send_weekly_summary
)
import sqlite3
from datetime import datetime
import pytz

app = Flask(__name__)

def get_all_active_users():
    """
    Retrieve all active users from the database.
    
    Returns:
        list: List of (phone_number, email, timezone, preferred_time) tuples for active users
    """
    conn = sqlite3.connect("gratitude.db")
    c = conn.cursor()
    c.execute("""
        SELECT phone_number, email, timezone, preferred_time 
        FROM users 
        WHERE active = TRUE
    """)
    users = c.fetchall()
    conn.close()
    return users

def should_send_prompt(user_timezone, preferred_time, force=False):
    """
    Check if it's time to send a prompt for a user in their timezone.
    
    Args:
        user_timezone (str): User's timezone (e.g., 'America/New_York')
        preferred_time (str): User's preferred time (e.g., '19:00')
        force (bool): If True, bypass time check (for testing)
    
    Returns:
        bool: True if it's time to send the prompt
    """
    if force:
        return True
        
    try:
        # Get current time in user's timezone
        tz = pytz.timezone(user_timezone)
        current_time = datetime.now(tz)
        
        # Parse preferred time
        preferred_hour, preferred_minute = map(int, preferred_time.split(':'))
        
        # Check if it's the right time (within 2 minute window)
        return (current_time.hour == preferred_hour and 
                abs(current_time.minute - preferred_minute) <= 2)
    except Exception as e:
        print(f"Error checking time for timezone {user_timezone}: {e}")
        return False

def daily_job(force=False):
    """
    Check each user's timezone and preferred time,
    send prompts only to users where it's the right time.
    
    Args:
        force (bool): If True, send to all users regardless of time (for testing)
    """
    users = get_all_active_users()
    prompt = None  # Only generate prompt if needed
    
    for phone_number, email, timezone, preferred_time in users:
        if should_send_prompt(timezone, preferred_time, force):
            if prompt is None:  # Generate prompt only once
                prompt = get_daily_prompt()
            send_sms(phone_number, prompt)

def weekly_job():
    """
    Send weekly summaries to users where it's Sunday at their preferred time.
    """
    users = get_all_active_users()
    for phone_number, email, timezone, preferred_time in users:
        try:
            tz = pytz.timezone(timezone)
            current_time = datetime.now(tz)
            if (current_time.weekday() == 6 and  # Sunday
                should_send_prompt(timezone, preferred_time)):
                entries = get_weekly_entries(phone_number)
                send_weekly_summary(email, entries)
        except Exception as e:
            print(f"Error in weekly job for {phone_number}: {e}")

@app.route("/sms", methods=['POST'])
def sms_webhook():
    """
    Webhook endpoint for incoming SMS messages.
    Handles:
    1. User responses to gratitude prompts
    2. STOP messages for unsubscribing
    
    Returns:
        tuple: Empty response with appropriate status code
    """
    phone_number = request.form.get('From')
    message_body = request.form.get('Body')
    
    # Handle unsubscribe requests
    if message_body.lower().strip() == 'stop':
        conn = sqlite3.connect("gratitude.db")
        c = conn.cursor()
        c.execute("UPDATE users SET active = FALSE WHERE phone_number = ?", (phone_number,))
        conn.commit()
        conn.close()
        return '', 204
    
    # Store the gratitude entry
    insert_entry(phone_number, message_body)
    return '', 204

def run_scheduler():
    """
    Run the scheduler in a separate thread.
    Checks every minute if it's time to send prompts to any users.
    """
    # Check every minute for users who should receive prompts
    schedule.every(1).minutes.do(daily_job)
    schedule.every(1).minutes.do(weekly_job)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    # Initialize the database
    init_db()
    
    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()
    
    # Start the Flask app
    app.run(host='0.0.0.0', port=8080)
