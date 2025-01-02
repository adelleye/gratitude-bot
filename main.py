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

app = Flask(__name__)

def get_all_active_users():
    """
    Retrieve all active users from the database.
    
    Returns:
        list: List of (phone_number, email) tuples for active users
    """
    conn = sqlite3.connect("gratitude.db")
    c = conn.cursor()
    c.execute("SELECT phone_number, email FROM users WHERE active = TRUE")
    users = c.fetchall()
    conn.close()
    return users

def daily_job():
    """
    Daily scheduled task that:
    1. Generates a new gratitude prompt
    2. Sends it to all active users via SMS
    """
    prompt = get_daily_prompt()
    users = get_all_active_users()
    for phone_number, _ in users:
        send_sms(phone_number, prompt)

def weekly_job():
    """
    Weekly scheduled task that:
    1. Gets each user's entries from the past week
    2. Sends a summary email to each active user
    """
    users = get_all_active_users()
    for phone_number, email in users:
        entries = get_weekly_entries(phone_number)
        send_weekly_summary(email, entries)

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
    Schedules:
    1. Daily prompts at 9:00 AM
    2. Weekly summaries on Sundays at 9:00 AM
    """
    schedule.every().day.at("09:00").do(daily_job)
    schedule.every().sunday.at("09:00").do(weekly_job)
    
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
