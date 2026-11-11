from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from backend.models import db, ExamPaper, AuditLog
from backend.utils.helpers import faculty_required, get_client_ip

faculty_bp = Blueprint('faculty', __name__)

@faculty_bp.route('/dashboard-stats', methods=['GET'])
@login_required
@faculty_required
def dashboard_stats():
    user_id = current_user.id
    total = ExamPaper.query.filter_by(uploaded_by=user_id).count()
    pending = ExamPaper.query.filter_by(uploaded_by=user_id, approval_status='pending').count()
    approved = ExamPaper.query.filter_by(uploaded_by=user_id, approval_status='approved').count()
    rejected = ExamPaper.query.filter_by(uploaded_by=user_id, approval_status='rejected').count()
    recent = ExamPaper.query.filter_by(uploaded_by=user_id).order_by(ExamPaper.created_at.desc()).limit(5).all()
    return jsonify({
        'stats': {'total': total, 'pending': pending, 'approved': approved, 'rejected': rejected},
        'recent_papers': [p.to_dict() for p in recent]
    }), 200

@faculty_bp.route('/papers', methods=['GET'])
@login_required
@faculty_required
def my_papers():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    query = ExamPaper.query.filter_by(uploaded_by=current_user.id)
    if status:
        query = query.filter_by(approval_status=status)
    pagination = query.order_by(ExamPaper.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({'papers': [p.to_dict() for p in pagination.items], 'total': pagination.total, 'pages': pagination.pages, 'current_page': page}), 200

@faculty_bp.route('/papers/<int:paper_id>', methods=['GET'])
@login_required
@faculty_required
def get_paper(paper_id):
    paper = ExamPaper.query.get_or_404(paper_id)
    if current_user.role != 'admin' and paper.uploaded_by != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    return jsonify({'paper': paper.to_dict()}), 200

@faculty_bp.route('/audit-logs', methods=['GET'])
@login_required
@faculty_required
def my_audit_logs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    pagination = AuditLog.query.filter_by(user_id=current_user.id).order_by(
        AuditLog.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({'logs': [l.to_dict() for l in pagination.items], 'total': pagination.total, 'pages': pagination.pages, 'current_page': page}), 200
