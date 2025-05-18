from app import create_app, db
from flask import Blueprint, render_template

app = create_app()

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

def create_app():
    app = Flask(__name__)
    # ...existing config...
    db.init_app(app)

    from app.products.routes import products_bp
    from app.auth.routes import auth_bp
    from app.main.routes import main_bp   # <-- add this line

    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(main_bp)       # <-- add this line

    return app