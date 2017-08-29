import os
import math

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_script import Manager, Shell
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate, MigrateCommand
from wtforms import StringField, SubmitField, PasswordField, SelectMultipleField, BooleanField
from wtforms.validators import Required, ValidationError, EqualTo, Regexp
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["DEBUG"] = True
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "data.sqlite")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "key"
app.config["SERVER_NAME"] = "192.168.1.15" #raspberry ip
db = SQLAlchemy(app)
manager = Manager(app)
bootstrap = Bootstrap(app)
login_manager = LoginManager(app)
migrate = Migrate(app, db)
login_manager.login_view = "login"

def make_shell_context():
    return dict(app=app, db=db, User=User, Purchase=Purchase, Due=Due)

@manager.command
def create_registration_link():
    new_user = User()
    db.session.add(new_user)
    db.session.commit()
    print(url_for("register", token=new_user.generate_registration_token(), _external=True))

manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command("db", MigrateCommand)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    dues = db.relationship("Due", foreign_keys="Due.owner_id", backref="owner")
    password_hash = db.Column(db.String(128))

    def generate_registration_token(self):
        s = URLSafeTimedSerializer(app.config["SECRET_KEY"])
        return s.dumps(self.id)

    @property
    def password(self):
        raise AttributeError("password is not a readble attribute")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self): 
        return "<User %s (%s)>" % (self.id, self.name)

class Purchase(db.Model):
    __tablename__ = "purchases"
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(64))
    by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    by = db.relationship("User")
    split = db.Column(db.Integer)
    price = db.Column(db.Float)

    def __repr__(self):
        return "<Purchase %s (%s, %s, %s)>" % (self.id, self.item, self.by.name, self.price)

class Due(db.Model):
    __tablename__ = "dues"
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    to_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    to = db.relationship("User", foreign_keys="Due.to_id")
    amount = db.Column(db.Integer)

    def __repr__(self):
        return "<Due %s, %s (%s)>" % (self.owner_id, self.to_id, self.amount)

@app.route("/register/<token>", methods=["POST","GET"])
def register(token):
    s = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    try:
        id = s.loads(token, max_age=86400)
    except:
        flash("The registration link is invalid or has expired")
        return redirect(url_for("index"))

    u = User.query.get(id)
    if u.name and u.password_hash:
        flash("User is already registered.")
        return redirect(url_for("index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        u.name = form.name.data
        u.password = form.password.data
        db.session.add(u)
        db.session.commit()
        flash("User registration successful.")
        return redirect(url_for("index"))
    return render_template("quick_form.html", header="Register", form=form)

@app.route("/login", methods=["POST", "GET"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(User.name.ilike(form.name.data)).first()
        print(form.name.data)
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get("next") or url_for("index"))
        flash("Invalid username or password.")
    return render_template("quick_form.html", header="Log in", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('index'))

def update_dues(p, split):
    if split:
        split_list = [User.query.get(id) for id in split]
        split_price = p.price/(len(split_list)+1)
    else:
        split_list = User.query.filter(User.name != p.by.name).all()
        split_price = p.price/User.query.count()
    for to_user in split_list:
        forward = Due.query.filter_by(owner_id=to_user.id, to_id=current_user.id).first()
        if not forward:
            forward = Due(owner=to_user,to=current_user, amount=0)
        backward = Due.query.filter_by(owner_id=current_user.id, to_id=to_user.id).first()
        if not backward:
            backward = Due(owner=current_user,to=to_user, amount=0)
        forward.amount += split_price
        m = min(forward.amount, backward.amount)
        forward.amount -= m
        backward.amount -= m
        db.session.add(forward)
        db.session.add(backward)
    db.session.add(p)
    db.session.commit()

def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(error)

@app.route("/", methods=["GET","POST"])
def index():
    form = AddPurchaseForm()
    if current_user.is_authenticated:
        form.split.choices = [(u.id, u.name) for u in User.query.filter(User.name != current_user.name)]
    if form.validate_on_submit():
        split = ", ".join([User.query.get(id).name for id in form.split.data])
        p = Purchase(item=form.item.data, 
                     by=current_user, 
                     split=split if split else "Everyone",
                     price=float(form.price.data))
        update_dues(p, form.split.data)
        form.item.data = ""
        form.split.data = ""
        form.price.data = ""
        #new item add animation
        return redirect(url_for("index"))

    flash_errors(form)
    users = User.query.filter(User.name != None).all()
    n_users = len(users)
    n_rows = math.ceil(n_users/3.0)
    return render_template("index.html", purchases=Purchase.query.all(), form=form, n_rows=n_rows, users=users, n_users=n_users)

if __name__ == "__main__":
    manager.run()