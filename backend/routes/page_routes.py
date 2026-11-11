from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required

page_bp = Blueprint('page', __name__)

@page_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('page.admin_dashboard'))
        return redirect(url_for('page.faculty_dashboard'))
    return render_template('landing.html')

@page_bp.route('/login')
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('page.index'))
    return render_template('login.html')

@page_bp.route('/register')
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for('page.index'))
    return render_template('register.html')

@page_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('page.faculty_dashboard'))
    return render_template('admin/dashboard.html')

@page_bp.route('/admin/faculty')
@login_required
def admin_faculty():
    if current_user.role != 'admin':
        return redirect(url_for('page.index'))
    return render_template('admin/faculty_management.html')

@page_bp.route('/admin/papers')
@login_required
def admin_papers():
    if current_user.role != 'admin':
        return redirect(url_for('page.index'))
    return render_template('admin/exam_papers.html')

@page_bp.route('/admin/audit-logs')
@login_required
def admin_audit_logs():
    if current_user.role != 'admin':
        return redirect(url_for('page.index'))
    return render_template('admin/audit_logs.html')

@page_bp.route('/faculty/dashboard')
@login_required
def faculty_dashboard():
    return render_template('faculty/dashboard.html')

@page_bp.route('/faculty/upload')
@login_required
def faculty_upload():
    return render_template('faculty/upload.html')

@page_bp.route('/faculty/papers')
@login_required
def faculty_papers():
    return render_template('faculty/my_papers.html')

@page_bp.route('/verify')
def verify_page():
    return render_template('verify.html')

@page_bp.route('/explorer')
def blockchain_explorer():
    return render_template('blockchain_explorer.html')

@page_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html')
