from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app import db
from app.models import ChatMessage, Product, User
from datetime import datetime

chat = Blueprint('chat', __name__)

@chat.route('/chat/<int:product_id>')
@login_required
def chat_room(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        
        # Prevent users from chatting with themselves
        if product.owner_id == current_user.id:
            flash('You cannot chat with yourself', 'warning')
            return redirect(url_for('product_detail', product_id=product_id))
        
        # Get chat history
        messages = ChatMessage.query.filter_by(
            product_id=product_id
        ).filter(
            ((ChatMessage.sender_id == current_user.id) | 
             (ChatMessage.receiver_id == current_user.id))
        ).order_by(ChatMessage.created_at.asc()).all()
        
        # Mark unread messages as read
        for message in messages:
            if message.receiver_id == current_user.id and not message.is_read:
                message.is_read = True
        db.session.commit()
        
        return render_template('chat.html', product=product, messages=messages)
    except Exception as e:
        current_app.logger.error(f'Error in chat_room: {str(e)}')
        flash('An error occurred while loading the chat room', 'danger')
        return redirect(url_for('product_detail', product_id=product_id))

@chat.route('/chat/send/<int:product_id>', methods=['POST'])
@login_required
def send_message(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        message_content = request.form.get('message', '').strip()
        
        if not message_content:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Prevent users from sending messages to themselves
        if product.owner_id == current_user.id:
            return jsonify({'error': 'You cannot send messages to yourself'}), 400
        
        new_message = ChatMessage(
            sender_id=current_user.id,
            receiver_id=product.owner_id,
            product_id=product_id,
            message=message_content
        )
        
        db.session.add(new_message)
        db.session.commit()
        
        return jsonify({
            'message': new_message.message,
            'sender': current_user.username,
            'timestamp': new_message.created_at.strftime('%Y-%m-%d %H:%M')
        })
    except Exception as e:
        current_app.logger.error(f'Error in send_message: {str(e)}')
        return jsonify({'error': 'Failed to send message'}), 500

@chat.route('/chat/messages')
@login_required
def get_messages():
    try:
        product_id = request.args.get('product_id', type=int)
        if not product_id:
            return jsonify({'error': 'Product ID is required'}), 400
        
        messages = ChatMessage.query.filter_by(
            product_id=product_id
        ).filter(
            ((ChatMessage.sender_id == current_user.id) | 
             (ChatMessage.receiver_id == current_user.id))
        ).order_by(ChatMessage.created_at.asc()).all()
        
        return jsonify([{
            'id': msg.id,
            'message': msg.message,
            'sender': msg.sender.username,
            'timestamp': msg.created_at.strftime('%Y-%m-%d %H:%M')
        } for msg in messages])
    except Exception as e:
        current_app.logger.error(f'Error in get_messages: {str(e)}')
        return jsonify({'error': 'Failed to retrieve messages'}), 500

@chat.route('/chat/conversations')
@login_required
def conversations():
    try:
        # Get all unique conversations for the current user
        conversations = db.session.query(
            ChatMessage.product_id,
            Product.title,
            User.username,
            db.func.count(ChatMessage.id).label('message_count'),
            db.func.sum(db.case((ChatMessage.is_read == False, 1), else_=0)).label('unread_count')
        ).join(
            Product, ChatMessage.product_id == Product.id
        ).join(
            User, db.case(
                (ChatMessage.sender_id == current_user.id, ChatMessage.receiver_id),
                else_=ChatMessage.sender_id
            ) == User.id
        ).filter(
            (ChatMessage.sender_id == current_user.id) | 
            (ChatMessage.receiver_id == current_user.id)
        ).group_by(
            ChatMessage.product_id, Product.title, User.username
        ).all()
        
        return render_template('conversations.html', conversations=conversations)
    except Exception as e:
        current_app.logger.error(f'Error in conversations: {str(e)}')
        flash('An error occurred while loading conversations', 'danger')
        return redirect(url_for('dashboard'))
