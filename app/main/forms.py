import math

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectMultipleField, BooleanField
from wtforms.validators import Required, ValidationError, EqualTo, Regexp

from ..models import User

class AddPurchaseForm(FlaskForm):
    def number_check(form, field):
        try: 
            number = float(field.data)
        except:
            raise ValidationError("Please enter a number.")
        if math.isinf(number) or math.isnan(number):
            raise ValidationError("Please enter a valid number.")

    item = StringField("Item", validators=[Required()])
    split = SelectMultipleField(coerce=int)
    price = StringField("Price", validators=[Required(), number_check])
    submit = SubmitField("Add purchase")

class LoginForm(FlaskForm):
    name = StringField("Name", validators=[Required()])
    password = PasswordField("Password", validators=[Required()])
    remember_me = BooleanField("Keep me logged in")
    submit = SubmitField("Log in")

class RegistrationForm(FlaskForm):
    name = StringField("Name", validators=[Required(), Regexp(r"^[A-Za-z]+$", message="Username must only have letters.")])
    password = PasswordField("Password", validators=[Required()])
    confirm = PasswordField("Confirm password", validators=[Required(), EqualTo("password", message="Passwords must match.")])
    submit = SubmitField("Create account")

    def validate_name(self, field):
        if User.query.filter_by(name=field.data).first():
            raise ValidationError("Name is already in use.")