from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='faculty')  # 'admin' or 'faculty'
    wallet_address = db.Column(db.String(42), unique=True, nullable=True)
    department = db.Column(db.String(100), nullable=True)
    employee_id = db.Column(db.String(50), unique=True, nullable=True)
    account_status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'active', 'suspended'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    exam_papers = db.relationship('ExamPaper', backref='uploader', lazy=True, foreign_keys='ExamPaper.uploaded_by')
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'wallet_address': self.wallet_address,
            'department': self.department,
            'employee_id': self.employee_id,
            'account_status': self.account_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        return f'<User {self.email}>'


class ExamPaper(db.Model):
    __tablename__ = 'exam_papers'
    
    id = db.Column(db.Integer, primary_key=True)
    exam_name = db.Column(db.String(200), nullable=False)
    subject_name = db.Column(db.String(200), nullable=False)
    subject_code = db.Column(db.String(50), nullable=False)
    semester = db.Column(db.String(20), nullable=False)
    academic_year = db.Column(db.String(20), nullable=False)
    exam_type = db.Column(db.String(50), nullable=False)  # 'midterm', 'final', 'supplementary'
    exam_date = db.Column(db.Date, nullable=False)
    
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    encrypted_file_path = db.Column(db.String(500), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)
    
    # Blockchain fields
    document_hash = db.Column(db.String(64), nullable=False)  # SHA-256 hex
    blockchain_exam_id = db.Column(db.Integer, nullable=True)  # on-chain ID
    transaction_hash = db.Column(db.String(66), nullable=True)  # 0x + 64 hex chars
    block_number = db.Column(db.Integer, nullable=True)
    
    # Approval
    approval_status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'approved', 'rejected'
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approval_transaction_hash = db.Column(db.String(66), nullable=True)
    approval_timestamp = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_papers')
    
    def to_dict(self):
        return {
            'id': self.id,
            'exam_name': self.exam_name,
            'subject_name': self.subject_name,
            'subject_code': self.subject_code,
            'semester': self.semester,
            'academic_year': self.academic_year,
            'exam_type': self.exam_type,
            'exam_date': self.exam_date.isoformat() if self.exam_date else None,
            'uploaded_by': self.uploaded_by,
            'uploader_name': self.uploader.name if self.uploader else None,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'document_hash': self.document_hash,
            'blockchain_exam_id': self.blockchain_exam_id,
            'transaction_hash': self.transaction_hash,
            'block_number': self.block_number,
            'approval_status': self.approval_status,
            'approved_by': self.approved_by,
            'approver_name': self.approver.name if self.approver else None,
            'approval_transaction_hash': self.approval_transaction_hash,
            'approval_timestamp': self.approval_timestamp.isoformat() if self.approval_timestamp else None,
            'rejection_reason': self.rejection_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<ExamPaper {self.subject_code} - {self.exam_name}>'


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    transaction_hash = db.Column(db.String(66), nullable=True)
    severity = db.Column(db.String(20), default='info')  # 'info', 'warning', 'error', 'critical'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else 'System',
            'action': self.action,
            'description': self.description,
            'ip_address': self.ip_address,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'transaction_hash': self.transaction_hash,
            'severity': self.severity
        }
    
    def __repr__(self):
        return f'<AuditLog {self.action} at {self.timestamp}>'
