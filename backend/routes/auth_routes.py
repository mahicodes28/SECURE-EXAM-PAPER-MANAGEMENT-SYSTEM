import re
from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from datetime import datetime

from backend.models import db, User, AuditLog
from backend.utils.helpers import get_client_ip

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        required = ['name', 'email', 'password', 'department', 'employee_id']
        for field in required:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        password = data['password']
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 409
        if User.query.filter_by(employee_id=data['employee_id']).first():
            return jsonify({'error': 'Employee ID already registered'}), 409
        user = User(
            name=data['name'],
            email=data['email'],
            role='faculty',
            department=data.get('department'),
            employee_id=data.get('employee_id'),
            wallet_address=data.get('wallet_address'),
            account_status='pending'
        )
        user.set_password(password)
        db.session.add(user)
        log = AuditLog(
            action='FACULTY_REGISTER',
            description=f'New faculty registration: {data["email"]} (pending approval)',
            ip_address=get_client_ip(request),
            severity='info'
        )
        db.session.add(log)
        db.session.commit()
        return jsonify({'message': 'Registration successful. Awaiting admin approval.', 'user_id': user.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            log = AuditLog(
                action='LOGIN_FAILED',
                description=f'Failed login attempt for email: {email}',
                ip_address=get_client_ip(request),
                severity='warning'
            )
            db.session.add(log)
            db.session.commit()
            return jsonify({'error': 'Invalid email or password'}), 401
        if user.account_status == 'pending':
            return jsonify({'error': 'Account pending approval by administrator'}), 403
        if user.account_status == 'suspended':
            return jsonify({'error': 'Account has been suspended. Contact administrator.'}), 403
        login_user(user, remember=data.get('remember', False))
        user.last_login = datetime.utcnow()
        log = AuditLog(
            user_id=user.id,
            action='LOGIN_SUCCESS',
            description=f'User {email} logged in successfully',
            ip_address=get_client_ip(request),
            severity='info'
        )
        db.session.add(log)
        db.session.commit()
        return jsonify({'message': 'Login successful', 'user': user.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    try:
        log = AuditLog(
            user_id=current_user.id,
            action='LOGOUT',
            description=f'User {current_user.email} logged out',
            ip_address=get_client_ip(request),
            severity='info'
        )
        db.session.add(log)
        db.session.commit()
        logout_user()
        return jsonify({'message': 'Logged out successfully'}), 200
    except Exception:
        logout_user()
        return jsonify({'message': 'Logged out'}), 200

@auth_bp.route('/me', methods=['GET'])
@login_required
def me():
    return jsonify({'user': current_user.to_dict()}), 200

@auth_bp.route('/update-wallet', methods=['POST'])
@login_required
def update_wallet():
    try:
        data = request.get_json()
        wallet_address = data.get('wallet_address', '').strip()
        if not wallet_address or not wallet_address.startswith('0x') or len(wallet_address) != 42:
            return jsonify({'error': 'Invalid wallet address'}), 400
        existing = User.query.filter_by(wallet_address=wallet_address).first()
        if existing and existing.id != current_user.id:
            return jsonify({'error': 'Wallet address already registered to another user'}), 409
        current_user.wallet_address = wallet_address
        log = AuditLog(
            user_id=current_user.id,
            action='WALLET_UPDATED',
            description=f'Wallet address updated for {current_user.email}',
            ip_address=get_client_ip(request),
            severity='info'
        )
        db.session.add(log)
        db.session.commit()
        return jsonify({'message': 'Wallet address updated', 'wallet_address': wallet_address}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        if not current_password or not new_password:
            return jsonify({'error': 'Current and new password required'}), 400
        if not current_user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 401
        if len(new_password) < 8:
            return jsonify({'error': 'New password must be at least 8 characters'}), 400
        current_user.set_password(new_password)
        log = AuditLog(
            user_id=current_user.id,
            action='PASSWORD_CHANGED',
            description=f'Password changed for {current_user.email}',
            ip_address=get_client_ip(request),
            severity='info'
        )
        db.session.add(log)
        db.session.commit()
        return jsonify({'message': 'Password changed successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
