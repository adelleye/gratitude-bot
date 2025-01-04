"""
Core service module for the Gratitude Journaling Bot.
Handles database operations, SMS interactions, and email summaries.
"""

import os
import sqlite3
from datetime import datetime, timedelta
from twilio.rest import Client
from openai import OpenAI
from email.mime.text import MIMEText
import smtplib
import json
from replit import db as repl_db

# Initialize Twilio client for SMS functionality
twilio_client = Client(
    os.environ.get('TWILIO_ACCOUNT_SID'),
    os.environ.get('TWILIO_AUTH_TOKEN')
)

# Initialize DeepSeek client for AI-generated prompts
deepseek_client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com"
)

def is_replit_env():
    """Check if we're running on Replit."""
    return os.environ.get('REPL_ID') is not None

def init_db():
    """
    Initialize database (SQLite for local dev, ReplDB for production).
    Creates necessary tables/keys if they don't exist.
    """
    if is_replit_env():
        # Initialize ReplDB structure
        if 'users' not in repl_db:
            repl_db['users'] = {}
        if 'entries' not in repl_db:
            repl_db['entries'] = []
            
        # Add example user if not exists (for demonstration)
        users = repl_db['users']
        if not users:  # Only add example if no users exist
            users['+1234567890'] = {
                'email': 'example@email.com',
                'timezone': 'America/New_York',
                'preferred_time': '20:00',
                'active': True
            }
            repl_db['users'] = users
    else:
        # Use SQLite for local development
        conn = sqlite3.connect("gratitude.db")
        c = conn.cursor()
        
        c.execute("DROP TABLE IF EXISTS entries")
        c.execute("DROP TABLE IF EXISTS users")
        
        c.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            entry_text TEXT NOT NULL
        )
        """)
        
        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            phone_number TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            timezone TEXT NOT NULL DEFAULT 'America/New_York',
            preferred_time TIME NOT NULL DEFAULT '19:00',
            active BOOLEAN DEFAULT TRUE
        )
        """)
        
        # Add example user (for demonstration)
        c.execute("""
        INSERT OR REPLACE INTO users (phone_number, email, timezone, preferred_time, active)
        VALUES (?, ?, ?, ?, ?)
        """, ('+1234567890', 'example@email.com', 'America/New_York', '20:00', True))
        
        conn.commit()
        conn.close()

def get_all_active_users():
    """Get all active users from the database."""
    if is_replit_env():
        users = repl_db['users']
        active_users = []
        for phone, data in users.items():
            if data.get('active', True):
                active_users.append((
                    phone,
                    data['email'],
                    data['timezone'],
                    data['preferred_time']
                ))
        return active_users
    else:
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

def insert_entry(phone_number, text):
    """Store a gratitude journal entry."""
    if is_replit_env():
        entries = repl_db['entries']
        entry = {
            'phone_number': phone_number,
            'timestamp': datetime.now().isoformat(),
            'entry_text': text
        }
        entries.append(entry)
        repl_db['entries'] = entries
    else:
        conn = sqlite3.connect("gratitude.db")
        c = conn.cursor()
        c.execute("INSERT INTO entries (phone_number, entry_text) VALUES (?, ?)", 
                (phone_number, text))
        conn.commit()
        conn.close()

def get_weekly_entries(phone_number):
    """Get the last 7 days of entries for a user."""
    if is_replit_env():
        entries = repl_db['entries']
        one_week_ago = datetime.now() - timedelta(days=7)
        
        user_entries = []
        for entry in entries:
            if (entry['phone_number'] == phone_number and
                datetime.fromisoformat(entry['timestamp']) >= one_week_ago):
                user_entries.append((
                    entry['entry_text'],
                    entry['timestamp']
                ))
        return user_entries
    else:
        conn = sqlite3.connect("gratitude.db")
        c = conn.cursor()
        c.execute("""
        SELECT entry_text, timestamp 
        FROM entries 
        WHERE phone_number = ? 
        AND timestamp >= date('now', '-7 days')
        ORDER BY timestamp DESC
        """, (phone_number,))
        entries = c.fetchall()
        conn.close()
        return entries

def update_user_status(phone_number, active):
    """Update user's active status."""
    if is_replit_env():
        users = repl_db['users']
        if phone_number in users:
            users[phone_number]['active'] = active
            repl_db['users'] = users
    else:
        conn = sqlite3.connect("gratitude.db")
        c = conn.cursor()
        c.execute("UPDATE users SET active = ? WHERE phone_number = ?", 
                 (active, phone_number))
        conn.commit()
        conn.close()

def get_daily_prompt():
    """
    Generate a unique daily gratitude prompt using DeepSeek's AI.
    Returns a clean, quote-free prompt suitable for SMS.
    
    Returns:
        str: A gratitude prompt question
    """
    try:
        # Add timestamp for uniqueness in each request
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "You are a friendly and creative coach that generates very short gratitude prompts. Rules: 1) Keep it under 20 words 2) Never use quotation marks 3) Write in a direct, conversational tone 4) End with a question mark if asking a question"
                },
                {
                    "role": "user",
                    "content": f"Generate a unique gratitude prompt for {current_time}. Make it personal and thought-provoking, but never use quotes."
                }
            ],
            temperature=0.9,  # Higher temperature for more variety
            max_tokens=64,
            presence_penalty=0.6,  # Reduce repetition
            frequency_penalty=0.6  # Reduce repetition
        )
        
        # Clean up the response and ensure proper formatting
        prompt = response.choices[0].message.content
        prompt = prompt.replace('"', '').replace("'", '').strip()
        if prompt and not prompt[-1] in '.!?':
            prompt += '?'
        return prompt
    except Exception as e:
        print(f"Error getting prompt from DeepSeek: {e}")
        return "What are you grateful for today?"

def send_sms(to_number, body):
    """
    Send an SMS message using Twilio.
    
    Args:
        to_number (str): Recipient's phone number
        body (str): Message content
    
    Returns:
        str or None: Message SID if successful, None if failed
    """
    try:
        message = twilio_client.messages.create(
            body=body,
            from_=os.environ.get('TWILIO_PHONE_NUMBER'),
            to=to_number
        )
        return message.sid
    except Exception as e:
        print(f"Error sending SMS: {e}")
        return None

def send_weekly_summary(email, entries):
    """
    Send a weekly email summary of gratitude entries.
    
    Args:
        email (str): Recipient's email address
        entries (list): List of (entry_text, timestamp) tuples
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    if not entries:
        body = "We missed you this week! Looking forward to your gratitude entries next week. 🌟"
    else:
        entries_text = "\n".join([f"- {entry[0]} ({entry[1]})" for entry in entries])
        body = f"""Your Weekly Gratitude Summary 🌟

Here are your gratitude moments from the past week:

{entries_text}

Keep cultivating gratitude! See you next week.
"""
    
    message = MIMEText(body, "plain")
    message["Subject"] = "Your Weekly Gratitude Summary"
    message["From"] = os.environ.get('SMTP_FROM_EMAIL')
    message["To"] = email

    try:
        with smtplib.SMTP(os.environ.get('SMTP_SERVER'), 587) as server:
            server.starttls()
            server.login(
                os.environ.get('SMTP_USERNAME'),
                os.environ.get('SMTP_PASSWORD')
            )
            server.send_message(message)
            return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False 