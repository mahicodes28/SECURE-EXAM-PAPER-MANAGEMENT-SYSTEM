from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from backend.models import db, User, ExamPaper, AuditLog
from backend.utils.helpers import admin_required, get_client_ip

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard-stats', methods=['GET'])
@login_required
@admin_required
def dashboard_stats():
    from sqlalchemy import extract
    total_faculty = User.query.filter_by(role='faculty').count()
    pending_faculty = User.query.filter_by(role='faculty', account_status='pending').count()
    active_faculty = User.query.filter_by(role='faculty', account_status='active').count()
    suspended_faculty = User.query.filter_by(role='faculty', account_status='suspended').count()
    total_papers = ExamPaper.query.count()
    pending_papers = ExamPaper.query.filter_by(approval_status='pending').count()
    approved_papers = ExamPaper.query.filter_by(approval_status='approved').count()
    rejected_papers = ExamPaper.query.filter_by(approval_status='rejected').count()
    monthly_data = []
    for i in range(5, -1, -1):
        import calendar as cal
        now = datetime.utcnow()
        month = ((now.month - 1 - i) % 12) + 1
        year = now.year + ((now.month - 1 - i) // 12)
        count = ExamPaper.query.filter(
            extract('year', ExamPaper.created_at) == year,
            extract('month', ExamPaper.created_at) == month
        ).count()
        month_name = cal.month_abbr[month]
        monthly_data.append({'month': f'{month_name} {year}', 'count': count})
    return jsonify({
        'faculty': {'total': total_faculty, 'pending': pending_faculty, 'active': active_faculty, 'suspended': suspended_faculty},
        'papers': {'total': total_papers, 'pending': pending_papers, 'approved': approved_papers, 'rejected': rejected_papers},
        'monthly_uploads': monthly_data
    }), 200

@admin_bp.route('/faculty', methods=['GET'])
@login_required
@admin_required
def list_faculty():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    search = request.args.get('search', '')
    query = User.query.filter_by(role='faculty')
    if status:
        query = query.filter_by(account_status=status)
    if search:
        query = query.filter(
            (User.name.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (User.employee_id.ilike(f'%{search}%'))
        )
    pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({'faculty': [u.to_dict() for u in pagination.items], 'total': pagination.total, 'pages': pagination.pages, 'current_page': page}), 200

@admin_bp.route('/faculty/<int:user_id>', methods=['GET'])
@login_required
@admin_required
def get_faculty(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({'user': user.to_dict()}), 200

@admin_bp.route('/faculty/<int:user_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_faculty(user_id):
    user = User.query.get_or_404(user_id)
    if user.role != 'faculty':
        return jsonify({'error': 'User is not faculty'}), 400
    user.account_status = 'active'
    log = AuditLog(user_id=current_user.id, action='FACULTY_APPROVED',
        description=f'Admin approved faculty: {user.email}', ip_address=get_client_ip(request), severity='info')
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': f'Faculty {user.name} approved successfully', 'user': user.to_dict()}), 200

@admin_bp.route('/faculty/<int:user_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_faculty(user_id):
    user = User.query.get_or_404(user_id)
    if user.role != 'faculty':
        return jsonify({'error': 'User is not faculty'}), 400
    data = request.get_json() or {}
    user.account_status = 'suspended'
    log = AuditLog(user_id=current_user.id, action='FACULTY_REJECTED',
        description=f'Admin rejected faculty: {user.email}. Reason: {data.get("reason","Not specified")}',
        ip_address=get_client_ip(request), severity='warning')
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': f'Faculty {user.name} rejected/suspended', 'user': user.to_dict()}), 200

@admin_bp.route('/papers', methods=['GET'])
@login_required
@admin_required
def list_papers():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    search = request.args.get('search', '')
    query = ExamPaper.query
    if status:
        query = query.filter_by(approval_status=status)
    if search:
        query = query.filter(
            (ExamPaper.exam_name.ilike(f'%{search}%')) |
            (ExamPaper.subject_code.ilike(f'%{search}%')) |
            (ExamPaper.subject_name.ilike(f'%{search}%'))
        )
    pagination = query.order_by(ExamPaper.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({'papers': [p.to_dict() for p in pagination.items], 'total': pagination.total, 'pages': pagination.pages, 'current_page': page}), 200

@admin_bp.route('/papers/<int:paper_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_paper(paper_id):
    from backend.services.blockchain_service import BlockchainService
    paper = ExamPaper.query.get_or_404(paper_id)
    if paper.approval_status != 'pending':
        return jsonify({'error': f'Paper is already {paper.approval_status}'}), 400
    bc = BlockchainService()
    tx_result = None
    if bc.is_connected() and paper.blockchain_exam_id is not None:
        try:
            tx_result = bc.approve_exam(paper.blockchain_exam_id)
        except Exception as e:
            log_bc = AuditLog(user_id=current_user.id, action='BLOCKCHAIN_APPROVE_FAILED',
                description=f'Blockchain approval failed for paper {paper_id}: {str(e)}',
                ip_address=get_client_ip(request), severity='warning')
            db.session.add(log_bc)
    paper.approval_status = 'approved'
    paper.approved_by = current_user.id
    paper.approval_timestamp = datetime.utcnow()
    if tx_result:
        paper.approval_transaction_hash = tx_result.get('transactionHash')
    log = AuditLog(user_id=current_user.id, action='PAPER_APPROVED',
        description=f'Admin approved exam paper: {paper.exam_name} ({paper.subject_code})',
        ip_address=get_client_ip(request), transaction_hash=paper.approval_transaction_hash, severity='info')
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': 'Exam paper approved successfully', 'paper': paper.to_dict(), 'blockchain_tx': tx_result}), 200

@admin_bp.route('/papers/<int:paper_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_paper(paper_id):
    from backend.services.blockchain_service import BlockchainService
    paper = ExamPaper.query.get_or_404(paper_id)
    if paper.approval_status != 'pending':
        return jsonify({'error': f'Paper is already {paper.approval_status}'}), 400
    data = request.get_json() or {}
    reason = data.get('reason', 'Not specified')
    bc = BlockchainService()
    tx_result = None
    if bc.is_connected() and paper.blockchain_exam_id is not None:
        try:
            tx_result = bc.reject_exam(paper.blockchain_exam_id)
        except Exception:
            pass
    paper.approval_status = 'rejected'
    paper.approved_by = current_user.id
    paper.approval_timestamp = datetime.utcnow()
    paper.rejection_reason = reason
    if tx_result:
        paper.approval_transaction_hash = tx_result.get('transactionHash')
    log = AuditLog(user_id=current_user.id, action='PAPER_REJECTED',
        description=f'Admin rejected exam paper: {paper.exam_name}. Reason: {reason}',
        ip_address=get_client_ip(request), transaction_hash=paper.approval_transaction_hash, severity='warning')
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': 'Exam paper rejected', 'paper': paper.to_dict()}), 200

@admin_bp.route('/audit-logs', methods=['GET'])
@login_required
@admin_required
def get_audit_logs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    severity = request.args.get('severity')
    action = request.args.get('action')
    query = AuditLog.query
    if severity:
        query = query.filter_by(severity=severity)
    if action:
        query = query.filter(AuditLog.action.ilike(f'%{action}%'))
    pagination = query.order_by(AuditLog.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({'logs': [l.to_dict() for l in pagination.items], 'total': pagination.total, 'pages': pagination.pages, 'current_page': page}), 200
