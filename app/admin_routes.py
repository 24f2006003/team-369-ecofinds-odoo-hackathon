from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, Product, Complaint, ComplaintHistory
from datetime import datetime, timedelta
from functools import wraps
from sqlalchemy import or_, func
from app.utils import send_email
from collections import defaultdict

admin = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    # Get statistics
    total_users = User.query.count()
    total_products = Product.query.count()
    total_complaints = Complaint.query.count()
    pending_complaints = Complaint.query.filter_by(status='pending').count()
    
    # Get recent complaints
    recent_complaints = Complaint.query.order_by(Complaint.created_at.desc()).limit(5).all()
    
    # Get complaint statistics
    complaint_stats = {
        'pending': Complaint.query.filter_by(status='pending').count(),
        'in_progress': Complaint.query.filter_by(status='in_progress').count(),
        'resolved': Complaint.query.filter_by(status='resolved').count(),
        'closed': Complaint.query.filter_by(status='closed').count()
    }
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_products=total_products,
                         total_complaints=total_complaints,
                         pending_complaints=pending_complaints,
                         recent_complaints=recent_complaints,
                         complaint_stats=complaint_stats)

@admin.route('/admin/complaints')
@login_required
@admin_required
def admin_complaints():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    status_filter = request.args.get('status', 'all')
    search_query = request.args.get('search', '')
    
    query = Complaint.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if search_query:
        query = query.filter(
            or_(
                Complaint.subject.ilike(f'%{search_query}%'),
                Complaint.description.ilike(f'%{search_query}%')
            )
        )
    
    complaints = query.order_by(Complaint.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('admin/complaints.html',
                         complaints=complaints,
                         status_filter=status_filter,
                         search_query=search_query)

@admin.route('/admin/complaints/<int:complaint_id>')
@login_required
@admin_required
def complaint_detail(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    history = ComplaintHistory.query.filter_by(complaint_id=complaint_id).order_by(ComplaintHistory.created_at.desc()).all()
    return render_template('admin/complaint_detail.html', complaint=complaint, history=history)

@admin.route('/admin/complaints/<int:complaint_id>/update', methods=['POST'])
@login_required
@admin_required
def update_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    new_status = request.form.get('status')
    
    if new_status and new_status != complaint.status:
        old_status = complaint.status
        complaint.status = new_status
        complaint.updated_at = datetime.utcnow()
        
        # Record history
        history = ComplaintHistory(
            complaint_id=complaint.id,
            admin_id=current_user.id,
            action=f'Status changed from {old_status} to {new_status}'
        )
        db.session.add(history)
        
        db.session.commit()
        flash('Complaint status updated successfully.', 'success')
    
    return redirect(url_for('admin.complaint_detail', complaint_id=complaint_id))

@admin.route('/admin/complaints/<int:complaint_id>/reply', methods=['POST'])
@login_required
@admin_required
def reply_to_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    reply_text = request.form.get('reply')
    
    if reply_text:
        # Record history
        history = ComplaintHistory(
            complaint_id=complaint.id,
            admin_id=current_user.id,
            action=f'Admin replied: {reply_text}'
        )
        db.session.add(history)
        
        db.session.commit()
        flash('Reply sent successfully.', 'success')
    
    return redirect(url_for('admin.complaint_detail', complaint_id=complaint_id))

@admin.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin.route('/admin/products')
@admin_required
def admin_products():
    products = Product.query.all()
    return render_template('admin/products.html', products=products)

@admin.route('/admin/users/<int:user_id>/update', methods=['POST'])
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Update user fields
    user.is_email_verified = 'is_email_verified' in request.form
    user.is_phone_verified = 'is_phone_verified' in request.form
    user.eco_points = int(request.form.get('eco_points', 0))
    user.is_admin = 'is_admin' in request.form

    try:
        db.session.commit()
        flash('User updated successfully!', 'success')
    except Exception as e:
        current_app.logger.error(f'Error updating user: {str(e)}')
        db.session.rollback()
        flash('An error occurred while updating the user.', 'danger')

    return redirect(url_for('admin.admin_users'))

@admin.route('/admin/products/<int:product_id>/delete', methods=['POST'])
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    try:
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully!', 'success')
    except Exception as e:
        current_app.logger.error(f'Error deleting product: {str(e)}')
        db.session.rollback()
        flash('An error occurred while deleting the product.', 'danger')

    return redirect(url_for('admin.admin_products'))

@admin.route('/admin/complaints/<int:complaint_id>/assign', methods=['POST'])
@login_required
@admin_required
def assign_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    admin_id = request.form.get('admin_id', type=int)
    
    if admin_id:
        admin = User.query.get(admin_id)
        if admin and admin.is_admin:
            old_admin = complaint.assigned_admin
            complaint.assigned_admin_id = admin_id
            
            # Record history
            history = ComplaintHistory(
                complaint_id=complaint.id,
                admin_id=current_user.id,
                action=f'Complaint assigned to {admin.username}'
            )
            db.session.add(history)
            
            db.session.commit()
            flash('Complaint assigned successfully.', 'success')
    
    return redirect(url_for('admin.complaint_detail', complaint_id=complaint_id)) 