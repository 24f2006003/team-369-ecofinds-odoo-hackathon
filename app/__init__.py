from flask import Flask, render_template, request, redirect, url_for, session, flash, g, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_babel import Babel, _
from flask_migrate import Migrate
import os
from werkzeug.utils import secure_filename
from app.config import Config
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy import or_
from datetime import datetime

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
babel = Babel()

@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    babel.init_app(app)
    login_manager.login_view = 'auth.login'

    # Add context processor for 'now' variable
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}

    # Configure supported languages
    app.config['LANGUAGES'] = {
        'en': 'English',
        'hi': 'हिंदी',
        'gu': 'ગુજરાતી'
    }

    # Configure Babel
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = os.path.join(app.root_path, 'translations')

    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.chat_routes import chat as chat_blueprint
    app.register_blueprint(chat_blueprint)
    
    from app.rating_routes import rating as rating_blueprint
    app.register_blueprint(rating_blueprint)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    # Import models here to avoid circular imports
    from app.models import User, Product, Order, ChatMessage, Rating, Complaint, Category

    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create default categories if they don't exist
        default_categories = [
            {'name': 'Eco-Friendly', 'description': 'Products that are environmentally friendly'},
            {'name': 'Recycled', 'description': 'Products made from recycled materials'},
            {'name': 'Water Saving', 'description': 'Products that help conserve water'},
            {'name': 'Other', 'description': 'Other eco-friendly products'}
        ]
        
        for category_data in default_categories:
            if not Category.query.filter_by(name=category_data['name']).first():
                category = Category(**category_data)
                db.session.add(category)
        
        try:
            db.session.commit()
            app.logger.info("Default categories created successfully")
        except Exception as e:
            app.logger.error(f"Error creating default categories: {str(e)}")
            db.session.rollback()

        # Add default products if none exist
        if Product.query.count() == 0:
            try:
                demo_products = [
                    Product(title='Eco-Friendly Water Bottle', description='Reusable water bottle made from recycled materials.', price=129.99, category_id=1, image_url='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQRZ1rOtZUOy4m3hbbgp27D_IKXBkaO2_mwXQ&s', seller_id=1, city='Mumbai', state='Maharashtra'),
                    Product(title='Bamboo Toothbrush', description='Biodegradable toothbrush with bamboo handle.', price=39.49, category_id=1, image_url='https://m.media-amazon.com/images/I/71edeKpYPpL.jpg', seller_id=1, city='Delhi', state='Delhi'),
                    Product(title='Recycled Notebook', description='Notebook made from 100% recycled paper.', price=59.99, category_id=2, image_url='https://images2.habeco.si/Upload/Product/sonora-plus---recycled-paper-notebook-pen_8494_productmain.webp', seller_id=1, city='Bangalore', state='Karnataka'),
                    Product(title='Water-Saving Showerhead', description='Eco-friendly showerhead that reduces water usage by 40%.', price=1999.99, category_id=3, image_url='https://m.media-amazon.com/images/I/81eF1mDe5gL.jpg', seller_id=1, city='Chennai', state='Tamil Nadu'),
                    Product(title='Eco-Friendly Water Bottle', description='Sustainable hydration on the go.', price=599, category_id=1, image_url='https://pplx-res.cloudinary.com/image/upload/v1749017272/gpt4o_images/kfvxpybk0ldixn89rhug.png', seller_id=1, city='Hyderabad', state='Telangana'),
                    Product(title='Eco-Friendly Tote Bag', description='Reusable tote bag made from recycled materials.', price=299, category_id=1, image_url='https://pplx-res.cloudinary.com/image/upload/v1749017789/gpt4o_images/bsz1nd5eddn0f7fzfth0.png', seller_id=1, city='Kolkata', state='West Bengal'),
                    Product(title='Eco-Friendly Keychain', description='Sustainable keychain made from recycled materials, perfect for your keys or bag.', price=99, category_id=1, image_url='https://pplx-res.cloudinary.com/image/upload/v1749017410/gpt4o_images/niqwd5dplgm4iwwylupe.png', seller_id=1, city='Pune', state='Maharashtra'),
                    Product(title='Eco-Friendly T-Shirt', description='Sustainable t-shirt made from organic cotton, a look you can wear anywhere', price=299, category_id=1, image_url='https://pplx-res.cloudinary.com/image/upload/v1749024630/gpt4o_images/rbnmez9sdd91glbo0f6i.png', seller_id=1, city='Ahmedabad', state='Gujarat'),
                    Product(title='Eco-Friendly Toothbrush', description='Biodegradable toothbrush for a cleaner mouth and a cleaner planet', price=89, category_id=1, image_url='https://i.postimg.cc/nLBgbmMj/Tooth.png', seller_id=1, city='Jaipur', state='Rajasthan'),
                    Product(title='Eco-Friendly Backpack', description='Sustainable backpack made from recycled materials, perfect for your daily needs.', price=699, category_id=1, image_url='https://pplx-res.cloudinary.com/image/upload/v1749017981/gpt4o_images/s3rtl7i6hqrqxorx4zlc.png', seller_id=1, city='Lucknow', state='Uttar Pradesh')
                ]
                for product in demo_products:
                    db.session.add(product)
                db.session.commit()
                app.logger.info("Demo products created successfully")
            except Exception as e:
                app.logger.error(f"Error creating demo products: {str(e)}")
                db.session.rollback()

    @babel.localeselector
    def get_locale():
        # Try to get the language from the session
        return session.get('language', 'en')

    @app.route('/set_language/<lang_code>')
    def set_language(lang_code):
        if lang_code in app.config['LANGUAGES']:
            session['language'] = lang_code
        return redirect(request.referrer or url_for('main.index'))

    return app