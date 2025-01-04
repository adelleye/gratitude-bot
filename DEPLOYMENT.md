# Deployment Checklist

## 1. Environment Setup
- [ ] Set up all required secrets in Replit:
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

## 2. Twilio Configuration
- [ ] Verify Twilio account is active and funded
- [ ] Verify Twilio phone number is SMS-capable
- [ ] Get your Replit deployment URL
- [ ] Configure Twilio webhook:
  1. Go to Twilio Console > Phone Numbers > Your Number
  2. Under "Messaging", find "When a message comes in"
  3. Set webhook URL to: `YOUR_REPLIT_URL/sms`
  4. Set method to HTTP POST

## 3. Email Configuration
- [ ] Test SMTP server connection
- [ ] Verify email sending works:
  ```python
  from mvp_service import send_weekly_summary
  send_weekly_summary("your_test@email.com", [("Test entry", "2024-01-01 12:00:00")])
  ```

## 4. Database Setup
- [ ] Initialize database:
  ```python
  from mvp_service import init_db
  init_db()
  ```
- [ ] Add test user:
  ```python
  python admin_tools.py
  # Choose option 2 (Add new user)
  ```
- [ ] Verify user appears in database:
  ```python
  python admin_tools.py
  # Choose option 1 (List all users)
  ```

## 5. Replit Deployment
- [ ] Push latest code to GitHub
- [ ] In Replit Deployments tab:
  1. Choose "Autoscale" deployment
  2. Set the following:
     - Build Command: `pip install -r requirements.txt`
     - Run Command: `python main.py`
     - Port: 8080

## 6. Testing Checklist
Before adding real users:
- [ ] Test daily prompt generation:
  ```python
  from mvp_service import get_daily_prompt
  print(get_daily_prompt())
  ```
- [ ] Test SMS sending:
  ```python
  from main import daily_job
  daily_job(force=True)  # Should send to all users
  ```
- [ ] Test SMS receiving:
  1. Send a test SMS to your Twilio number
  2. Check if it's stored in ReplDB:
     ```python
     from replit import db
     print(db['entries'])
     ```
- [ ] Test weekly summary:
  ```python
  from main import weekly_job
  weekly_job()  # Should send summary emails
  ```

## 7. Production Launch
- [ ] Add real users using admin_tools.py
- [ ] Monitor first day of prompts
- [ ] Check first weekly summary
- [ ] Set up monitoring:
  1. Check Replit logs daily
  2. Monitor Twilio dashboard for SMS delivery
  3. Check email delivery success

## 8. Backup Plan
- [ ] Document how to export user data:
  ```python
  from replit import db
  import json
  
  # Export users
  with open('users_backup.json', 'w') as f:
      json.dump(dict(db['users']), f)
      
  # Export entries
  with open('entries_backup.json', 'w') as f:
      json.dump(list(db['entries']), f)
  ```
- [ ] Document how to restore from backup:
  ```python
  from replit import db
  import json
  
  # Restore users
  with open('users_backup.json', 'r') as f:
      db['users'] = json.load(f)
      
  # Restore entries
  with open('entries_backup.json', 'r') as f:
      db['entries'] = json.load(f)
  ```

## 9. Troubleshooting Guide
Common issues and solutions:

1. **SMS not sending**
   - Check Twilio balance
   - Verify phone numbers are in correct format (+1234567890)
   - Check Twilio logs for errors

2. **Webhook not receiving**
   - Verify Replit is running
   - Check Twilio webhook URL configuration
   - Check Replit logs for incoming requests

3. **Emails not sending**
   - Verify SMTP credentials
   - Check spam folders
   - Verify email format

4. **Database issues**
   - Use admin_tools.py to verify user data
   - Check ReplDB connection
   - Consider backing up data

## 10. Maintenance Tasks
Weekly:
- [ ] Check Replit logs for errors
- [ ] Monitor Twilio credit balance
- [ ] Verify all users are receiving prompts
- [ ] Back up user data

Monthly:
- [ ] Review and clean up old entries
- [ ] Check for any inactive users
- [ ] Update dependencies if needed
- [ ] Review Replit usage/credits 