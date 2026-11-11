import pytest
import io
import hashlib
from backend.app import create_app
from backend.models import db, User, ExamPaper
from backend.services.encryption_service import EncryptionService
from backend.services.integrity_service import IntegrityService

@pytest.fixture
def app_instance():
    app = create_app('development')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        yield app

@pytest.fixture
def client(app_instance):
    return app_instance.test_client()

def test_encryption_decryption():
    service = EncryptionService()
    secret_text = b"University Final Exam - Confidential Question Paper"
    encrypted = service.encrypt(secret_text)
    assert encrypted != secret_text
    
    decrypted = service.decrypt(encrypted)
    assert decrypted == secret_text

def test_integrity_hash():
    data = b"%PDF-1.4 Mock Exam Paper Content"
    expected_hash = hashlib.sha256(data).hexdigest()
    
    res = IntegrityService.verify(expected_hash, file_data=data)
    assert res['verified'] is True
    assert res['result'] == 'VERIFIED'
    
    tampered_data = b"%PDF-1.4 Mock Exam Paper Content - Altered"
    res_tampered = IntegrityService.verify(expected_hash, file_data=tampered_data)
    assert res_tampered['verified'] is False
    assert res_tampered['result'] == 'TAMPERED'

def test_auth_registration_and_login(client, app_instance):
    with app_instance.app_context():
        email = 'turing_test@university.edu'
        # Clean up if exists
        existing = User.query.filter_by(email=email).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
            
        reg_payload = {
            'name': 'Dr. Alan Turing',
            'email': email,
            'password': 'StrongPassword123!',
            'department': 'CS',
            'employee_id': 'CS-TEST-99'
        }
        res = client.post('/api/auth/register', json=reg_payload)
        assert res.status_code == 201
        
        # Pending account cannot log in
        login_res = client.post('/api/auth/login', json={
            'email': email,
            'password': 'StrongPassword123!'
        })
        assert login_res.status_code == 403
        
        # Approve user
        user = User.query.filter_by(email=email).first()
        user.account_status = 'active'
        db.session.commit()
        
        # Active account logs in
        login_res_active = client.post('/api/auth/login', json={
            'email': email,
            'password': 'StrongPassword123!'
        })
        assert login_res_active.status_code == 200
        data = login_res_active.get_json()
        assert data['user']['email'] == email
