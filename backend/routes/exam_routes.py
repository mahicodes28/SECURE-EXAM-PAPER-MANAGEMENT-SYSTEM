
import hashlib
from datetime import datetime

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from backend.models import db, ExamPaper, AuditLog
from backend.utils.helpers import (
    faculty_required,
    allowed_file,
    validate_pdf_signature,
    secure_filename_custom,
    get_client_ip
)
from backend.services.encryption_service import EncryptionService
from backend.services.storage_service import StorageService
from backend.services.blockchain_service import BlockchainService


exam_bp = Blueprint('exam', __name__)


def create_audit_log(
    user_id,
    action,
    description,
    ip_address=None,
    transaction_hash=None,
    severity='info'
):
    """Create an audit log without keyword-based model initialization."""

    log = AuditLog()
    log.user_id = user_id
    log.action = action
    log.description = description
    log.ip_address = ip_address
    log.transaction_hash = transaction_hash
    log.severity = severity

    return log


def normalize_hash(value):
    """Normalize blockchain and SHA-256 hashes for comparison."""

    if value is None:
        return None

    if isinstance(value, bytes):
        value = value.hex()

    value = str(value).strip().lower()

    if value.startswith('0x'):
        value = value[2:]

    return value


@exam_bp.route('/upload', methods=['POST'])
@login_required
@faculty_required
def upload_exam():

    try:
        # 1. Validate uploaded file
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files are allowed'}), 400

        file_data = file.read()

        if not validate_pdf_signature(file_data):
            return jsonify({'error': 'Invalid PDF file'}), 400

        max_size = current_app.config.get(
            'MAX_CONTENT_LENGTH',
            16 * 1024 * 1024
        )

        if len(file_data) > max_size:
            return jsonify({
                'error': f'File too large. Maximum size is {max_size // (1024 * 1024)}MB'
            }), 400

        # 2. Validate examination metadata
        required_fields = [
            'exam_name',
            'subject_name',
            'subject_code',
            'semester',
            'academic_year',
            'exam_type',
            'exam_date'
        ]

        form = request.form

        for field in required_fields:
            if not form.get(field):
                return jsonify({
                    'error': f'{field} is required'
                }), 400

        try:
            exam_date = datetime.strptime(
                form['exam_date'],
                '%Y-%m-%d'
            ).date()
        except ValueError:
            return jsonify({
                'error': 'Invalid exam date format. Use YYYY-MM-DD'
            }), 400

        # 3. Generate SHA-256 hash
        sha256_hash = hashlib.sha256(file_data).hexdigest()

        # 4. Encrypt examination paper
        enc_service = EncryptionService()
        encrypted_data = enc_service.encrypt(file_data)

        # 5. Store encrypted document
        storage_service = StorageService(
            current_app.config['UPLOAD_FOLDER']
        )

        secure_name = secure_filename_custom(file.filename)
        enc_filename = secure_name + '.enc'

        file_path = storage_service.save_encrypted(
            enc_filename,
            encrypted_data
        )

        # 6. Blockchain registration
        bc = BlockchainService()

        blockchain_exam_id = None
        transaction_hash = None
        block_number = None
        blockchain_registered = False

        if bc.is_connected():

            try:
                tx_result = bc.upload_exam(
                    subject_code=form['subject_code'].upper(),
                    document_hash=sha256_hash,
                    file_reference=enc_filename
                )

                blockchain_exam_id = tx_result.get('exam_id')
                transaction_hash = tx_result.get('transactionHash')
                block_number = tx_result.get('blockNumber')

                blockchain_registered = (
                    blockchain_exam_id is not None
                    and transaction_hash is not None
                )

                if not blockchain_registered:
                    raise Exception(
                        'Blockchain transaction did not return valid registration details'
                    )

            except Exception as e:

                log_bc = create_audit_log(
                    user_id=current_user.id,
                    action='BLOCKCHAIN_UPLOAD_FAILED',
                    description=f'Blockchain registration failed: {str(e)}',
                    ip_address=get_client_ip(request),
                    severity='warning'
                )

                db.session.add(log_bc)

        # 7. Create examination record
        # Assign fields individually to avoid Pyrefly
        # unexpected-keyword constructor diagnostics.

        paper = ExamPaper()

        paper.exam_name = form['exam_name']
        paper.subject_name = form['subject_name']
        paper.subject_code = form['subject_code'].upper()
        paper.semester = form['semester']
        paper.academic_year = form['academic_year']
        paper.exam_type = form['exam_type']
        paper.exam_date = exam_date
        paper.uploaded_by = current_user.id
        paper.encrypted_file_path = file_path
        paper.original_filename = file.filename
        paper.file_size = len(file_data)
        paper.document_hash = sha256_hash
        paper.blockchain_exam_id = blockchain_exam_id
        paper.transaction_hash = transaction_hash
        paper.block_number = block_number
        paper.approval_status = 'pending'

        db.session.add(paper)

        # 8. Create audit log
        log = create_audit_log(
            user_id=current_user.id,
            action='PAPER_UPLOADED',
            description=(
                f'Exam paper uploaded: {form["exam_name"]} '
                f'({form["subject_code"]})'
            ),
            ip_address=get_client_ip(request),
            transaction_hash=transaction_hash,
            severity='info'
        )

        db.session.add(log)

        db.session.commit()

        return jsonify({
            'message': 'Exam paper uploaded successfully',
            'paper': paper.to_dict(),
            'document_hash': sha256_hash,
            'blockchain_registered': blockchain_registered,
            'transaction_hash': transaction_hash,
            'block_number': block_number
        }), 201

    except Exception as e:

        db.session.rollback()

        current_app.logger.exception(
            'Exam paper upload failed'
        )

        return jsonify({
            'error': 'Exam paper upload failed',
            'details': str(e)
        }), 500


