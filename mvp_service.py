"""
Core service module for the Gratitude Journaling Bot.
Handles database operations, SMS interactions, and email summaries.
"""

import os
import sqlite3
from datetime import datetime
from twilio.rest import Client
from openai import OpenAI
from email.mime.text import MIMEText
import smtplib

# Initialize Twilio client for SMS functionality
twilio_client = Client(
    os.environ.get('TWILIO_ACCOUNT_SID'),
    os.environ.get('TWILIO_AUTH_TOKEN')
)

# Initialize DeepSeek client for AI-generated prompts
# Using OpenAI's SDK with DeepSeek's API for compatibility
deepseek_client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com"
)

def init_db():
    """
    Initialize SQLite database with two tables:
    1. entries: Stores user's gratitude journal entries
    2. users: Stores user information and preferences
    
    Note: On Replit, database will be wiped on redeploy
    """
    conn = sqlite3.connect("gratitude.db")
    c = conn.cursor()
    
    # Create entries table for storing gratitude responses
    c.execute("""
    CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone_number TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        entry_text TEXT NOT NULL
    )
    """)
    
    # Create users table for managing subscriptions
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        phone_number TEXT PRIMARY KEY,
        email TEXT NOT NULL,
        active BOOLEAN DEFAULT TRUE
    )
    """)
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

def insert_entry(phone_number, text):
    """
    Store a gratitude journal entry in the database.
    
    Args:
        phone_number (str): User's phone number
        text (str): Gratitude entry text
    """
    conn = sqlite3.connect("gratitude.db")
    c = conn.cursor()
    c.execute("INSERT INTO entries (phone_number, entry_text) VALUES (?, ?)", 
              (phone_number, text))
    conn.commit()
    conn.close()

def get_weekly_entries(phone_number):
    """
    Retrieve the last 7 days of entries for a user.
    
    Args:
        phone_number (str): User's phone number
    
    Returns:
        list: List of (entry_text, timestamp) tuples
    """
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