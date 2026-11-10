import hashlib
import os
import re
from datetime import datetime
from functools import wraps
from flask import jsonify
from flask_login import current_user

def calculate_sha256(file_path):
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def calculate_sha256_bytes(data: bytes) -> str:
    """Calculate SHA-256 hash of bytes."""
    return hashlib.sha256(data).hexdigest()

def secure_filename_custom(filename):
    """Generate a secure, unique filename."""
    if '.' in filename:
        ext = filename.rsplit('.', 1)[1].lower()
    else:
        ext = ''
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')
    safe_name = re.sub(r'[^\w]', '_', filename.rsplit('.', 1)[0])[:50]
    return f"{timestamp}_{safe_name}.{ext}" if ext else f"{timestamp}_{safe_name}"

def allowed_file(filename, allowed_extensions={'pdf'}):
    """Check if a file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def validate_pdf_signature(file_data: bytes) -> bool:
    """Validate PDF file signature (magic bytes)."""
    return file_data[:4] == b'%PDF'

def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        if current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        if current_user.account_status != 'active':
            return jsonify({'error': 'Account not active'}), 403
        return f(*args, **kwargs)
    return decorated_function

def faculty_required(f):
    """Decorator to require faculty role (or admin)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        if current_user.role not in ['faculty', 'admin']:
            return jsonify({'error': 'Faculty access required'}), 403
        if current_user.account_status != 'active':
            return jsonify({'error': 'Account not active'}), 403
        return f(*args, **kwargs)
    return decorated_function

def login_required_api(f):
    """Decorator to require login for API endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def format_file_size(size_bytes):
    """Format file size in human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

def get_client_ip(request):
    """Get client IP address from request."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers['X-Forwarded-For'].split(',')[0].strip()
    return request.remote_addr
