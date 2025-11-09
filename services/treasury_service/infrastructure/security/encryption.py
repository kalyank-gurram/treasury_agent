"""Data encryption and key management services."""

import os
import base64
import hashlib
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from typing import Dict, Optional, Union, Tuple, List
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum
from ..observability import get_observability_manager


class EncryptionAlgorithm(Enum):
    """Supported encryption algorithms."""
    AES_256_GCM = "AES-256-GCM"
    FERNET = "Fernet"
    RSA_2048 = "RSA-2048"
    RSA_4096 = "RSA-4096"


class KeyType(Enum):
    """Types of encryption keys."""
    SYMMETRIC = "symmetric"
    ASYMMETRIC_PUBLIC = "asymmetric_public"
    ASYMMETRIC_PRIVATE = "asymmetric_private"


@dataclass
class EncryptionKey:
    """Represents an encryption key."""
    key_id: str
    key_type: KeyType
    algorithm: EncryptionAlgorithm
    key_data: bytes
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    metadata: Dict[str, str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class EncryptedData:
    """Represents encrypted data with metadata."""
    ciphertext: bytes
    algorithm: EncryptionAlgorithm
    key_id: str
    iv: Optional[bytes] = None  # Initialization Vector for some algorithms
    auth_tag: Optional[bytes] = None  # Authentication tag for AEAD algorithms
    metadata: Dict[str, str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
            
    def to_base64(self) -> str:
        """Convert encrypted data to base64 string for storage."""
        data = {
            'ciphertext': base64.b64encode(self.ciphertext).decode('utf-8'),
            'algorithm': self.algorithm.value,
            'key_id': self.key_id,
        }
        
        if self.iv:
            data['iv'] = base64.b64encode(self.iv).decode('utf-8')
        if self.auth_tag:
            data['auth_tag'] = base64.b64encode(self.auth_tag).decode('utf-8')
        if self.metadata:
            data['metadata'] = self.metadata
            
        return base64.b64encode(str(data).encode('utf-8')).decode('utf-8')
        
    @classmethod
    def from_base64(cls, data_str: str) -> 'EncryptedData':
        """Create EncryptedData from base64 string."""
        # This is a simplified implementation
        # In production, use proper JSON serialization
        import ast
        
        decoded = base64.b64decode(data_str.encode('utf-8')).decode('utf-8')
        data = ast.literal_eval(decoded)
        
        return cls(
            ciphertext=base64.b64decode(data['ciphertext'].encode('utf-8')),
            algorithm=EncryptionAlgorithm(data['algorithm']),
            key_id=data['key_id'],
            iv=base64.b64decode(data['iv'].encode('utf-8')) if data.get('iv') else None,
            auth_tag=base64.b64decode(data['auth_tag'].encode('utf-8')) if data.get('auth_tag') else None,
            metadata=data.get('metadata', {})
        )


class KeyManagementService:
    """Manages encryption keys with rotation and lifecycle."""
    
    def __init__(self):
        self.observability = get_observability_manager()
        self.logger = self.observability.get_logger("security.key_management")
        
        # Key storage (in production, use HSM or cloud KMS)
        self.keys: Dict[str, EncryptionKey] = {}
        
        # Key rotation configuration
        self.key_rotation_interval = timedelta(days=90)  # 3 months
        
        # Initialize master keys
        self._initialize_master_keys()
        
    def _initialize_master_keys(self):
        """Initialize master encryption keys."""
        # Create master symmetric key
        master_key = self.generate_symmetric_key(
            algorithm=EncryptionAlgorithm.FERNET,
            key_id="master_symmetric_001"
        )
        
        # Create master asymmetric key pair
        public_key, private_key = self.generate_asymmetric_key_pair(
            algorithm=EncryptionAlgorithm.RSA_2048,
            key_id_prefix="master_rsa_001"
        )
        
        self.logger.info("Master encryption keys initialized")
        
    def generate_key_id(self, prefix: str = "key") -> str:
        """Generate a unique key ID."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        random_suffix = secrets.token_hex(4)
        return f"{prefix}_{timestamp}_{random_suffix}"
        
    def generate_symmetric_key(self, algorithm: EncryptionAlgorithm, 
                             key_id: str = None) -> EncryptionKey:
        """Generate a new symmetric encryption key."""
        if not key_id:
            key_id = self.generate_key_id("sym")
            
        if algorithm == EncryptionAlgorithm.FERNET:
            key_data = Fernet.generate_key()
        elif algorithm == EncryptionAlgorithm.AES_256_GCM:
            key_data = os.urandom(32)  # 256-bit key
        else:
            raise ValueError(f"Unsupported symmetric algorithm: {algorithm}")
            
        key = EncryptionKey(
            key_id=key_id,
            key_type=KeyType.SYMMETRIC,
            algorithm=algorithm,
            key_data=key_data,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + self.key_rotation_interval
        )
        
        self.keys[key_id] = key
        
        self.logger.info(f"Generated symmetric key", key_id=key_id, algorithm=algorithm.value)
        
        return key
        
    def generate_asymmetric_key_pair(self, algorithm: EncryptionAlgorithm,
                                   key_id_prefix: str = None) -> Tuple[EncryptionKey, EncryptionKey]:
        """Generate an asymmetric key pair."""
        if not key_id_prefix:
            key_id_prefix = self.generate_key_id("asym")
            
        if algorithm == EncryptionAlgorithm.RSA_2048:
            key_size = 2048
        elif algorithm == EncryptionAlgorithm.RSA_4096:
            key_size = 4096
        else:
            raise ValueError(f"Unsupported asymmetric algorithm: {algorithm}")
            
        # Generate RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size
        )
        public_key = private_key.public_key()
        
        # Serialize keys
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        now = datetime.now(timezone.utc)
        expires_at = now + self.key_rotation_interval
        
        # Create key objects
        public_key_obj = EncryptionKey(
            key_id=f"{key_id_prefix}_public",
            key_type=KeyType.ASYMMETRIC_PUBLIC,
            algorithm=algorithm,
            key_data=public_pem,
            created_at=now,
            expires_at=expires_at
        )
        
        private_key_obj = EncryptionKey(
            key_id=f"{key_id_prefix}_private",
            key_type=KeyType.ASYMMETRIC_PRIVATE,
            algorithm=algorithm,
            key_data=private_pem,
            created_at=now,
            expires_at=expires_at
        )
        
        # Store keys
        self.keys[public_key_obj.key_id] = public_key_obj
        self.keys[private_key_obj.key_id] = private_key_obj
        
        self.logger.info(f"Generated asymmetric key pair", 
                        public_key_id=public_key_obj.key_id,
                        private_key_id=private_key_obj.key_id,
                        algorithm=algorithm.value)
        
        return public_key_obj, private_key_obj
        
    def get_key(self, key_id: str) -> Optional[EncryptionKey]:
        """Retrieve a key by ID."""
        key = self.keys.get(key_id)
        
        if key and key.expires_at and key.expires_at < datetime.now(timezone.utc):
            self.logger.warning(f"Requested expired key", key_id=key_id)
            return None
            
        return key
        
    def rotate_key(self, old_key_id: str) -> Optional[EncryptionKey]:
        """Rotate an encryption key."""
        old_key = self.get_key(old_key_id)
        if not old_key:
            return None
            
        # Generate new key with same algorithm
        if old_key.key_type == KeyType.SYMMETRIC:
            new_key = self.generate_symmetric_key(old_key.algorithm)
        else:
            # For asymmetric keys, generate new pair
            public_key, private_key = self.generate_asymmetric_key_pair(old_key.algorithm)
            new_key = private_key if old_key.key_type == KeyType.ASYMMETRIC_PRIVATE else public_key
            
        # Mark old key as inactive
        old_key.is_active = False
        
        self.logger.info(f"Key rotated", old_key_id=old_key_id, new_key_id=new_key.key_id)
        
        return new_key
        
    def list_keys(self, key_type: KeyType = None, active_only: bool = True) -> List[EncryptionKey]:
        """List keys with optional filtering."""
        keys = []
        for key in self.keys.values():
            if key_type and key.key_type != key_type:
                continue
            if active_only and not key.is_active:
                continue
            if key.expires_at and key.expires_at < datetime.now(timezone.utc):
                continue
            keys.append(key)
            
        return keys


class EncryptionService:
    """Main encryption service for the treasury system."""
    
    def __init__(self, key_manager: KeyManagementService = None):
        self.key_manager = key_manager or KeyManagementService()
        self.observability = get_observability_manager()
        self.logger = self.observability.get_logger("security.encryption")
        
        # Default encryption algorithms for different data types
        self.default_algorithms = {
            'pii': EncryptionAlgorithm.AES_256_GCM,
            'financial': EncryptionAlgorithm.FERNET,
            'general': EncryptionAlgorithm.FERNET
        }
        
    def encrypt_data(self, plaintext: Union[str, bytes], key_id: str = None, 
                    data_type: str = 'general') -> EncryptedData:
        """Encrypt data using specified or default key."""
        
        # Convert string to bytes if necessary
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
            
        # Get or generate key
        if key_id:
            key = self.key_manager.get_key(key_id)
            if not key:
                raise ValueError(f"Key not found: {key_id}")
        else:
            # Use default algorithm for data type
            algorithm = self.default_algorithms.get(data_type, EncryptionAlgorithm.FERNET)
            key = self._get_default_key(algorithm)
            
        # Encrypt based on algorithm
        if key.algorithm == EncryptionAlgorithm.FERNET:
            return self._encrypt_fernet(plaintext, key)
        elif key.algorithm == EncryptionAlgorithm.AES_256_GCM:
            return self._encrypt_aes_gcm(plaintext, key)
        elif key.algorithm in [EncryptionAlgorithm.RSA_2048, EncryptionAlgorithm.RSA_4096]:
            return self._encrypt_rsa(plaintext, key)
        else:
            raise ValueError(f"Unsupported encryption algorithm: {key.algorithm}")
            
    def decrypt_data(self, encrypted_data: EncryptedData) -> bytes:
        """Decrypt data using the associated key."""
        
        # Get decryption key
        key = self.key_manager.get_key(encrypted_data.key_id)
        if not key:
            raise ValueError(f"Decryption key not found: {encrypted_data.key_id}")
            
        # Decrypt based on algorithm
        if encrypted_data.algorithm == EncryptionAlgorithm.FERNET:
            return self._decrypt_fernet(encrypted_data, key)
        elif encrypted_data.algorithm == EncryptionAlgorithm.AES_256_GCM:
            return self._decrypt_aes_gcm(encrypted_data, key)
        elif encrypted_data.algorithm in [EncryptionAlgorithm.RSA_2048, EncryptionAlgorithm.RSA_4096]:
            return self._decrypt_rsa(encrypted_data, key)
        else:
            raise ValueError(f"Unsupported decryption algorithm: {encrypted_data.algorithm}")
            
    def _get_default_key(self, algorithm: EncryptionAlgorithm) -> EncryptionKey:
        """Get or create default key for algorithm."""
        # Look for existing master key
        for key in self.key_manager.keys.values():
            if key.algorithm == algorithm and key.is_active and "master" in key.key_id:
                return key
                
        # Generate new key if none found
        return self.key_manager.generate_symmetric_key(algorithm)
        
    def _encrypt_fernet(self, plaintext: bytes, key: EncryptionKey) -> EncryptedData:
        """Encrypt using Fernet algorithm."""
        fernet = Fernet(key.key_data)
        ciphertext = fernet.encrypt(plaintext)
        
        return EncryptedData(
            ciphertext=ciphertext,
            algorithm=EncryptionAlgorithm.FERNET,
            key_id=key.key_id
        )
        
    def _decrypt_fernet(self, encrypted_data: EncryptedData, key: EncryptionKey) -> bytes:
        """Decrypt using Fernet algorithm."""
        fernet = Fernet(key.key_data)
        return fernet.decrypt(encrypted_data.ciphertext)
        
    def _encrypt_aes_gcm(self, plaintext: bytes, key: EncryptionKey) -> EncryptedData:
        """Encrypt using AES-256-GCM algorithm."""
        # Generate random IV
        iv = os.urandom(12)  # 96-bit IV for GCM
        
        # Create cipher
        cipher = Cipher(algorithms.AES(key.key_data), modes.GCM(iv))
        encryptor = cipher.encryptor()
        
        # Encrypt data
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        
        return EncryptedData(
            ciphertext=ciphertext,
            algorithm=EncryptionAlgorithm.AES_256_GCM,
            key_id=key.key_id,
            iv=iv,
            auth_tag=encryptor.tag
        )
        
    def _decrypt_aes_gcm(self, encrypted_data: EncryptedData, key: EncryptionKey) -> bytes:
        """Decrypt using AES-256-GCM algorithm."""
        # Create cipher
        cipher = Cipher(
            algorithms.AES(key.key_data), 
            modes.GCM(encrypted_data.iv, encrypted_data.auth_tag)
        )
        decryptor = cipher.decryptor()
        
        # Decrypt data
        return decryptor.update(encrypted_data.ciphertext) + decryptor.finalize()
        
    def _encrypt_rsa(self, plaintext: bytes, key: EncryptionKey) -> EncryptedData:
        """Encrypt using RSA algorithm."""
        # Load public key
        public_key = serialization.load_pem_public_key(key.key_data)
        
        # RSA has size limitations, so we'll encrypt in chunks if necessary
        max_chunk_size = (public_key.key_size // 8) - 42  # OAEP padding overhead
        
        if len(plaintext) > max_chunk_size:
            # For large data, use hybrid encryption (RSA + AES)
            # Generate AES key
            aes_key = os.urandom(32)
            
            # Encrypt data with AES
            iv = os.urandom(12)
            cipher = Cipher(algorithms.AES(aes_key), modes.GCM(iv))
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(plaintext) + encryptor.finalize()
            
            # Encrypt AES key with RSA
            encrypted_key = public_key.encrypt(
                aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            # Combine encrypted key + IV + auth_tag + ciphertext
            combined_ciphertext = encrypted_key + iv + encryptor.tag + ciphertext
            
            return EncryptedData(
                ciphertext=combined_ciphertext,
                algorithm=key.algorithm,
                key_id=key.key_id,
                metadata={'hybrid': 'true'}
            )
        else:
            # Direct RSA encryption for small data
            ciphertext = public_key.encrypt(
                plaintext,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            return EncryptedData(
                ciphertext=ciphertext,
                algorithm=key.algorithm,
                key_id=key.key_id
            )
            
    def _decrypt_rsa(self, encrypted_data: EncryptedData, key: EncryptionKey) -> bytes:
        """Decrypt using RSA algorithm."""
        # Load private key
        private_key = serialization.load_pem_private_key(key.key_data, password=None)
        
        if encrypted_data.metadata.get('hybrid') == 'true':
            # Hybrid decryption
            ciphertext = encrypted_data.ciphertext
            
            # Extract components
            key_size = private_key.key_size // 8
            encrypted_aes_key = ciphertext[:key_size]
            iv = ciphertext[key_size:key_size + 12]
            auth_tag = ciphertext[key_size + 12:key_size + 28]
            data_ciphertext = ciphertext[key_size + 28:]
            
            # Decrypt AES key
            aes_key = private_key.decrypt(
                encrypted_aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            # Decrypt data
            cipher = Cipher(algorithms.AES(aes_key), modes.GCM(iv, auth_tag))
            decryptor = cipher.decryptor()
            return decryptor.update(data_ciphertext) + decryptor.finalize()
        else:
            # Direct RSA decryption
            return private_key.decrypt(
                encrypted_data.ciphertext,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
    def encrypt_field(self, value: str, field_name: str) -> str:
        """Encrypt a specific field value and return base64 encoded result."""
        # Determine data type based on field name
        data_type = 'general'
        if any(pii_field in field_name.lower() for pii_field in ['ssn', 'tax_id', 'account_number']):
            data_type = 'pii'
        elif any(fin_field in field_name.lower() for fin_field in ['amount', 'balance', 'salary']):
            data_type = 'financial'
            
        encrypted_data = self.encrypt_data(value, data_type=data_type)
        return encrypted_data.to_base64()
        
    def decrypt_field(self, encrypted_value: str) -> str:
        """Decrypt a field value from base64 encoded encrypted data."""
        encrypted_data = EncryptedData.from_base64(encrypted_value)
        decrypted_bytes = self.decrypt_data(encrypted_data)
        return decrypted_bytes.decode('utf-8')
        
    def hash_data(self, data: Union[str, bytes], salt: bytes = None) -> Tuple[bytes, bytes]:
        """Hash data with salt for password storage or data integrity."""
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        if salt is None:
            salt = os.urandom(32)
            
        # Use PBKDF2 for password-like data
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        hash_value = kdf.derive(data)
        
        return hash_value, salt
        
    def verify_hash(self, data: Union[str, bytes], hash_value: bytes, salt: bytes) -> bool:
        """Verify data against its hash."""
        computed_hash, _ = self.hash_data(data, salt)
        return computed_hash == hash_value