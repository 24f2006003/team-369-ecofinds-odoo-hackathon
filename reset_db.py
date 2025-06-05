import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import db, create_app
from app.models import User, Product, Order, ProductRating, Complaint

app = create_app()
with app.app_context():
    # Drop all tables
    db.drop_all()
    print("Dropped all tables.")
    
    # Create all tables
    db.create_all()
    print("Created all tables with updated schema.") 