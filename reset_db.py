from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Drop all tables
    with db.engine.connect() as conn:
        conn.execute(text('DROP TABLE IF EXISTS complaint_history'))
        conn.execute(text('DROP TABLE IF EXISTS complaint'))
        conn.execute(text('DROP TABLE IF EXISTS purchase'))
        conn.execute(text('DROP TABLE IF EXISTS product_rating'))
        conn.execute(text('DROP TABLE IF EXISTS cart_item'))
        conn.execute(text('DROP TABLE IF EXISTS chat_message'))
        conn.execute(text('DROP TABLE IF EXISTS product'))
        conn.execute(text('DROP TABLE IF EXISTS user'))
        conn.commit()
    print('Dropped all tables.')
    
    # Create all tables with the new schema
    db.create_all()
    print('Created all tables with updated schema.') 