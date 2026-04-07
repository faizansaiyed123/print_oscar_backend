"""Security and PCI compliance utilities for payment processing."""

import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger(__name__)


class PCIComplianceManager:
    """Manages PCI DSS compliance for payment processing."""
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        self.encryption_key = encryption_key or self._generate_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # PCI DSS requirements tracking
        self.sensitive_data_operations = []
        self.audit_log = []
    
    def _generate_key(self) -> bytes:
        """Generate encryption key for sensitive data."""
        return Fernet.generate_key()
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive payment data."""
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            self._log_sensitive_operation("encrypt", len(data))
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Data encryption failed: {str(e)}")
            raise
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive payment data."""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(encrypted_bytes)
            self._log_sensitive_operation("decrypt", len(decrypted_data))
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Data decryption failed: {str(e)}")
            raise
    
    def hash_card_data(self, card_number: str) -> str:
        """Hash card number for comparison (PCI compliant)."""
        # Use SHA-256 with salt for card hashing
        salt = "payment_salt_constant"  # In production, use proper salt management
        return hashlib.sha256((card_number + salt).encode()).hexdigest()
    
    def mask_card_number(self, card_number: str, mask_char: str = "*") -> str:
        """Mask card number for display (PCI compliant)."""
        if len(card_number) < 4:
            return mask_char * len(card_number)
        
        last4 = card_number[-4:]
        masked_length = len(card_number) - 4
        return mask_char * masked_length + last4
    
    def validate_card_number(self, card_number: str) -> bool:
        """Validate card number using Luhn algorithm."""
        def luhn_checksum(card_num: str) -> bool:
            def digits_of(n: str) -> list[int]:
                return [int(d) for d in n]
            
            digits = digits_of(card_num)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = 0
            checksum += sum(odd_digits)
            
            for d in even_digits:
                checksum += sum(digits_of(str(d * 2)))
            
            return checksum % 10 == 0
        
        # Remove spaces and dashes
        clean_number = card_number.replace(" ", "").replace("-", "")
        
        # Check if numeric and valid length
        if not clean_number.isdigit() or not (13 <= len(clean_number) <= 19):
            return False
        
        return luhn_checksum(clean_number)
    
    def validate_expiry_date(self, exp_month: int, exp_year: int) -> bool:
        """Validate card expiry date."""
        if not (1 <= exp_month <= 12):
            return False
        
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # Check if year is in the future or current year
        if exp_year < current_year:
            return False
        
        # If same year, check month
        if exp_year == current_year and exp_month < current_month:
            return False
        
        return True
    
    def validate_cvv(self, cvv: str) -> bool:
        """Validate CVV format."""
        clean_cvv = cvv.replace(" ", "").replace("-", "")
        return clean_cvv.isdigit() and len(clean_cvv) in [3, 4]
    
    def _log_sensitive_operation(self, operation: str, data_length: int):
        """Log sensitive data operations for audit."""
        self.audit_log.append({
            "timestamp": datetime.utcnow(),
            "operation": operation,
            "data_length": data_length,
        })
        
        # Keep audit log manageable
        if len(self.audit_log) > 1000:
            self.audit_log = self.audit_log[-500:]


