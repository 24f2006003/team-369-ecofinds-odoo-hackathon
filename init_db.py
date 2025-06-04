from app import create_app, db
from app.models import User, Product
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Add is_admin column
    with db.engine.connect() as conn:
        conn.execute(text('ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0'))
        conn.execute(text('COMMIT'))

    # Create demo user if it doesn't exist
    if not User.query.filter_by(email='demo@ecofinds.com').first():
        user = User(
            email='demo@ecofinds.com',
            username='DemoUser',
            phone_number='+1234567890',
            is_email_verified=True,
            is_phone_verified=True
        )
        user.set_password('demo123')
        db.session.add(user)
        db.session.commit()

    # Create admin user if it doesn't exist
    if not User.query.filter_by(email='admin@ecofinds.com').first():
        admin_user = User(
            email='admin@ecofinds.com',
            username='Admin',
            phone_number='+10000000000',
            is_email_verified=True,
            is_phone_verified=True,
            is_admin=True
        )
        admin_user.set_password('admin@ecofinds')
        db.session.add(admin_user)
        db.session.commit()

    print("Database initialized successfully!") 