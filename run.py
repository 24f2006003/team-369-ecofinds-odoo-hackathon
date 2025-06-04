from app import create_app
import os

app = create_app()

# Configure for Vercel
app.config['SERVER_NAME'] = None
app.config['PREFERRED_URL_SCHEME'] = 'https'

# Ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

# For local development
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))