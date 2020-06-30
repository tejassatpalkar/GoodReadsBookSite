import os

from setup.Keys import GR_API_KEY
from flask import Flask, session, render_template, request, redirect, jsonify, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("layout.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        session.clear()
        check_usr = db.execute("SELECT * FROM users WHERE username = :username",
                               {"username":request.form.get("user_ID")}).fetchone()
        if check_usr is not None:
            # TODO  add in arguments for Displaying invalid username
            print('invalid username')
            return redirect(url_for('register'))
        else:
            temp_hash1 = generate_password_hash(request.form.get("user_Pass"), method='pbkdf2:sha256', salt_length=8)
            temp_hash2 = generate_password_hash(request.form.get("user_Pass2"), method='pbkdf2:sha256', salt_length=8)
            if temp_hash1 == temp_hash2:
                db.execute("INSERT INTO users (username,hash) VALUES (:username, :hash)",
                                        {'username': request.form.get("user_ID"),
                                         'hash': temp_hash1})
                db.commit()
                # TODO add in arguments for displaying successfully creating account
                print('success')
                return redirect('/login')
            else:
                # TODO add in arguments for Displaying invalid password
                print('invalid password')
                return redirect(url_for('register'))

    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == 'POST':
        check_usr = db.execute("SELECT * FROM users WHERE username = :username",
                               {"username": request.form.get("user_ID")}).fetchone()
        if check_usr is None:
            # TODO return arguments to display invalid username
            return render_template("layout.html")

        else:
            user_input_pass = generate_password_hash(request.form.get("user_Pass"), method='pbkdf2:sha256', salt_length=8)
            user_pass = check_usr.hash
            if user_pass == user_input_pass:
                session["user_id"] = check_usr.id
                session["user_name"] = check_usr.username
                return  redirect(url_for("search"))

            else:
                return redirect(url_for("login"))

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    return


@app.route("/search", methods=["GET"])
def search():
    return "search page"









