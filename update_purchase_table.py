from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Drop the existing purchase table
    with db.engine.connect() as conn:
        conn.execute(text('DROP TABLE IF EXISTS purchase'))
        conn.commit()
    print('Dropped purchase table.')
    
    # Create all tables with the new schema
    db.create_all()
    print('Created purchase table with updated schema.') 