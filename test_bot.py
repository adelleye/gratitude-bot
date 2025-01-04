"""
Comprehensive test script for the Gratitude Bot.
This script verifies all major functionality including:
- Database operations
- SMS sending/receiving
- Email functionality
- Prompt generation
- User management
- Timezone handling
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import pytz
import os
from datetime import datetime, timedelta
from mvp_service import (
    init_db, get_daily_prompt, send_sms, send_weekly_summary,
    insert_entry, get_recent_entries, is_replit_env
)
from admin_tools import add_user, list_users, update_user, delete_user

class TestGratitudeBot(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        # Mock environment variables
        self.env_patcher = patch.dict('os.environ', {
            'TWILIO_ACCOUNT_SID': 'test_sid',
            'TWILIO_AUTH_TOKEN': 'test_token',
            'TWILIO_PHONE_NUMBER': '+15555555555',
            'DEEPSEEK_API_KEY': 'test_key',
            'SMTP_FROM_EMAIL': 'test@example.com',
            'SMTP_SERVER': 'smtp.test.com',
            'SMTP_USERNAME': 'test_user',
            'SMTP_PASSWORD': 'test_pass'
        })
        self.env_patcher.start()
        
        # Create a shared mock database for both modules
        self.db_mock = {}
        
        # Mock ReplDB for mvp_service
        self.mvp_db_patcher = patch('mvp_service.repl_db', self.db_mock)
        self.mvp_db_patcher.start()
        
        # Mock ReplDB for admin_tools
        self.admin_db_patcher = patch('admin_tools.repl_db', self.db_mock)
        self.admin_db_patcher.start()
        
        # Mock is_replit_env to always return True for testing
        self.replit_env_patcher = patch('mvp_service.is_replit_env', return_value=True)
        self.replit_env_patcher.start()
        
        # Mock Twilio client
        self.twilio_mock = MagicMock()
        self.twilio_mock.messages = MagicMock()
        self.twilio_mock.messages.create = MagicMock(return_value=MagicMock(sid='test_sid'))
        self.twilio_patcher = patch('mvp_service.twilio_client', self.twilio_mock)
        self.twilio_patcher.start()
        
        # Mock SMTP
        self.smtp_mock = MagicMock()
        self.smtp_instance = MagicMock()
        self.smtp_instance.__enter__ = MagicMock(return_value=self.smtp_instance)
        self.smtp_instance.__exit__ = MagicMock(return_value=None)
        self.smtp_mock.return_value = self.smtp_instance
        self.smtp_patcher = patch('smtplib.SMTP', self.smtp_mock)
        self.smtp_patcher.start()
        
        # Mock DeepSeek client
        self.deepseek_mock = MagicMock()
        self.deepseek_mock.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content="What made you smile today?"))
        ]
        self.deepseek_patcher = patch('mvp_service.deepseek_client', self.deepseek_mock)
        self.deepseek_patcher.start()
        
        # Initialize test database without example user
        init_db(skip_example=True)
        
        # Add test user
        self.test_phone = "+1234567890"
        self.test_email = "test@example.com"
        self.test_timezone = "America/New_York"
        self.test_time = "20:00"
        add_user(self.test_phone, self.test_email, self.test_timezone, self.test_time)

    def tearDown(self):
        """Clean up after each test."""
        self.env_patcher.stop()
        self.mvp_db_patcher.stop()
        self.admin_db_patcher.stop()
        self.replit_env_patcher.stop()
        self.twilio_patcher.stop()
        self.smtp_patcher.stop()
        self.deepseek_patcher.stop()
        
        # Clear test database
        self.db_mock.clear()

    def test_database_operations(self):
        """Test basic database operations."""
        # Test user exists
        users = self.db_mock.get('users', {})
        self.assertIn(self.test_phone, users)
        
        # Test user data is correct
        user_data = users[self.test_phone]
        self.assertEqual(user_data['email'], self.test_email)
        self.assertEqual(user_data['timezone'], self.test_timezone)
        self.assertEqual(user_data['preferred_time'], self.test_time)
        
        # Test updating user
        update_user(self.test_phone, timezone="America/Los_Angeles")
        updated_user = self.db_mock['users'][self.test_phone]
        self.assertEqual(updated_user['timezone'], "America/Los_Angeles")
        
        # Test deleting user
        delete_user(self.test_phone)
        self.assertNotIn(self.test_phone, self.db_mock['users'])

    def test_prompt_generation(self):
        """Test daily prompt generation."""
        prompt = get_daily_prompt()
        self.assertIsInstance(prompt, str)
        self.assertTrue(len(prompt) > 0)
        self.assertNotIn('"', prompt)  # Verify no quotes in prompt

    def test_sms_functionality(self):
        """Test SMS sending and receiving."""
        # Test sending SMS
        message = "Test prompt"
        send_sms(self.test_phone, message)
        
        self.twilio_mock.messages.create.assert_called_once_with(
            to=self.test_phone,
            from_=os.environ['TWILIO_PHONE_NUMBER'],
            body=message
        )
        
        # Test storing response
        test_response = "I am grateful for this test passing"
        insert_entry(self.test_phone, test_response)
        
        entries = self.db_mock.get('entries', [])
        self.assertTrue(any(entry['entry_text'] == test_response for entry in entries))

    def test_email_functionality(self):
        """Test email sending for weekly summaries."""
        # Store some test entries
        test_entries = [
            ("Test entry 1", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            ("Test entry 2", (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"))
        ]
        
        # Test sending weekly summary
        send_weekly_summary(self.test_email, test_entries)
        
        # Verify SMTP setup
        self.smtp_mock.assert_called_once_with(
            os.environ['SMTP_SERVER'],
            587
        )
        
        # Verify SMTP operations
        self.smtp_instance.starttls.assert_called_once()
        self.smtp_instance.login.assert_called_once_with(
            os.environ['SMTP_USERNAME'],
            os.environ['SMTP_PASSWORD']
        )
        self.smtp_instance.send_message.assert_called_once()
        
        # Verify message content
        sent_message = self.smtp_instance.send_message.call_args[0][0]
        self.assertEqual(sent_message['To'], self.test_email)
        self.assertEqual(sent_message['From'], os.environ['SMTP_FROM_EMAIL'])
        self.assertEqual(sent_message['Subject'], "Your Weekly Gratitude Summary")
        
        # Get and decode message payload
        payload = sent_message.get_payload()
        if sent_message['Content-Transfer-Encoding'] == 'base64':
            import base64
            payload = base64.b64decode(payload).decode('utf-8')
        
        # Verify email content
        self.assertIn("Test entry 1", payload)
        self.assertIn("Test entry 2", payload)
        self.assertIn("Your Weekly Gratitude Summary", payload)
        self.assertIn("Keep cultivating gratitude!", payload)

    def test_timezone_handling(self):
        """Test timezone-aware operations."""
        # Add users in different timezones
        add_user("+1987654321", "test2@example.com", "America/Los_Angeles", "18:00")
        add_user("+1555555555", "test3@example.com", "Europe/London", "19:00")
        
        # Verify users in different timezones
        users = self.db_mock.get('users', {})
        self.assertEqual(users["+1987654321"]['timezone'], "America/Los_Angeles")
        self.assertEqual(users["+1555555555"]['timezone'], "Europe/London")
        
        # Test time conversion
        la_time = datetime.now(pytz.timezone("America/Los_Angeles"))
        london_time = datetime.now(pytz.timezone("Europe/London"))
        self.assertNotEqual(la_time.hour, london_time.hour)

    def test_recent_entries(self):
        """Test retrieving recent entries."""
        # Store multiple entries
        entries = [
            "First test entry",
            "Second test entry",
            "Third test entry"
        ]
        
        for entry in entries:
            insert_entry(self.test_phone, entry)
            
        # Test retrieving recent entries
        recent = get_recent_entries(self.test_phone)
        self.assertEqual(len(recent), len(entries))
        
        # Verify entries are in correct order (most recent first)
        for i, entry in enumerate(reversed(entries)):
            self.assertEqual(recent[i][0], entry)

def run_tests():
    """Run all tests and print results."""
    print("Starting Gratitude Bot Tests...")
    print("-" * 50)
    
    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGratitudeBot)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # Print summary
    print("\nTest Summary:")
    print(f"Ran {result.testsRun} tests")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1) 