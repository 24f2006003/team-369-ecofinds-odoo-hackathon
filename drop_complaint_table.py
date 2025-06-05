from app import create_app, db

app = create_app()

with app.app_context():
    db.engine.execute('DROP TABLE IF EXISTS complaint')
    print('Dropped complaint table.') 