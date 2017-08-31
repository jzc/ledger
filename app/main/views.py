import math

from flask import current_app, flash, url_for, redirect, render_template, request
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer

from . import main
from .. import db
from ..models import User, Due, Purchase
from .forms import RegistrationForm, LoginForm, AddPurchaseForm

@main.route("/register/<token>", methods=["POST","GET"])
def register(token):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        id = s.loads(token, max_age=86400)
    except:
        flash("The registration link is invalid or has expired")
        return redirect(url_for("main.index"))

    u = User.query.get(id)
    if u.name and u.password_hash:
        flash("User is already registered.")
        return redirect(url_for("main.index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        u.name = form.name.data
        u.password = form.password.data
        db.session.add(u)
        db.session.commit()
        flash("User registration successful.")
        return redirect(url_for("main.index"))
    return render_template("quick_form.html", header="Register", form=form)

@main.route("/login", methods=["POST", "GET"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(User.name.ilike(form.name.data)).first()
        print(form.name.data)
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get("next") or url_for("main.index"))
        flash("Invalid username or password.")
    return render_template("quick_form.html", header="Log in", form=form)

@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))

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

@main.route("/", methods=["GET","POST"])
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
        return redirect(url_for("main.index"))

    flash_errors(form)
    users = User.query.filter(User.name != None).all()
    n_users = len(users)
    n_rows = math.ceil(n_users/3.0)
    return render_template("index.html", purchases=Purchase.query.all(), form=form, n_rows=n_rows, users=users, n_users=n_users)