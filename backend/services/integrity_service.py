import hashlib
import os

class IntegrityService:
    """Handles document integrity verification using SHA-256."""
    
    @staticmethod
    def hash_file(file_path: str) -> str:
        """Calculate SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    @staticmethod
    def hash_bytes(data: bytes) -> str:
        """Calculate SHA-256 hash of raw bytes."""
        return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def verify(original_hash: str, file_path: str = None, file_data: bytes = None) -> dict:
        """
        Verify file integrity against original hash.
        Returns dict with match status and details.
        """
        if file_path:
            if not os.path.exists(file_path):
                return {'verified': False, 'error': 'File not found', 'result': 'NOT_FOUND'}
            computed_hash = IntegrityService.hash_file(file_path)
        elif file_data is not None:
            computed_hash = IntegrityService.hash_bytes(file_data)
        else:
            return {'verified': False, 'error': 'No file or data provided', 'result': 'ERROR'}
        
        matches = (computed_hash.lower() == original_hash.lower())
        return {
            'verified': matches,
            'result': 'VERIFIED' if matches else 'TAMPERED',
            'computed_hash': computed_hash,
            'original_hash': original_hash,
            'message': 'Document integrity verified — Hashes match' if matches else 'INTEGRITY VIOLATION — Document has been modified!'
        }