@exam_bp.route('/verify', methods=['POST'])
def verify_integrity():

    try:
        provided_hash = None
        exam_id = None

        # 1. Get document hash or uploaded PDF
        if request.is_json:

            data = request.get_json(silent=True) or {}

            provided_hash = data.get('document_hash')
            exam_id = data.get('exam_id')

        elif 'file' in request.files:

            file = request.files['file']
            exam_id = request.form.get('exam_id')

            if file.filename != '':
                file_data = file.read()

                if not validate_pdf_signature(file_data):
                    return jsonify({
                        'error': 'Invalid PDF file'
                    }), 400

                provided_hash = hashlib.sha256(
                    file_data
                ).hexdigest()

        if not provided_hash:
            return jsonify({
                'error': 'File or document hash required'
            }), 400

        provided_hash = normalize_hash(provided_hash)

        # 2. Find examination record
        paper = None

        if exam_id:

            try:
                paper = ExamPaper.query.get(int(exam_id))
            except (ValueError, TypeError):
                return jsonify({
                    'error': 'Invalid examination ID'
                }), 400

        if not paper:
            paper = ExamPaper.query.filter_by(
                document_hash=provided_hash
            ).first()

        if not paper:

            return jsonify({
                'result': 'NOT_FOUND',
                'message': 'No registered examination found',
                'provided_hash': provided_hash
            }), 200

        # 3. Compare with database hash
        original_hash = normalize_hash(
            paper.document_hash
        )

        database_verified = (
            provided_hash == original_hash
        )

        # 4. Verify against blockchain
        blockchain_hash = None
        blockchain_verified = False

        bc = BlockchainService()

        if not bc.is_connected():

            return jsonify({
                'result': 'BLOCKCHAIN_UNAVAILABLE',
                'message': (
                    'Blockchain is currently unavailable. '
                    'Database verification cannot confirm blockchain integrity.'
                ),
                'database_verified': database_verified,
                'provided_hash': provided_hash,
                'original_hash': original_hash
            }), 503

        if paper.blockchain_exam_id is None:

            return jsonify({
                'result': 'BLOCKCHAIN_NOT_REGISTERED',
                'message': (
                    'This examination paper does not have '
                    'a blockchain registration.'
                ),
                'database_verified': database_verified,
                'provided_hash': provided_hash,
                'original_hash': original_hash
            }), 200

        try:

            details = bc.get_exam_details(
                paper.blockchain_exam_id
            )

            blockchain_hash = normalize_hash(
                details.get('documentHash')
            )

            if not blockchain_hash:
                raise Exception(
                    'Document hash not found in blockchain record'
                )

            blockchain_verified = (
                provided_hash == blockchain_hash
            )

        except Exception as e:

            current_app.logger.exception(
                'Blockchain integrity verification failed'
            )

            return jsonify({
                'result': 'BLOCKCHAIN_VERIFICATION_FAILED',
                'message': 'Unable to retrieve blockchain verification record.',
                'details': str(e),
                'database_verified': database_verified,
                'provided_hash': provided_hash,
                'original_hash': original_hash
            }), 503

        # 5. Final verification
        is_verified = (
            database_verified and blockchain_verified
        )

        result = (
            'VERIFIED' if is_verified else 'TAMPERED'
        )

        message = (
            'Document integrity verified successfully. '
            'Database and blockchain hashes match.'
            if is_verified
            else 'WARNING: Document hash does not match the registered records!'
        )

        return jsonify({
            'result': result,
            'message': message,
            'provided_hash': provided_hash,
            'original_hash': original_hash,
            'blockchain_hash': blockchain_hash,
            'database_verified': database_verified,
            'blockchain_verified': blockchain_verified,
            'paper': paper.to_dict(),
            'verified_at': datetime.utcnow().isoformat(),
            'transaction_hash': paper.transaction_hash,
            'block_number': paper.block_number
        }), 200

    except Exception as e:

        current_app.logger.exception(
            'Document integrity verification failed'
        )

        return jsonify({
            'error': str(e)
        }), 500


@exam_bp.route('/<int:paper_id>', methods=['GET'])
@login_required
def get_exam_details(paper_id):

    paper = ExamPaper.query.get_or_404(paper_id)

    if (
        current_user.role == 'faculty'
        and paper.uploaded_by != current_user.id
    ):
        return jsonify({
            'error': 'Access denied'
        }), 403

    return jsonify({
        'paper': paper.to_dict()
    }), 200


@exam_bp.route('/list', methods=['GET'])
@login_required
def list_exams():

    page = request.args.get(
        'page', 1, type=int
    )

    per_page = request.args.get(
        'per_page', 20, type=int
    )

    # Prevent invalid pagination values
    page = max(1, page)
    per_page = min(max(1, per_page), 100)

    if current_user.role == 'admin':
        query = ExamPaper.query
    else:
        query = ExamPaper.query.filter_by(
            uploaded_by=current_user.id
        )

    status = request.args.get('status')

    if status:
        query = query.filter_by(
            approval_status=status
        )

    pagination = (
        query
        .order_by(ExamPaper.created_at.desc())
        .paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
    )

    return jsonify({
        'papers': [
            paper.to_dict()
            for paper in pagination.items
        ],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200
