import os
import requests
import json
import string

from flask import Flask, jsonify, session, redirect, url_for, render_template, request, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.sql import text
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

logged_in = False

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

@app.route("/", methods=["GET", "POST"])
def index():
#    session.pop("username", None)
    if "username" in session:
        return render_template("library.html", username = session["username"])
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        account =  db.execute("SELECT EXISTS "
        "(SELECT * "
        "FROM users_t WHERE username "
        "= :username AND password = :password) ",
        {"username" : username, "password" : password}).fetchone()
        if account[0]:
            session["username"] = username
            uid = db.execute("SELECT id "
            "FROM users_t "
            "WHERE username = :username", {"username" : session["username"]}).fetchone()
            session["uid"] = uid[0]
            return render_template("library.html", username = username)
        else:
            return render_template("login.html", error = "Wrong name or password!")
    return render_template("login.html")

@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.pop("username", None)
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        account =  db.execute("SELECT EXISTS"
        "(SELECT * FROM users_t WHERE username"
        "= :username)", {"username" : username}).fetchone()
        if account[0]:
            return render_template("register.html", error = "User already exists!")
        else:
            db.execute("INSERT INTO users_t (username, password) VALUES (:username, :password)",
            {"username" : username, "password" : password})
            db.commit()
            return render_template("login.html", message = "Registered successfully! Login to continue.")
    return render_template("register.html")

@app.route("/library", methods=["GET", "POST"])
def library():
    if request.method == "POST":
        isbn = request.form.get("isbn")
        title = request.form.get("title")
        author = request.form.get("author")
        if isbn:
            search_result = db.execute("SELECT * FROM books_t WHERE isbn LIKE :isbn", {"isbn" : '%'+isbn+'%'})
        if title:
            search_result = db.execute("SELECT * FROM books_t WHERE LOWER(title) LIKE :title", {"title" : '%'+title+'%'})
        if author:
            search_result = db.execute("SELECT * FROM books_t WHERE LOWER(author) LIKE :author", {"author" : '%'+author+'%'})
        if search_result == None:
            return render_template("results.html", error = "Nothing found!")
        return render_template("results.html", search_result = search_result)

    return render_template("library.html")

@app.route("/books/<int:id>", methods=["GET", "POST"])
def books(id = None):

    # Get goodreads.com data for the book
    book = db.execute("SELECT id, isbn, title, author, year "
    "FROM books_t "
    "WHERE id = :id ",
    {"id" : id}).fetchone()
    res = requests.get("https://www.goodreads.com/book/review_counts.json",
    params= {"isbns" : book['isbn'], "key" : "vx0aE0ZPJQB8jChUIacOeA"})
    if res.status_code != 200:
        raise Exception("Error! Api request unsuccessful.")
    goodreads = res.json()
    ratings_count = goodreads["books"][0]["ratings_count"]
    average_rating = goodreads["books"][0]["average_rating"]

    book = db.execute("SELECT id, isbn, title, author, year "
    "FROM books_t "
    "WHERE id = :id ",
    {"id" : id})

    reviews = db.execute("SELECT users_t.username, reviews_t.review, reviews_t.textrev "
    "FROM users_t "
    "INNER JOIN reviews_t "
    "ON users_t.id = reviews_t.uid "
    "WHERE reviews_t.bid = :id ",
    {"id" : id})

    if request.method == "POST":
        reviewed = db.execute("SELECT EXISTS ( "
        "SELECT * "
        "FROM reviews_t "
        "WHERE uid = :uid "
        "AND bid = :bid)",
        {"uid" : session["uid"], "bid" : id}).fetchone()

        if reviewed[0]:
            return render_template("books.html", book = book, reviews = reviews,
            ratings_count = ratings_count, average_rating = average_rating, error = "Already reviewed")

        review = request.form.get("review")
        textrev = request.form.get("textrev")
        db.execute("INSERT INTO reviews_t "
        "(uid, bid, review, textrev) "
        "VALUES (:uid, :bid, :review, :textrev)",
        {"uid" : session["uid"], "bid" : id, "review" : review, "textrev" : textrev})
        reviews = db.execute("SELECT users_t.username, reviews_t.review, reviews_t.textrev "
        "FROM users_t "
        "INNER JOIN reviews_t "
        "ON users_t.id = reviews_t.uid "
        "WHERE reviews_t.bid = :id ",
        {"id" : id})
        db.commit()
        return render_template("books.html", book = book, reviews = reviews,
        ratings_count = ratings_count, average_rating = average_rating, bid = id)

    return render_template("books.html", book = book, ratings_count = ratings_count,
    average_rating = average_rating, reviews = reviews)

@app.route("/api/<string:isbn>", methods=["GET"])
def api(isbn):
    book = db.execute("SELECT title, author, year, isbn "
    "FROM books_t "
    "WHERE isbn = :isbn ",
    {"isbn" : isbn}).fetchone()

    review_count = db.execute("SELECT COUNT(reviews_t.review) "
    "FROM reviews_t "
    "INNER JOIN books_t "
    "ON books_t.id = reviews_t.bid "
    "WHERE books_t.isbn = :isbn ",
    {"isbn" : isbn}).fetchone()

    average_score = db.execute("SELECT AVG(reviews_t.review) OVER() "
    "FROM reviews_t "
    "INNER JOIN books_t "
    "ON books_t.id = reviews_t.bid "
    "WHERE books_t.isbn = :isbn ",
    {"isbn" : isbn}).fetchone()

    #for title, author, year, isbn in book
    book = list(book)
    return jsonify({
    "title": book[0],
    "author": book[1],
    "year": book[2],
    "isbn": book[3],
    "review_count": int(review_count[0]),
    "average_score": int(average_score[0])
    })
