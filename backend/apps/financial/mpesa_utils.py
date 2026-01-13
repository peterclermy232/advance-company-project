import requests
import base64
from datetime import datetime
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class MpesaClient:
    """M-Pesa Daraja API Client for STK Push transactions"""

    def __init__(self):
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.shortcode = settings.MPESA_SHORTCODE
        self.passkey = settings.MPESA_PASSKEY
        self.callback_url = settings.MPESA_CALLBACK_URL

        self.base_url = (
            'https://api.safaricom.co.ke'
            if settings.MPESA_ENVIRONMENT == 'production'
            else 'https://sandbox.safaricom.co.ke'
        )

        self.auth_url = f'{self.base_url}/oauth/v1/generate?grant_type=client_credentials'
        self.stk_push_url = f'{self.base_url}/mpesa/stkpush/v1/processrequest'
        self.query_url = f'{self.base_url}/mpesa/stkpushquery/v1/query'

    def get_access_token(self):
        """Get M-Pesa access token with caching"""
        cache_key = f"mpesa_token_{settings.MPESA_ENVIRONMENT}"
        token = cache.get(cache_key)

        if token:
            return token

        try:
            credentials = f"{self.consumer_key}:{self.consumer_secret}"
            encoded = base64.b64encode(credentials.encode()).decode()

            headers = {"Authorization": f"Basic {encoded}"}
            response = requests.get(self.auth_url, headers=headers, timeout=30)
            response.raise_for_status()

            token = response.json()['access_token']
            # Cache for 55 minutes (token valid for 1 hour)
            cache.set(cache_key, token, 3300)
            return token
        except requests.RequestException as e:
            logger.error(f"Failed to get M-Pesa access token: {e}")
            raise

    def generate_password(self):
        """Generate M-Pesa password and timestamp"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        data = f"{self.shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(data.encode()).decode()
        return password, timestamp

    def format_phone_number(self, phone_number):
        """Format phone number to M-Pesa standard (254XXXXXXXXX)"""
        phone_number = phone_number.replace('+', '').replace(' ', '').strip()
        
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif phone_number.startswith('254'):
            pass  # Already in correct format
        elif phone_number.startswith('7') or phone_number.startswith('1'):
            phone_number = '254' + phone_number
        
        return phone_number

    def stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """
        Initiate STK Push request
        
        Args:
            phone_number: Customer phone number
            amount: Amount to charge
            account_reference: Reference for the transaction (max 12 chars)
            transaction_desc: Description of transaction (max 13 chars)
            
        Returns:
            dict: Response from M-Pesa API
        """
        try:
            token = self.get_access_token()
            password, timestamp = self.generate_password()
            phone_number = self.format_phone_number(phone_number)

            payload = {
                "BusinessShortCode": self.shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),
                "PartyA": phone_number,
                "PartyB": self.shortcode,
                "PhoneNumber": phone_number,
                "CallBackURL": self.callback_url,
                "AccountReference": str(account_reference)[:12],
                "TransactionDesc": str(transaction_desc)[:13],
            }

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            logger.info(f"Initiating STK Push for {phone_number}, amount: {amount}")
            response = requests.post(
                self.stk_push_url, 
                json=payload, 
                headers=headers, 
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"STK Push response: {result}")
            return result
            
        except requests.RequestException as e:
            logger.error(f"M-Pesa STK Push failed: {e}")
            raise

    def query_transaction(self, checkout_request_id):
        """
        Query the status of an STK Push transaction
        
        Args:
            checkout_request_id: CheckoutRequestID from STK Push response
            
        Returns:
            dict: Transaction status
        """
        try:
            token = self.get_access_token()
            password, timestamp = self.generate_password()

            payload = {
                "BusinessShortCode": self.shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": checkout_request_id,
            }

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            response = requests.post(
                self.query_url, 
                json=payload, 
                headers=headers, 
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"M-Pesa query failed: {e}")
            raise


# Singleton instance
mpesa_client = MpesaClient()


def initiate_stk_push(phone_number, amount, account_reference, transaction_desc):
    """
    Helper function to initiate STK Push
    
    Returns:
        dict: Success response or error dict
    """
    try:
        response = mpesa_client.stk_push(
            phone_number, 
            amount, 
            account_reference, 
            transaction_desc
        )
        return {
            'success': True,
            'data': response
        }
    except Exception as e:
        logger.error(f"MPESA STK Push failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def query_stk_push_status(checkout_request_id):
    """
    Helper function to query STK Push status
    
    Returns:
        dict: Transaction status or error dict
    """
    try:
        response = mpesa_client.query_transaction(checkout_request_id)
        return {
            'success': True,
            'data': response
        }
    except Exception as e:
        logger.error(f"MPESA query failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }