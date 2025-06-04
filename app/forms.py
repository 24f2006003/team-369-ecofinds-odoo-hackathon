from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange, URL
from flask_babel import _

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