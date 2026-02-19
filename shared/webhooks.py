"""
Webhook Verification Module

Handles cryptographic signature verification for incoming webhooks from payment
providers (Hubtel, Paystack). Ensures webhook authenticity and integrity.
"""

import hmac
import hashlib
import json
import logging
from typing import Optional, Tuple
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status

logger = logging.getLogger(__name__)

# ==================== Webhook Signature Verification ====================

class WebhookVerifier:
    """Verifies webhook signatures using HMAC-SHA256 or other algorithms."""
    
    ALGORITHMS = {
        'sha256': hashlib.sha256,
        'sha512': hashlib.sha512,
        'sha1': hashlib.sha1,
        'md5': hashlib.md5,
    }
    
    def __init__(self, secret: str, algorithm: str = 'sha256'):
        """
        Initialize webhook verifier.
        
        Args:
            secret: Shared secret key from payment provider
            algorithm: HMAC algorithm (sha256, sha512, sha1, md5)
        """
        self.secret = secret
        self.algorithm = algorithm
        if algorithm not in self.ALGORITHMS:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    def compute_signature(self, payload: bytes) -> str:
        """
        Compute HMAC signature for payload.
        
        Args:
            payload: Raw request body as bytes
            
        Returns:
            Hex-encoded signature
        """
        hash_func = self.ALGORITHMS[self.algorithm]
        signature = hmac.new(
            self.secret.encode(),
            payload,
            hash_func
        ).hexdigest()
        return signature
    
    def verify(
        self,
        payload: bytes,
        signature: str,
        signature_format: str = 'hex'
    ) -> bool:
        """
        Verify webhook signature.
        
        Args:
            payload: Raw request body as bytes
            signature: Signature from webhook header (may include prefix like 'sha256=')
            signature_format: 'hex' for hex-encoded, 'base64' for base64-encoded
            
        Returns:
            True if signature is valid, False otherwise
        """
        # Extract signature value (remove prefix like 'sha256=')
        sig_value = signature.split('=', 1)[-1] if '=' in signature else signature
        
        # Compute expected signature
        expected = self.compute_signature(payload)
        
        # Compare using constant-time comparison (prevent timing attacks)
        return hmac.compare_digest(expected, sig_value)


# ==================== Webhook Request Handlers ====================

async def verify_hubtel_webhook(
    request: Request,
    secret: str
) -> Tuple[dict, bool]:
    """
    Verify Hubtel payment webhook.
    
    Args:
        request: FastAPI request object
        secret: HUBTEL_WEBHOOK_SECRET from environment
        
    Returns:
        Tuple of (parsed_body, is_valid)
        
    Raises:
        HTTPException: If signature verification fails
    """
    # Get raw body for signature verification
    raw_body = await request.body()
    
    # Get signature from header (Hubtel uses X-Hubtel-Signature)
    signature = request.headers.get('X-Hubtel-Signature', '')
    
    if not signature:
        logger.warning("Missing X-Hubtel-Signature header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing signature header"
        )
    
    # Verify signature
    verifier = WebhookVerifier(secret, algorithm='sha256')
    if not verifier.verify(raw_body, signature):
        logger.error("Hubtel webhook signature verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )
    
    # Parse body
    try:
        body = json.loads(raw_body.decode() if isinstance(raw_body, bytes) else raw_body)
    except json.JSONDecodeError:
        logger.error("Failed to parse Hubtel webhook JSON")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    
    return body, True


# ==================== Generic Webhook Verification ====================

def verify_generic_signature(
    payload: bytes,
    signature: str,
    secret: str,
    algorithm: str = 'sha256',
    signature_prefix: bool = True
) -> bool:
    """
    Generic webhook signature verification.
    
    Args:
        payload: Raw request body
        signature: Signature from header
        secret: Shared secret
        algorithm: HMAC algorithm (sha256, sha512, etc)
        signature_prefix: Whether signature has prefix like 'sha256='
        
    Returns:
        True if valid, False otherwise
    """
    verifier = WebhookVerifier(secret, algorithm)
    return verifier.verify(payload, signature)


def extract_signature_from_header(
    header_value: str,
    format: str = 'hex'
) -> str:
    """
    Extract signature value from header.
    
    Handles formats like:
    - 'sha256=abcd1234' → 'abcd1234'
    - 'abcd1234' → 'abcd1234'
    - 't=123,v1=abcd1234' → 'abcd1234'
    
    Args:
        header_value: Raw header value
        format: Expected format
        
    Returns:
        Extracted signature
    """
    if '=' not in header_value:
        return header_value
    
    if ',' in header_value:  # Stripe-like format: t=...,v1=...
        parts = {}
        for part in header_value.split(','):
            key, value = part.split('=', 1)
            parts[key] = value
        return parts.get('v1', '')
    
    # Simple format: algo=signature
    return header_value.split('=', 1)[-1]


# ==================== Webhook Event Types ====================

class WebhookEvent:
    """Represents a verified webhook event."""
    
    def __init__(self, provider: str, event_type: str, body: dict):
        self.provider = provider  # 'hubtel', 'stripe', 'paypal'
        self.event_type = event_type
        self.body = body
        self.timestamp = datetime.utcnow()
    
    def is_payment_event(self) -> bool:
        """Check if this is a payment-related event."""
        payment_events = [
            'payment.completed', 'payment.success', 'charge.succeeded',
            'PAYMENT_COMPLETED', 'COMPLETED'
        ]
        return self.event_type in payment_events
    
    def is_payout_event(self) -> bool:
        """Check if this is a payout-related event."""
        payout_events = [
            'payout.completed', 'payout.success', 'transfer.succeeded',
            'PAYOUT_COMPLETED'
        ]
        return self.event_type in payout_events
    
    def extract_payment_id(self) -> Optional[str]:
        """Extract payment ID from event."""
        # Try common field names
        return (
            self.body.get('payment_id') or
            self.body.get('id') or
            (self.body.get('metadata') or {}).get('payment_id') or
            self.body.get('transaction_id')
        )
    
    def extract_amount(self) -> Optional[float]:
        """Extract amount from event."""
        return (
            self.body.get('amount') or
            self.body.get('amount_received') or
            (self.body.get('metadata') or {}).get('amount')
        )


# ==================== Logging & Audit ====================

class WebhookAuditLog:
    """Audit trail for webhook events."""
    
    def __init__(self):
        self.entries = []
    
    def log(
        self,
        provider: str,
        event_type: str,
        status: str,
        details: dict = None,
        error: str = None
    ):
        """
        Log webhook event.
        
        Args:
            provider: Payment provider name
            event_type: Type of event
            status: 'success', 'failed', 'rejected'
            details: Additional details
            error: Error message if failed
        """
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'provider': provider,
            'event_type': event_type,
            'status': status,
            'details': details or {},
            'error': error
        }
        self.entries.append(entry)
        
        # Keep only last 1000 entries
        if len(self.entries) > 1000:
            self.entries.pop(0)
        
        log_level = logging.ERROR if status == 'failed' else logging.INFO
        logger.log(
            log_level,
            f"Webhook {status}: {provider}/{event_type}",
            extra={'details': entry}
        )
    
    def get_log(self, limit: int = 100) -> list:
        """Get recent audit log entries."""
        return self.entries[-limit:]
    
    def get_by_provider(self, provider: str, limit: int = 50) -> list:
        """Get entries for a specific provider."""
        return [e for e in self.entries if e['provider'] == provider][-limit:]


# Global audit log instance
webhook_audit = WebhookAuditLog()
