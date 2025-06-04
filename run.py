from app import create_app

app = create_app()

# This is needed for Vercel
app.config['SERVER_NAME'] = None

if __name__ == '__main__':
    app.run(debug=True)