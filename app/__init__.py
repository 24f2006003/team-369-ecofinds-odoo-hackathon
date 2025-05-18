from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'
db = SQLAlchemy(app)

from app.auth import routes as auth_routes
from app.products import routes as product_routes

app.register_blueprint(auth_routes.auth_bp)
app.register_blueprint(product_routes.product_bp)