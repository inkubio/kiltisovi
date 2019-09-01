from flask import Flask, render_template, flash, g, request, make_response
import sqlite3
import os
import json
from config import Config
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.config.from_object(Config)

LAST_ID = "lastid.txt"


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    card = StringField("Card ID", validators=[DataRequired()])
    submit = SubmitField("Register")


def load_file(filename):
    with open(filename) as f:
        return json.load(f)

def dump_file(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f)


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(Config.DATABASE)
    db.row_factory = sqlite3.Row
    return db


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    get_db().commit()
    cur.close()
    return (rv[0] if rv else None) if one else rv


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


with app.app_context():
    if not os.path.isfile(Config.DATABASE):
        query_db(Config.INIT_DB)


@app.route("/", methods=["GET", "POST", "DELETE"])
def index():
    form = RegisterForm()
    if form.validate_on_submit():
        query_db(Config.ADD_USER, (form.email.data, form.card.data))
        flash("Added new card {} for email {}".format(
            form.card.data, form.email.data))
    
    users = query_db(Config.GET_USERS)
    last = load_file(LAST_ID) or {"id": ""}
    return render_template("index.html", form=form, users=users, last_id=last["id"])


@app.route("/check", methods=["POST"])
def check():
    req = request.get_json()
    card_id = req["id"]
    db_ret = query_db(Config.VALID_ID, (card_id,), True)

    if db_ret[0]:
        return make_response("nice", 200)
    else:
        dump_file(LAST_ID, req)
        return make_response("fug", 403)


@app.route("/error")
def error():
    req = request.get_json()
    print(req["error"])
