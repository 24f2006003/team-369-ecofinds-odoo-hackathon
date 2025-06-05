from flask import Blueprint, render_template, jsonify, request, abort
from flask_login import login_required, current_user
from app.models import Order
from app import db

from app.admin import bp

@bp.before_request
def before_request():
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)

@bp.route('/orders')
@login_required
def orders():
    status = request.args.get('status')
    query = Order.query
    
    if status:
        query = query.filter_by(status=status)
    
    orders = query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)

@bp.route('/order/<int:id>/update-status', methods=['POST'])
@login_required
def update_order_status(id):
    order = Order.query.get_or_404(id)
    data = request.get_json()
    
    if not data or 'status' not in data:
        return jsonify({'success': False, 'error': 'Status is required'}), 400
    
    new_status = data['status']
    valid_statuses = ['purchased', 'delivered', 'cancelled', 'returned']
    
    if new_status not in valid_statuses:
        return jsonify({'success': False, 'error': 'Invalid status'}), 400
    
    order.status = new_status
    db.session.commit()
    
    return jsonify({'success': True}) 