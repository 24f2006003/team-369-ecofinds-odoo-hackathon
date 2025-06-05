from app import create_app, db
from app.models import User, Product, Order
import os
from compile_translations import compile_translations

# Try to compile translations, but don't fail if it doesn't work
try:
    compile_translations()
except Exception as e:
    print(f"Warning: Translation compilation failed: {str(e)}")

app = create_app()

# Create database tables in production
with app.app_context():
    try:
        db.create_all()
        # Create demo user if it doesn't exist
        demo_user = User.query.filter_by(email='demo@ecofinds.com').first()
        if not demo_user:
            # First, check if there are any users
            if User.query.count() == 0:
                # If no users exist, we can safely create the demo user with ID 1
                user = User(
                    id=1,  # Explicitly set ID to 1
                    email='demo@ecofinds.com',
                    username='John Smith',
                    phone_number='+1234567890',
                    is_email_verified=True,
                    is_phone_verified=True,
                    eco_points=150,
                    profile_img='default_profile.png',
                    is_admin=True  # Make this user an admin
                )
                user.set_password('demo123')
                db.session.add(user)
                db.session.commit()
                print("Demo admin user created with ID 1")
            else:
                # If other users exist, create demo user normally
                user = User(
                    email='demo@ecofinds.com',
                    username='John Smith',
                    phone_number='+1234567890',
                    is_email_verified=True,
                    is_phone_verified=True,
                    eco_points=150,
                    profile_img='default_profile.png',
                    is_admin=True  # Make this user an admin
                )
                user.set_password('demo123')
                db.session.add(user)
                db.session.commit()
                print("Demo admin user created with auto-generated ID")
        else:
            # Update existing demo user to be admin if not already
            if not demo_user.is_admin:
                demo_user.is_admin = True
                db.session.commit()
                print("Updated existing demo user to admin")
    except Exception as e:
        print(f"Warning: Database initialization failed: {str(e)}")

# Configure for Vercel
app.config['SERVER_NAME'] = None
app.config['PREFERRED_URL_SCHEME'] = 'https'

# For local development
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))