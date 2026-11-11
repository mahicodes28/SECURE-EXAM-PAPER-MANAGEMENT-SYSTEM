import os
import re

class StorageService:
    """Handles encrypted file storage operations."""
    
    def __init__(self, storage_path: str):
        self.storage_path = os.path.abspath(storage_path)
        os.makedirs(self.storage_path, exist_ok=True)
    
    def save_encrypted(self, filename: str, data: bytes) -> str:
        """Save encrypted data to storage. Returns full path."""
        safe_name = re.sub(r'[^\w\.\-]', '_', filename)
        full_path = os.path.join(self.storage_path, safe_name)
        
        with open(full_path, 'wb') as f:
            f.write(data)
        
        return full_path
    
    def read_encrypted(self, file_path: str) -> bytes:
        """Read encrypted file data safely."""
        abs_path = os.path.abspath(file_path)
        if not abs_path.startswith(self.storage_path):
            raise PermissionError("Path traversal attempt detected")
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Encrypted file not found: {abs_path}")
        
        with open(abs_path, 'rb') as f:
            return f.read()
    
    def delete_file(self, file_path: str) -> bool:
        """Delete an encrypted file."""
        try:
            abs_path = os.path.abspath(file_path)
            if not abs_path.startswith(self.storage_path):
                raise PermissionError("Path traversal attempt detected")
            if os.path.exists(abs_path):
                os.remove(abs_path)
                return True
        except Exception:
            pass
        return False
    
    def file_exists(self, file_path: str) -> bool:
        return os.path.exists(file_path)
    
    def get_file_size(self, file_path: str) -> int:
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
        return 0
    
    def list_files(self) -> list:
        try:
            return os.listdir(self.storage_path)
        except Exception:
            return []

