from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash

from . import db
from . import login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    dues = db.relationship("Due", foreign_keys="Due.owner_id", backref="owner")
    password_hash = db.Column(db.String(128))

    def generate_registration_token(self):
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
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