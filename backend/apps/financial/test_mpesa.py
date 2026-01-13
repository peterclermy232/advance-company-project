"""
M-Pesa Integration Test Script
Run this script to verify your M-Pesa setup is working correctly
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
django.setup()

from django.conf import settings
import requests
import base64
from datetime import datetime


class MpesaTestSuite:
    """Test suite for M-Pesa integration"""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def test(self, name, condition, error_msg=""):
        """Record test result"""
        if condition:
            self.results.append(f"✅ {name}")
            self.passed += 1
            return True
        else:
            self.results.append(f"❌ {name}: {error_msg}")
            self.failed += 1
            return False
    
    def print_results(self):
        """Print all test results"""
        print("\n" + "="*60)
        print("M-PESA INTEGRATION TEST RESULTS")
        print("="*60 + "\n")
        
        for result in self.results:
            print(result)
        
        print("\n" + "="*60)
        print(f"Total: {self.passed + self.failed} | Passed: {self.passed} | Failed: {self.failed}")
        print("="*60 + "\n")
    
    def run_all_tests(self):
        """Run all tests"""
        print("Starting M-Pesa Integration Tests...\n")
        
        # Test 1: Check environment variables
        self.test_environment_variables()
        
        # Test 2: Check M-Pesa credentials
        self.test_credentials()
        
        # Test 3: Test access token generation
        self.test_access_token()
        
        # Test 4: Check callback URL
        self.test_callback_url()
        
        # Test 5: Test phone number formatting
        self.test_phone_formatting()
        
        # Test 6: Test password generation
        self.test_password_generation()
        
        self.print_results()
        
        return self.failed == 0
    
    def test_environment_variables(self):
        """Test if environment variables are set"""
        print("Testing environment variables...")
        
        required_vars = [
            'MPESA_CONSUMER_KEY',
            'MPESA_CONSUMER_SECRET',
            'MPESA_SHORTCODE',
            'MPESA_PASSKEY',
            'MPESA_CALLBACK_URL',
            'MPESA_ENVIRONMENT'
        ]
        
        all_set = True
        for var in required_vars:
            value = getattr(settings, var, None)
            if not value or value == '':
                self.test(
                    f"Environment variable: {var}",
                    False,
                    f"{var} is not set"
                )
                all_set = False
            else:
                self.test(f"Environment variable: {var}", True)
        
        return all_set
    
    def test_credentials(self):
        """Test if credentials are valid format"""
        print("\nTesting M-Pesa credentials format...")
        
        # Test consumer key length
        consumer_key = settings.MPESA_CONSUMER_KEY
        self.test(
            "Consumer Key format",
            len(consumer_key) > 20,
            f"Consumer key seems too short: {len(consumer_key)} characters"
        )
        
        # Test consumer secret length
        consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.test(
            "Consumer Secret format",
            len(consumer_secret) > 20,
            f"Consumer secret seems too short: {len(consumer_secret)} characters"
        )
        
        # Test shortcode
        shortcode = settings.MPESA_SHORTCODE
        self.test(
            "Shortcode (should be 174379 for sandbox)",
            shortcode == '174379' or shortcode == 174379,
            f"Expected 174379, got {shortcode}"
        )
        
        # Test passkey length
        passkey = settings.MPESA_PASSKEY
        self.test(
            "Passkey format",
            len(passkey) > 50,
            f"Passkey seems too short: {len(passkey)} characters"
        )
    
    def test_access_token(self):
        """Test M-Pesa access token generation"""
        print("\nTesting M-Pesa access token generation...")
        
        try:
            consumer_key = settings.MPESA_CONSUMER_KEY
            consumer_secret = settings.MPESA_CONSUMER_SECRET
            
            credentials = f"{consumer_key}:{consumer_secret}"
            encoded = base64.b64encode(credentials.encode()).decode()
            
            base_url = (
                'https://api.safaricom.co.ke'
                if settings.MPESA_ENVIRONMENT == 'production'
                else 'https://sandbox.safaricom.co.ke'
            )
            
            auth_url = f'{base_url}/oauth/v1/generate?grant_type=client_credentials'
            headers = {"Authorization": f"Basic {encoded}"}
            
            response = requests.get(auth_url, headers=headers, timeout=30)
            
            self.test(
                "M-Pesa API connection",
                response.status_code == 200,
                f"HTTP {response.status_code}: {response.text}"
            )
            
            if response.status_code == 200:
                data = response.json()
                self.test(
                    "Access token generation",
                    'access_token' in data,
                    "No access_token in response"
                )
                
                if 'access_token' in data:
                    print(f"   ℹ️  Token expires in: {data.get('expires_in', 'unknown')} seconds")
            else:
                self.test(
                    "Access token generation",
                    False,
                    f"Failed: {response.text}"
                )
        
        except Exception as e:
            self.test(
                "M-Pesa API connection",
                False,
                f"Exception: {str(e)}"
            )
    
    def test_callback_url(self):
        """Test callback URL format"""
        print("\nTesting callback URL...")
        
        callback_url = settings.MPESA_CALLBACK_URL
        
        self.test(
            "Callback URL is HTTPS",
            callback_url.startswith('https://'),
            f"Callback URL must be HTTPS, got: {callback_url}"
        )
        
        self.test(
            "Callback URL ends with /mpesa/callback/",
            callback_url.endswith('/mpesa/callback/'),
            f"Callback URL should end with /mpesa/callback/, got: {callback_url}"
        )
        
        # Check if URL is reachable (optional, might fail in local dev)
        if 'ngrok' in callback_url or 'localhost' not in callback_url:
            try:
                response = requests.get(callback_url.replace('/mpesa/callback/', '/'), timeout=5)
                self.test(
                    "Callback URL is accessible",
                    response.status_code in [200, 404, 405],  # 404/405 is ok, means server is up
                    f"Cannot reach callback URL"
                )
            except:
                print("   ⚠️  Warning: Could not verify callback URL accessibility (this is OK for local dev)")
    
    def test_phone_formatting(self):
        """Test phone number formatting"""
        print("\nTesting phone number formatting...")
        
        from apps.finances.mpesa_utils import mpesa_client
        
        test_cases = [
            ('0712345678', '254712345678'),
            ('+254712345678', '254712345678'),
            ('254712345678', '254712345678'),
            ('712345678', '254712345678'),
        ]
        
        for input_phone, expected in test_cases:
            result = mpesa_client.format_phone_number(input_phone)
            self.test(
                f"Format phone: {input_phone} → {expected}",
                result == expected,
                f"Got {result}, expected {expected}"
            )
    
    def test_password_generation(self):
        """Test M-Pesa password generation"""
        print("\nTesting password generation...")
        
        from apps.finances.mpesa_utils import mpesa_client
        
        password, timestamp = mpesa_client.generate_password()
        
        self.test(
            "Password generation",
            len(password) > 50,
            f"Password seems too short: {len(password)} characters"
        )
        
        self.test(
            "Timestamp format",
            len(timestamp) == 14,
            f"Timestamp should be 14 characters, got {len(timestamp)}"
        )
        
        # Verify timestamp is valid
        try:
            datetime.strptime(timestamp, '%Y%m%d%H%M%S')
            self.test("Timestamp is valid datetime", True)
        except:
            self.test("Timestamp is valid datetime", False, f"Invalid timestamp: {timestamp}")


def main():
    """Run the test suite"""
    print("\n" + "="*60)
    print("M-PESA INTEGRATION TEST SUITE")
    print("="*60 + "\n")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  WARNING: .env file not found!")
        print("Please create a .env file with your M-Pesa credentials\n")
    
    suite = MpesaTestSuite()
    success = suite.run_all_tests()
    
    if success:
        print("🎉 All tests passed! Your M-Pesa integration is ready to use.")
        print("\nNext steps:")
        print("1. Start your Django server: python manage.py runserver")
        print("2. Start ngrok: ngrok http 8000")
        print("3. Update MPESA_CALLBACK_URL in .env with ngrok URL")
        print("4. Test creating a deposit via API")
    else:
        print("⚠️  Some tests failed. Please fix the issues above before proceeding.")
        print("\nCommon fixes:")
        print("- Make sure .env file exists with correct credentials")
        print("- Get credentials from https://developer.safaricom.co.ke/")
        print("- Use shortcode 174379 for sandbox")
        print("- Ensure ngrok is running for callback URL")
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())