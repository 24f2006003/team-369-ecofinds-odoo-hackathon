from app import create_app, db
from app.models import User, Product, CartItem, Purchase
import os

app = create_app()

# Create database tables in production
with app.app_context():
    db.create_all()
    # Create demo user if it doesn't exist
    if not User.query.filter_by(email='demo@ecofinds.com').first():
        user = User(
            email='demo@ecofinds.com',
            username='John Smith',
            phone_number='+1234567890',
            is_email_verified=True,
            is_phone_verified=True,
            eco_points=150,
            profile_img='default_profile.png'
        )
        user.set_password('demo123')
        db.session.add(user)
        db.session.commit()

# Configure for Vercel
app.config['SERVER_NAME'] = None
app.config['PREFERRED_URL_SCHEME'] = 'https'

# For local development
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))