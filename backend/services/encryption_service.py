import os
import base64
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

class EncryptionService:
    """Handles Fernet symmetric encryption for exam papers."""
    
    def __init__(self):
        key = os.environ.get('FERNET_KEY')
        if not key or key == 'your-fernet-key-here-generate-with-cryptography-library':
            key = Fernet.generate_key().decode()
            print(f"[EncryptionService] Warning: Using dynamically generated FERNET_KEY: {key}")
        
        if isinstance(key, str):
            key = key.encode('utf-8')
        
        try:
            self.fernet = Fernet(key)
        except Exception as e:
            # Fallback to freshly generated key to avoid crash
            temp_key = Fernet.generate_key()
            self.fernet = Fernet(temp_key)
            print(f"[EncryptionService] Invalid FERNET_KEY format ({e}), initialized fallback key.")
    
    def encrypt(self, data: bytes) -> bytes:
        """Encrypt binary data."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return self.fernet.encrypt(data)
    
    def decrypt(self, encrypted_data: bytes) -> bytes:
        """Decrypt encrypted binary data."""
        if isinstance(encrypted_data, str):
            encrypted_data = encrypted_data.encode('utf-8')
        return self.fernet.decrypt(encrypted_data)
    
    def encrypt_file(self, file_path: str, output_path: str = None) -> str:
        """Encrypt a file and save to output_path."""
        with open(file_path, 'rb') as f:
            data = f.read()
        
        encrypted = self.encrypt(data)
        if not output_path:
            output_path = file_path + '.enc'
        
        with open(output_path, 'wb') as f:
            f.write(encrypted)
        
        return output_path
    
    def decrypt_file(self, encrypted_path: str, output_path: str = None) -> bytes:
        """Decrypt a file and return bytes (or save to output_path)."""
        with open(encrypted_path, 'rb') as f:
            encrypted_data = f.read()
        
        decrypted = self.decrypt(encrypted_data)
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(decrypted)
        
        return decrypted
    
    @staticmethod
    def generate_key() -> str:
        """Generate a new Fernet key."""
        return Fernet.generate_key().decode()

