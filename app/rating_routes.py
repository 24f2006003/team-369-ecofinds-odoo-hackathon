from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Rating, Purchase, User

rating = Blueprint('rating', __name__)

@rating.route('/rate/<int:purchase_id>', methods=['GET', 'POST'])
@login_required
def rate_transaction(purchase_id):
    purchase = Purchase.query.get_or_404(purchase_id)
    
    # Check if user is authorized to rate
    if purchase.user_id != current_user.id and purchase.product.owner_id != current_user.id:
        flash('You are not authorized to rate this transaction', 'danger')
        return redirect(url_for('purchases'))
    
    # Check if already rated
    existing_rating = Rating.query.filter_by(
        purchase_id=purchase_id,
        rater_id=current_user.id
    ).first()
    
    if existing_rating:
        flash('You have already rated this transaction', 'warning')
        return redirect(url_for('purchases'))
    
    if request.method == 'POST':
        rating_value = request.form.get('rating', type=int)
        comment = request.form.get('comment', '')
        
        if not rating_value or rating_value < 1 or rating_value > 5:
            flash('Invalid rating value', 'danger')
            return redirect(url_for('rate_transaction', purchase_id=purchase_id))
        
        # Determine who is being rated
        rated_id = purchase.product.owner_id if purchase.user_id == current_user.id else purchase.user_id
        
        new_rating = Rating(
            rater_id=current_user.id,
            rated_id=rated_id,
            purchase_id=purchase_id,
            rating=rating_value,
            comment=comment
        )
        
        db.session.add(new_rating)
        purchase.is_rated = True
        db.session.commit()
        
        flash('Thank you for your rating!', 'success')
        return redirect(url_for('purchases'))
    
    return render_template('rate_transaction.html', purchase=purchase)

@rating.route('/ratings/<int:user_id>')
def view_ratings(user_id):
    user = User.query.get_or_404(user_id)
    ratings = Rating.query.filter_by(rated_id=user_id).order_by(Rating.created_at.desc()).all()
    
    # Calculate average rating
    avg_rating = db.session.query(db.func.avg(Rating.rating)).filter_by(rated_id=user_id).scalar() or 0
    
    return render_template('view_ratings.html', user=user, ratings=ratings, avg_rating=round(avg_rating, 1))

@rating.route('/rating/<int:rating_id>')
def view_rating(rating_id):
    rating = Rating.query.get_or_404(rating_id)
    return render_template('view_rating.html', rating=rating) 