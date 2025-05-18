from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Product
from app import db

products_bp = Blueprint('products', __name__)

@products_bp.route('/products', methods=['GET'])
def product_list():
    products = Product.query.all()
    return render_template('product_list.html', products=products)

@products_bp.route('/products/new', methods=['GET', 'POST'])
def new_product():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = request.form['price']
        # Add additional fields as necessary
        new_product = Product(title=title, description=description, price=price)
        db.session.add(new_product)
        db.session.commit()
        flash('Product created successfully!', 'success')
        return redirect(url_for('products.product_list'))
    return render_template('new_product.html')

@products_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        product.title = request.form['title']
        product.description = request.form['description']
        product.price = request.form['price']
        # Update additional fields as necessary
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('products.product_list'))
    return render_template('edit_product.html', product=product)

@products_bp.route('/products/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('products.product_list'))