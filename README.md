# EcoFinds - Sustainable Second-Hand Marketplace

EcoFinds is a web application designed to create a sustainable second-hand marketplace where users can buy and sell pre-owned items. The platform promotes eco-friendly practices by encouraging the reuse of products.

## Features

- **User Authentication**: Secure registration and login for users.
- **Product Listing Management**: Users can create, view, edit, and delete their product listings.
- **Responsive Design**: Optimized for both desktop and mobile devices, ensuring a seamless user experience.
- **Search and Filter Options**: Users can easily find products based on categories and keywords.

## Project Structure

```
EcoFinds
├── app
│   ├── __init__.py
│   ├── auth
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── products
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── models.py
│   ├── templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── register.html
│   │   └── product_list.html
│   └── static
│       ├── css
│       │   └── styles.css
│       └── js
│           └── main.js
├── run.py
├── requirements.txt
└── README.md
```

## Setup Instructions

1. **Clone the Repository**: 
   ```
   git clone https://github.com/24f2006003/team-369-ecofinds-odoo-hackathon
   cd EcoFinds
   ```

2. **Create a Virtual Environment**:
   ```
   python -m venv venv
   On Mac use `source venv/bin/activate`
   On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**:
   ```
   pip install -r requirements.txt
   ```

4. **Run the Application**:
   ```
   python run.py
   ```

5. **Access the Application**: Open your web browser and go to `http://127.0.0.1:5000`.
