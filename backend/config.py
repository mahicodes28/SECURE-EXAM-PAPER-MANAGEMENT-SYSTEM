import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or 'csrf-secret-change-in-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///exam_system.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Upload
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'encrypted_storage'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH') or 16 * 1024 * 1024)
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # Blockchain
    GANACHE_URL = os.environ.get('GANACHE_URL') or 'http://127.0.0.1:7545'
    CONTRACT_ADDRESS = os.environ.get('CONTRACT_ADDRESS') or ''
    ADMIN_WALLET_ADDRESS = os.environ.get('ADMIN_WALLET_ADDRESS') or ''
    ADMIN_PRIVATE_KEY = os.environ.get('ADMIN_PRIVATE_KEY') or ''
    
    # Encryption
    FERNET_KEY = os.environ.get('FERNET_KEY') or ''
    
    # Admin defaults
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@university.edu'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'Admin@2024!'

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
