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

4. Initialize the database:
   ```python
   from mvp_service import init_db
   init_db()
   ```

5. Add users to the database:
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

6. Run the application:
   ```bash
   python main.py
   ```

## Testing

You can test the SMS functionality in two ways:

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
- SQLite database with two tables:
  - `entries`: Stores gratitude journal entries
  - `users`: Manages user subscriptions and preferences

## Deployment

The bot is designed to be deployed on Replit, but can be deployed anywhere with Python support. Note that on Replit:
- The SQLite database is ephemeral (wiped on redeploy)
- Consider using ReplDB or an external database for permanent storage
- The scheduler runs every minute to check each user's preferred time
- Weekly summaries are sent on Sundays at the user's preferred time

## Contributing

Feel free to open issues or submit pull requests! 