class WebhookSecurity:
    """Handles webhook signature verification."""
    
    @staticmethod
    def verify_stripe_webhook(
        payload: bytes, 
        signature: str, 
        webhook_secret: str
    ) -> bool:
        """Verify Stripe webhook signature."""
        try:
            import stripe
            
            event = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
            return True
        except Exception as e:
            logger.error(f"Stripe webhook verification failed: {str(e)}")
            return False
    
    @staticmethod
    def verify_paypal_webhook(
        payload: bytes,
        cert_id: str,
        transmission_id: str,
        auth_algo: str,
        transmission_sig: str,
        transmission_time: str,
        webhook_id: str,
    ) -> bool:
        """Verify PayPal webhook signature."""
        try:
            # PayPal webhook verification is complex
            # This is a simplified version
            import hashlib
            import hmac
            
            # Create verification string
            verification_string = f"{transmission_id}|{transmission_time}|{webhook_id}|{crc32(payload)}|"
            
            # Verify signature (simplified)
            expected_sig = hmac.new(
                webhook_secret.encode(),
                verification_string.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_sig, transmission_sig)
            
        except Exception as e:
            logger.error(f"PayPal webhook verification failed: {str(e)}")
            return False
    
    @staticmethod
    def verify_adyen_webhook(
        payload: bytes,
        signature: str,
        hmac_key: str,
    ) -> bool:
        """Verify Adyen webhook signature."""
        try:
            # Adyen uses HMAC-SHA256 for webhook verification
            expected_signature = hmac.new(
                hmac_key.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Adyen webhook verification failed: {str(e)}")
            return False


class FraudDetection:
    """Basic fraud detection for payments."""
    
    def __init__(self):
        self.suspicious_patterns = {
            "velocity_check": timedelta(minutes=15),
            "amount_threshold": 10000.00,  # $10,000
            "ip_velocity": timedelta(hours=1),
        }
    
    async def check_payment_risk(
        self,
        customer_email: str,
        amount: float,
        customer_ip: str,
        card_hash: Optional[str] = None,
        db_session=None,
    ) -> Dict[str, Any]:
        """Check payment for fraud indicators."""
        risk_score = 0
        risk_factors = []
        
        # Check amount threshold
        if amount > self.suspicious_patterns["amount_threshold"]:
            risk_score += 30
            risk_factors.append("high_amount")
        
        # Check velocity (multiple payments in short time)
        recent_payments = await self._get_recent_payments(
            customer_email, 
            self.suspicious_patterns["velocity_check"],
            db_session
        )
        
        if len(recent_payments) > 5:
            risk_score += 40
            risk_factors.append("high_velocity")
        
        # Check IP velocity
        ip_payments = await self._get_ip_payments(
            customer_ip,
            self.suspicious_patterns["ip_velocity"],
            db_session
        )
        
        if len(ip_payments) > 10:
            risk_score += 25
            risk_factors.append("high_ip_velocity")
        
        # Check for suspicious patterns
        if card_hash:
            card_payments = await self._get_card_payments(
                card_hash,
                timedelta(hours=24),
                db_session
            )
            
            if len(card_payments) > 3:
                risk_score += 20
                risk_factors.append("card_velocity")
        
        # Determine risk level
        if risk_score >= 60:
            risk_level = "high"
        elif risk_score >= 30:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "requires_review": risk_level in ["medium", "high"],
        }
    
    async def _get_recent_payments(self, email: str, time_period: timedelta, db_session):
        """Get recent payments for a customer."""
        # This would query the payment repository
        # For now, return empty list
        return []
    
    async def _get_ip_payments(self, ip: str, time_period: timedelta, db_session):
        """Get recent payments from an IP address."""
        # This would query the payment repository
        return []
    
    async def _get_card_payments(self, card_hash: str, time_period: timedelta, db_session):
        """Get recent payments for a card."""
        # This would query the payment repository
        return []


class TokenManager:
    """Manages secure tokens for payment processing."""
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or secrets.token_urlsafe(32)
    
    def generate_client_token(self, gateway: str, customer_email: str) -> str:
        """Generate secure client token for payment forms."""
        timestamp = str(int(datetime.utcnow().timestamp()))
        payload = f"{gateway}:{customer_email}:{timestamp}"
        
        signature = hmac.new(
            self.secret_key.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{base64.urlsafe_b64encode(payload.encode()).decode()}.{signature}"
    
    def verify_client_token(self, token: str) -> Optional[Dict[str, str]]:
        """Verify and decode client token."""
        try:
            payload, signature = token.rsplit(".", 1)
            decoded_payload = base64.urlsafe_b64decode(payload).decode()
            
            # Verify signature
            expected_signature = hmac.new(
                self.secret_key.encode(),
                decoded_payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(expected_signature, signature):
                return None
            
            # Parse payload
            gateway, email, timestamp = decoded_payload.split(":")
            
            # Check token age (5 minutes)
            token_time = datetime.fromtimestamp(int(timestamp))
            if datetime.utcnow() - token_time > timedelta(minutes=5):
                return None
            
            return {
                "gateway": gateway,
                "email": email,
                "timestamp": timestamp,
            }
            
        except Exception:
            return None


# Utility functions
def generate_secure_reference(length: int = 8) -> str:
    """Generate secure reference number."""
    return secrets.token_urlsafe(length)[:length].upper()


def sanitize_payment_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove sensitive data from payment logs."""
    sensitive_fields = [
        "card_number", "cvv", "expiry", "cvc", "pin",
        "api_key", "secret", "password", "token"
    ]
    
    sanitized = data.copy()
    
    for field in sensitive_fields:
        if field in sanitized:
            sanitized[field] = "***REDACTED***"
    
    return sanitized


def crc32(data: bytes) -> str:
    """Calculate CRC32 checksum."""
    import zlib
    return format(zlib.crc32(data), '08x')
