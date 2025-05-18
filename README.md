# EcoFinds: Sustainable E-Commerce Platform

**EcoFinds** is a responsive e-commerce platform that connects buyers and sellers in a seamless online marketplace. It offers a user-friendly interface optimized for desktop, tablet, and mobile devices, allowing sellers to manage detailed product listings and buyers to browse, filter, and search for items effortlessly. Key features include secure user authentication, shopping cart functionality, detailed product information, and purchase tracking. Committed to sustainability, EcoFinds promotes the reuse of pre-owned goods, aiming to reduce waste and foster a community of conscious consumers.

## Key Features

- **User Authentication**: A secure mechanism for users to register and log in, enabling personalized experiences across sessions.
- **Profile Creation**: Users can set and edit their usernames, allowing for a more customized profile.
- **User Dashboard**: A central hub where users can manage their profiles, product listings, and other account details.
- **Product Listing Management**: Users can create, view, edit, and delete their own product listings, including title, description, price, and category.
- **Product Browsing & Category Filtering**: Easily browse available products and filter them by predefined categories to narrow down choices.
- **Keyword Search**: A basic search bar helps users find products based on keywords within product titles.
- **Product Detail View**: A detailed page displaying complete product information, including price, description, category, and images.
- **Previous Purchases**: A dedicated section that displays users' previous orders, helping them keep track of their purchasing history.
- **Cart Management**: Users can add products to a cart, view selected items, modify quantities, and proceed to checkout when ready.

## Conclusion

In conclusion, the EcoFinds Platform is a robust, user-friendly solution designed to streamline the buying and selling experience. By offering an intuitive interface, seamless product management, and powerful search and filtering capabilities, it simplifies e-commerce for users of all kinds. Whether you're a seller looking to showcase your products or a buyer seeking to discover new items, the app provides everything you need in one cohesive platform. With a strong focus on security, responsiveness, and user experience, it is perfectly suited for both casual shoppers and active marketplace participants.


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
