from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import User, Product, Message

chat = Blueprint('chat', __name__)

@chat.route('/chat/<int:seller_id>/<int:product_id>', methods=['GET', 'POST'])
@login_required
def chat_with_seller(seller_id, product_id):
    seller = User.query.get_or_404(seller_id)
    product = Product.query.get_or_404(product_id)
    # Fetch all messages between current user and seller for this product
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == seller_id) |
         (Message.sender_id == seller_id) & (Message.receiver_id == current_user.id)) &
        (Message.product_id == product_id)
    ).order_by(Message.timestamp.asc()).all()
    if request.method == 'POST':
        content = request.form.get('message')
        if content:
            msg = Message(
                sender_id=current_user.id,
                receiver_id=seller_id,
                product_id=product_id,
                content=content
            )
            db.session.add(msg)
            db.session.commit()
            flash('Message sent!', 'success')
            return redirect(url_for('chat.chat_with_seller', seller_id=seller_id, product_id=product_id))
    return render_template('chat.html', seller=seller, product=product, messages=messages)
