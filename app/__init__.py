from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    # Configure your app
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    
    # Import and register blueprints
    from app.products.routes import products_bp
    from app.auth.routes import auth_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    
    return app