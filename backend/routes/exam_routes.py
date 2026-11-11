import os
import sys
import hashlib
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime

# Direct imports from backend package
from backend.models import db, ExamPaper, AuditLog
from backend.utils.helpers import faculty_required, allowed_file, validate_pdf_signature, secure_filename_custom, get_client_ip
from backend.services.encryption_service import EncryptionService
from backend.services.storage_service import StorageService
from backend.services.blockchain_service import BlockchainService

exam_bp = Blueprint('exam', __name__)

@exam_bp.route('/upload', methods=['POST'])
@login_required
@faculty_required
def upload_exam():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files allowed'}), 400
        file_data = file.read()
        if not validate_pdf_signature(file_data):
            return jsonify({'error': 'Invalid PDF file'}), 400
        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
        if len(file_data) > max_size:
            return jsonify({'error': f'File too large. Maximum size is {max_size // (1024*1024)}MB'}), 400
        required_fields = ['exam_name', 'subject_name', 'subject_code', 'semester', 'academic_year', 'exam_type', 'exam_date']
        form = request.form
        for field in required_fields:
            if not form.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        try:
            exam_date = datetime.strptime(form['exam_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid exam date format (use YYYY-MM-DD)'}), 400
            
        sha256_hash = hashlib.sha256(file_data).hexdigest()
        
        enc_service = EncryptionService()
        storage_service = StorageService(current_app.config['UPLOAD_FOLDER'])
        encrypted_data = enc_service.encrypt(file_data)
        secure_name = secure_filename_custom(file.filename)
        enc_filename = secure_name + '.enc'
        file_path = storage_service.save_encrypted(enc_filename, encrypted_data)
        
        bc = BlockchainService()
        blockchain_exam_id = None
        transaction_hash = None
        block_number = None
        if bc.is_connected():
            try:
                tx_result = bc.upload_exam(
                    subject_code=form['subject_code'],
                    document_hash=sha256_hash,
                    file_reference=enc_filename
                )
                blockchain_exam_id = tx_result.get('exam_id')
                transaction_hash = tx_result.get('transactionHash')
                block_number = tx_result.get('blockNumber')
            except Exception as e:
                log_bc = AuditLog(user_id=current_user.id, action='BLOCKCHAIN_UPLOAD_FAILED',
                    description=f'Blockchain registration failed: {str(e)}',
                    ip_address=get_client_ip(request), severity='warning')
                db.session.add(log_bc)
                
        paper = ExamPaper(
            exam_name=form['exam_name'], subject_name=form['subject_name'],
            subject_code=form['subject_code'].upper(), semester=form['semester'],
            academic_year=form['academic_year'], exam_type=form['exam_type'],
            exam_date=exam_date, uploaded_by=current_user.id,
            encrypted_file_path=file_path, original_filename=file.filename,
            file_size=len(file_data), document_hash=sha256_hash,
            blockchain_exam_id=blockchain_exam_id, transaction_hash=transaction_hash,
            block_number=block_number, approval_status='pending'
        )
        db.session.add(paper)
        log = AuditLog(user_id=current_user.id, action='PAPER_UPLOADED',
            description=f'Exam paper uploaded: {form["exam_name"]} ({form["subject_code"]})',
            ip_address=get_client_ip(request), transaction_hash=transaction_hash, severity='info')
        db.session.add(log)
        db.session.commit()
        return jsonify({
            'message': 'Exam paper uploaded successfully', 'paper': paper.to_dict(),
            'document_hash': sha256_hash, 'blockchain_registered': blockchain_exam_id is not None,
            'transaction_hash': transaction_hash, 'block_number': block_number
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@exam_bp.route('/verify', methods=['POST'])
def verify_integrity():
    try:
        provided_hash = None
        exam_id = None
        if request.is_json:
            data = request.get_json()
            provided_hash = data.get('document_hash')
            exam_id = data.get('exam_id')
        elif 'file' in request.files:
            file = request.files['file']
            exam_id = request.form.get('exam_id')
            if file.filename != '':
                file_data = file.read()
                provided_hash = hashlib.sha256(file_data).hexdigest()
        if not provided_hash:
            return jsonify({'error': 'File or document hash required'}), 400
        paper = None
        if exam_id:
            paper = ExamPaper.query.get(int(exam_id))
        if not paper:
            paper = ExamPaper.query.filter_by(document_hash=provided_hash).first()
        if not paper:
            return jsonify({'result': 'NOT_FOUND', 'message': 'No registered examination found for this document', 'provided_hash': provided_hash}), 200
        original_hash = paper.document_hash
        blockchain_hash = None
        bc = BlockchainService()
        if bc.is_connected() and paper.blockchain_exam_id is not None:
            try:
                details = bc.get_exam_details(paper.blockchain_exam_id)
                blockchain_hash = details.get('documentHash')
            except Exception:
                pass
        is_verified = (provided_hash == original_hash)
        return jsonify({
            'result': 'VERIFIED' if is_verified else 'TAMPERED',
            'message': 'Document integrity verified — Original document matches' if is_verified else 'WARNING: Document has been tampered!',
            'provided_hash': provided_hash, 'original_hash': original_hash,
            'blockchain_hash': blockchain_hash, 'paper': paper.to_dict(),
            'verified_at': datetime.utcnow().isoformat(),
            'transaction_hash': paper.transaction_hash, 'block_number': paper.block_number
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@exam_bp.route('/<int:paper_id>', methods=['GET'])
@login_required
def get_exam_details(paper_id):
    paper = ExamPaper.query.get_or_404(paper_id)
    if current_user.role == 'faculty' and paper.uploaded_by != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    return jsonify({'paper': paper.to_dict()}), 200

@exam_bp.route('/list', methods=['GET'])
@login_required
def list_exams():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    if current_user.role == 'admin':
        query = ExamPaper.query
    else:
        query = ExamPaper.query.filter_by(uploaded_by=current_user.id)
    status = request.args.get('status')
    if status:
        query = query.filter_by(approval_status=status)
    pagination = query.order_by(ExamPaper.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({'papers': [p.to_dict() for p in pagination.items], 'total': pagination.total, 'pages': pagination.pages}), 200
