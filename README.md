# Gratitude Journaling Bot

A simple but powerful SMS-based gratitude journaling bot that helps users cultivate daily gratitude through:
- Daily AI-generated prompts via SMS at their preferred time
- Easy response collection via text message
- Weekly email summaries of gratitude entries

## Features

- 📱 Daily SMS prompts using Twilio
- 🤖 AI-generated prompts using DeepSeek
- 📧 Weekly email summaries
- 🔒 Timezone-aware scheduling (prompts sent at user's preferred time)
- 🔒 Privacy-focused (each user's entries are private)
- ⚡ Easy unsubscribe with "STOP" message

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```
   TWILIO_ACCOUNT_SID=your_sid
   TWILIO_AUTH_TOKEN=your_token
   TWILIO_PHONE_NUMBER=your_number
   DEEPSEEK_API_KEY=your_key
   SMTP_FROM_EMAIL=your_email
   SMTP_SERVER=your_server
   SMTP_USERNAME=your_username
   SMTP_PASSWORD=your_password
   ```

4. Choose your database setup (see Database Options below)

5. Initialize the database:
   ```python
   from mvp_service import init_db
   init_db()
   ```

6. Add users to the database:
   ```sql
   INSERT INTO users (phone_number, email, timezone, preferred_time, active) 
   VALUES (
       '+1234567890',           -- User's phone number
       'user@example.com',      -- Email for weekly summaries
       'America/New_York',      -- User's timezone
       '20:00',                 -- Preferred time (24-hour format)
       TRUE
   );
   ```

7. Run the application:
   ```bash
   python main.py
   ```

## Database Options

The bot supports multiple database options:

### 1. Replit Database (Default for Replit deployment)
- Built-in, no setup required
- Data persists across deploys
- Free with Replit account
- Already implemented in the code

### 2. SQLite (Default for local development)
- Local file-based database
- Good for development and testing
- Already implemented in the code
- Note: Data may be lost on Replit deploys

### 3. MongoDB Atlas (Alternative for production)
1. Create free MongoDB Atlas account
2. Add to requirements.txt:
   ```
   pymongo==4.6.1
   ```
3. Add environment variable:
   ```
   MONGODB_URI=your_mongodb_uri
   ```
4. Create `mongodb_service.py`:
   ```python
   from pymongo import MongoClient
   
   client = MongoClient(os.environ.get('MONGODB_URI'))
   db = client.gratitude_bot
   
   def init_db():
       # Create indexes
       db.users.create_index('phone_number', unique=True)
       db.entries.create_index([('phone_number', 1), ('timestamp', -1)])
   
   def insert_entry(phone_number, text):
       db.entries.insert_one({
           'phone_number': phone_number,
           'timestamp': datetime.now(),
           'entry_text': text
       })
   ```

### 4. PostgreSQL (Alternative for production)
1. Create free PostgreSQL database (e.g., on Railway or Supabase)
2. Add to requirements.txt:
   ```
   psycopg2-binary==2.9.9
   ```
3. Add environment variable:
   ```
   DATABASE_URL=your_postgresql_url
   ```
4. Create `postgresql_service.py`:
   ```python
   import psycopg2
   from psycopg2.extras import DictCursor
   
   def get_db():
       return psycopg2.connect(os.environ.get('DATABASE_URL'))
   
   def init_db():
       with get_db() as conn:
           with conn.cursor() as cur:
               cur.execute("""
               CREATE TABLE IF NOT EXISTS users (
                   phone_number TEXT PRIMARY KEY,
                   email TEXT NOT NULL,
                   timezone TEXT NOT NULL,
                   preferred_time TIME NOT NULL,
                   active BOOLEAN DEFAULT TRUE
               )
               """)
   ```

## Testing

You can test the functionality in two ways:

1. Force immediate sending (bypass time check):
   ```python
   from main import daily_job
   daily_job(force=True)  # Sends immediately
   ```

2. Test real-time behavior:
   ```python
   daily_job()  # Only sends if it's the user's preferred time ±2 minutes
   ```

## Architecture

- `main.py`: Web server setup, webhook handling, and task scheduling
- `mvp_service.py`: Core functionality (database, SMS, email, AI prompts)
- Database options:
  - ReplDB (Replit's key-value store)
  - SQLite (local development)
  - MongoDB (optional)
  - PostgreSQL (optional)

## Deployment

The bot is designed to be deployed on Replit, but can be deployed anywhere with Python support:

### Replit Deployment
- Uses ReplDB for persistence
- Scheduler runs every minute
- Weekly summaries on Sundays
- Free tier works well for small user base

### Alternative Deployment Options
1. **Heroku**
   - Use PostgreSQL add-on
   - Set up Heroku Scheduler for jobs
   - Requires credit card for free tier

2. **Railway**
   - Built-in PostgreSQL
   - Cron job support
   - Free tier available

3. **DigitalOcean App Platform**
   - MongoDB or PostgreSQL options
   - Built-in job scheduler
   - Starts at $5/month

## Contributing

Feel free to open issues or submit pull requests! 