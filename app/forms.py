from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange, URL
from flask_babel import _
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import Length, Optional

class ProductForm(FlaskForm):
    title = StringField(_('Title'), validators=[DataRequired()])
    description = TextAreaField(_('Description'), validators=[DataRequired()])
    price = FloatField(_('Price'), validators=[DataRequired(), NumberRange(min=0)])
    category = SelectField(_('Category'), choices=[
        ('Eco-Friendly', _('Eco-Friendly')),
        ('Recycled', _('Recycled')),
        ('Water Saving', _('Water Saving'))
    ])
    image_url = StringField(_('Image URL'), validators=[DataRequired(), URL()])
    city = StringField(_('City'), validators=[DataRequired()])
    state = StringField(_('State'), validators=[DataRequired()])
    submit = SubmitField(_('Add Product'))

class ComplaintForm(FlaskForm):
    subject = StringField('Subject', validators=[
        DataRequired(),
        Length(min=5, max=200, message='Subject must be between 5 and 200 characters')
    ])
    description = TextAreaField('Description', validators=[
        DataRequired(),
        Length(min=10, message='Description must be at least 10 characters long')
    ])
    category = SelectField('Category', choices=[
        ('general', 'General'),
        ('product_issue', 'Product Issue'),
        ('seller_issue', 'Seller Issue'),
        ('technical', 'Technical'),
        ('other', 'Other')
    ], default='general')
    evidence = FileField('Evidence', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx'], 
                   'Only images, PDFs, and Word documents are allowed')
    ])
    submit = SubmitField('Submit Complaint') 