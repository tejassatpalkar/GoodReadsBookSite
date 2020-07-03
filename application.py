import os
import requests

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
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    session.clear()
    if request.method == 'POST':
        check_usr = db.execute("SELECT * FROM users WHERE username = :username",
                               {"username": request.form.get("user_ID")}).fetchone()
        if check_usr is not None:
            # TODO  add in arguments for Displaying invalid username
            print('invalid username')
            return redirect(url_for('register'))
        else:
            temp_hash1 = generate_password_hash(request.form.get("user_Pass"), method='pbkdf2:sha256', salt_length=8)
            if request.form.get("user_Pass") == request.form.get("user_Pass2"):
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
            print("invalid username")
            return redirect(url_for("login"))

        else:

            user_pass = check_usr.hash

            if check_password_hash(user_pass, request.form.get("user_Pass")):
                session["user_id"] = check_usr.id
                session["user_name"] = check_usr.username
                print("successfully logged in")
                return redirect("/search")

            else:
                # TODO return wrong password
                print("invalid password")
                return redirect(url_for("login"))

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/search", methods=["GET"])
def search():
    return render_template("search.html")


@app.route("/results", methods=["POST"])
def results():
    user_input = f'%{request.form.get("book")}%'
    result = db.execute("SELECT * FROM books WHERE \
                        isbn ILIKE :query OR \
                        title ILIKE :query OR \
                        author ILIKE :query",
                        {"query": user_input})

    if result.rowcount == 0:
        return render_template("error.html", message="no results found, try again")
    books = result.fetchall()
    print(books)
    return render_template("results.html", books=books)


@app.route("/book/<book_isbn>", methods=["GET","POST"])
def book(book_isbn):


    if request.method == "POST":
        currentUser = session["user_id"]
        rating = request.form.get("rating")
        comment = request.form.get("comment")
        row = db.execute("SELECT id FROM books WHERE isbn = :isbn",
                         {"isbn": book_isbn})
        bookId = row.fetchone()
        bookId = bookId[0]
        row2 = db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND book_id = :book_id",
                          {"user_id": currentUser,
                           "book_id": bookId})
        if row2.rowcount == 1:
            print("already submitted review for this user")
            return redirect("/book/" + book_isbn)
        rating = int(rating)

        db.execute("INSERT INTO reviews (user_id, book_id, comment, rating, time) VALUES \
                        (:user_id, :book_id, :comment, :rating, NOW()::TIMESTAMP)",
                   {"user_id": currentUser,
                    "book_id": bookId,
                    "comment": comment,
                    "rating": rating})


        db.commit()



        return redirect("/book/" + book_isbn)

    # Take the book ISBN and redirect to his page (GET)
    else:

        row = db.execute("SELECT isbn, title, author, year FROM books WHERE \
                            isbn = :isbn",
                         {"isbn": book_isbn})

        bookInfo = row.fetchall()

        """ GOODREADS reviews """

        # Read API key from env variable
        key = os.getenv("GR_API_KEY")

        # Query the api with key and ISBN as parameters
        query = requests.get("https://www.goodreads.com/book/review_counts.json",
                             params={"key": key, "isbns": book_isbn})

        # Convert the response to JSON
        response = query.json()

        # "Clean" the JSON before passing it to the bookInfo list
        response = response['books'][0]

        # Append it as the second element on the list. [1]
        bookInfo.append(response)

        """ Users reviews """

        # Search book_id by ISBN
        row = db.execute("SELECT id FROM books WHERE isbn = :isbn",
                         {"isbn": book_isbn})

        # Save id into variable
        book = row.fetchone()  # (id,)
        book = book[0]

        # Fetch book reviews
        # Date formatting (https://www.postgresql.org/docs/9.1/functions-formatting.html)
        results = db.execute("SELECT users.username, comment, rating, \
                                to_char(time, 'DD Mon YY - HH24:MI:SS') as time \
                                FROM users \
                                INNER JOIN reviews \
                                ON users.id = reviews.user_id \
                                WHERE book_id = :book \
                                ORDER BY time",
                             {"book": book})

        reviews = results.fetchall()

        return render_template("book.html", bookInfo=bookInfo, reviews=reviews)


@app.route("/api/<book_isbn>", methods=["GET"])
def api_call(book_isbn):
    # code taken from https://github.com/marcorichetta/cs50w-project1/blob/master/application.py

    book = db.execute("SELECT title, author, year, isbn, \
                COUNT(reviews.id) as review_count, \
                AVG(reviews.rating) as average_score \
                FROM books \
                INNER JOIN reviews \
                ON books.id = reviews.book_id \
                WHERE isbn = :isbn \
                GROUP BY title, author, year, isbn",
                {"isbn": book_isbn})
    if book.rowcount != 1:
        return jsonify({"Error": "Invalid book ISBN"}), 422
    book = book.fetchone()
    result = dict(book.items())
    result['average_score'] = float('%.2f' % (result['average_score']))
    return jsonify(result)











