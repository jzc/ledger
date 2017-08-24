import os
import math

from flask import Flask, render_template, redirect, url_for
from flask_script import Manager, Shell
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import Required

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["DEBUG"] = True
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "data.sqlite")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "key"
db = SQLAlchemy(app)
manager = Manager(app)
bootstrap = Bootstrap(app)

def make_shell_context():
    return dict(app=app, db=db, User=User, Purchase=Purchase, Due=Due)

manager.add_command("shell", Shell(make_context=make_shell_context))

class AddForm(FlaskForm):
    item = StringField("Item", validators=[Required()])
    by = StringField("By", validators=[Required()])
    split = StringField("Split")
    price = FloatField("Price", validators=[Required()])
    submit = SubmitField("Submit")

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    dues = db.relationship("Due", foreign_keys="Due.owner_id", backref="owner")
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

@app.route("/", methods=["GET","POST"])
def index():
    form = AddForm()
    if form.validate_on_submit():
        #float validation
        owner_user = User.query.filter_by(name=form.by.data).first()
        if owner_user:
            p = Purchase(item=form.item.data, by=owner_user, split=form.split.data, price=form.price.data)
            split_list = User.query.filter(User.name != p.by.name).all()
            split_price = p.price/User.query.count()
            for to_user in split_list:
                forward = Due.query.filter_by(owner_id=to_user.id, to_id=owner_user.id).first()
                if not forward:
                    forward = Due(owner=to_user,to=owner_user, amount=0)
                backward = Due.query.filter_by(owner_id=owner_user.id, to_id=to_user.id).first()
                if not backward:
                    backward = Due(owner=owner_user,to=to_user, amount=0)
                forward.amount += split_price
                m = min(forward.amount, backward.amount)
                forward.amount -= m
                backward.amount -= m
                db.session.add(forward)
                db.session.add(backward)
            form.item.data = ""
            form.by.data = ""
            form.split.data = ""
            form.price.data = ""
            db.session.add(p)
            db.session.commit()
            #new item add animation
        return redirect(url_for("index"))
    users = User.query.all()
    n_users = len(users)
    n_rows = math.ceil(n_users/3.0)
    return render_template("main.html", purchases=Purchase.query.all(), form=form, n_rows=n_rows, users=users, n_users=n_users)

if __name__ == "__main__":
    manager.run()