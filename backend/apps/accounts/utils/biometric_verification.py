import base64
import hashlib
import hmac
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend
from django.core.cache import cache
from django.conf import settings
import secrets

class BiometricVerifier:
    """Secure biometric verification using public key cryptography"""
    
    @staticmethod
    def generate_challenge(user_email: str) -> str:
        """Generate a cryptographic challenge for authentication"""
        challenge = secrets.token_urlsafe(32)
        # Store challenge in cache with 5-minute expiration
        cache_key = f"biometric_challenge_{user_email}"
        cache.set(cache_key, challenge, timeout=300)
        return challenge
    
    @staticmethod
    def verify_signature(user_email: str, public_key_pem: str, 
                        signature: str, challenge_response: str) -> bool:
        """
        Verify the biometric signature using stored public key
        
        Args:
            user_email: User's email
            public_key_pem: PEM-encoded public key
            signature: Base64-encoded signature
            challenge_response: The challenge we sent
            
        Returns:
            bool: True if signature is valid
        """
        try:
            # Retrieve stored challenge
            cache_key = f"biometric_challenge_{user_email}"
            stored_challenge = cache.get(cache_key)
            
            if not stored_challenge:
                return False
            
            # Verify challenge matches
            if stored_challenge != challenge_response:
                return False
            
            # Load public key
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode('utf-8'),
                backend=default_backend()
            )
            
            # Decode signature
            signature_bytes = base64.b64decode(signature)
            challenge_bytes = challenge_response.encode('utf-8')
            
            # Verify signature
            public_key.verify(
                signature_bytes,
                challenge_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            # Clear challenge after successful verification
            cache.delete(cache_key)
            return True
            
        except Exception as e:
            print(f"Biometric verification error: {str(e)}")
            return False
    
    @staticmethod
    def validate_public_key(public_key_pem: str) -> bool:
        """Validate that the public key is properly formatted"""
        try:
            serialization.load_pem_public_key(
                public_key_pem.encode('utf-8'),
                backend=default_backend()
            )
            return True
        except:
            return False