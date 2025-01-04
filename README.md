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

5. Add users using the admin tools:
   ```bash
   python admin_tools.py
   ```
   Choose option 2 to add a new user with their:
   - Phone number (with country code)
   - Email address
   - Timezone
   - Preferred time for daily prompts

6. Run the application:
   ```bash
   python main.py
   ```

## Testing

The project includes comprehensive tests covering all major functionality:

1. Run all tests:
   ```bash
   python test_bot.py
   ```

2. Test coverage includes:
   - Database operations (user management)
   - SMS functionality (sending/receiving)
   - Email functionality (weekly summaries)
   - Prompt generation
   - Timezone handling
   - Recent entries retrieval

3. Manual testing options:
   ```python
   # Test prompt generation
   from mvp_service import get_daily_prompt
   print(get_daily_prompt())

   # Test SMS sending
   from main import daily_job
   daily_job(force=True)  # Sends to all users

   # Test weekly summary
   from main import weekly_job
   weekly_job()  # Sends summary emails
   ```

4. Admin tools testing:
   ```bash
   python admin_tools.py
   ```
   - List all users (option 1)
   - Add test user (option 2)
   - Update user settings (option 3)
   - Delete user (option 4)

## Architecture

- `main.py`: Web server setup, webhook handling, and task scheduling
- `mvp_service.py`: Core functionality (database, SMS, email, AI prompts)
- `admin_tools.py`: User management interface
- `test_bot.py`: Comprehensive test suite

### Database Structure

1. Users Table:
   - phone_number (primary key)
   - email
   - timezone
   - preferred_time
   - active status

2. Entries Table:
   - phone_number
   - timestamp
   - entry_text

## Deployment

The bot is designed to be deployed on Replit:

1. Fork the repository to your Replit account
2. Set up environment variables in Replit Secrets
3. Run `python main.py` to start the server
4. Configure Twilio webhook to your Replit URL

### Production Considerations

1. Data Backup:
   - Regular database backups
   - Export functionality in admin tools
   - Backup verification procedures

2. Monitoring:
   - Daily prompt delivery logs
   - Weekly summary success rates
   - User engagement metrics

3. Scaling:
   - ReplDB handles concurrent users
   - Rate limiting for API calls
   - Error handling and retries

## Contributing

Feel free to open issues or submit pull requests! 

## License

MIT License - See LICENSE file for details 