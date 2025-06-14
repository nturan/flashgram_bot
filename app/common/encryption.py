"""Encryption utilities for sensitive data like API keys."""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import str, Optional
import logging

logger = logging.getLogger(__name__)


class EncryptionManager:
    """Manages encryption and decryption of sensitive data."""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """Initialize encryption manager.
        
        Args:
            encryption_key: Base encryption key. If None, uses environment variable.
        """
        if encryption_key is None:
            encryption_key = os.getenv("ENCRYPTION_KEY")
            
        if not encryption_key:
            # Generate a key if none provided (for development)
            encryption_key = base64.urlsafe_b64encode(os.urandom(32)).decode()
            logger.warning("No ENCRYPTION_KEY found. Generated temporary key for this session.")
            logger.warning(f"Add to .env: ENCRYPTION_KEY={encryption_key}")
        
        self.encryption_key = encryption_key.encode()
        self._fernet = self._create_fernet()
    
    def _create_fernet(self) -> Fernet:
        """Create Fernet instance with derived key."""
        # Use a fixed salt for deterministic key derivation
        salt = b"flashgram_salt_2024"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.encryption_key))
        return Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string.
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Base64 encoded encrypted string
        """
        try:
            encrypted_bytes = self._fernet.encrypt(plaintext.encode())
            return base64.urlsafe_b64encode(encrypted_bytes).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_text: str) -> str:
        """Decrypt a string.
        
        Args:
            encrypted_text: Base64 encoded encrypted string
            
        Returns:
            Decrypted plaintext string
        """
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_text.encode())
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def encrypt_api_key(self, api_key: str) -> str:
        """Encrypt an API key for storage.
        
        Args:
            api_key: API key to encrypt
            
        Returns:
            Encrypted API key suitable for database storage
        """
        return self.encrypt(api_key)
    
    def decrypt_api_key(self, encrypted_api_key: str) -> str:
        """Decrypt an API key from storage.
        
        Args:
            encrypted_api_key: Encrypted API key from database
            
        Returns:
            Decrypted API key
        """
        return self.decrypt(encrypted_api_key)


# Global encryption manager instance
_encryption_manager = None

def get_encryption_manager() -> EncryptionManager:
    """Get the global encryption manager instance."""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager