from backend.models import db, User, AuditLog
from backend.config import Config
import os

def init_db(app):
    """Initialize the database and create default admin user."""
    with app.app_context():
        db.create_all()
        _create_default_admin(app)
        print("Database initialized successfully.")

def _create_default_admin(app):
    """Create default admin user if none exists."""
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin = User(
            name='System Administrator',
            email=app.config['ADMIN_EMAIL'],
            role='admin',
            account_status='active',
            department='Examination Department',
            employee_id='ADMIN001'
        )
        admin.set_password(app.config['ADMIN_PASSWORD'])
        db.session.add(admin)
        
        log = AuditLog(
            action='SYSTEM_INIT',
            description='Default admin account created',
            severity='info'
        )
        db.session.add(log)
        db.session.commit()
        print(f"Default admin created: {app.config['ADMIN_EMAIL']}")
    else:
        print("Admin account already exists.")
