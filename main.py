import os

from flask import Flask, render_template, redirect, url_for
from flask_script import Manager
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import Required

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['DEBUG'] = True
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "data.sqlite")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "key"
db = SQLAlchemy(app)
manager = Manager(app)
bootstrap = Bootstrap(app)

class AddForm(FlaskForm):
    item = StringField("Item", validators=[Required()])
    by = StringField("By", validators=[Required()])
    split = StringField("Split")
    price = FloatField("Price", validators=[Required()])
    submit = SubmitField("Submit")


class Purchase(db.Model):
    __tablename__ = "purchases"
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(64))
    by = db.Column(db.String(64))
    split = db.Column(db.Integer)
    price = db.Column(db.Float)

    def __repr__(self):
        return "(%s, %s, %s, %s, %s)" % (self.id, self.item, self.by, self.split, self.price)

@app.route("/", methods=["GET","POST"])
def index():
    form = AddForm()
    if form.validate_on_submit():
        #float validation
        p = Purchase(item=form.item.data, by=form.by.data, split=form.split.data, price=form.price.data)
        form.item.data = ""
        form.by.data = ""
        form.split.data = ""
        form.price.data = ""
        db.session.add(p)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("main.html", purchases=Purchase.query.all(), form=form)

if __name__ == "__main__":
    manager.run()