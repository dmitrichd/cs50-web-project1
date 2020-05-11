#This is a project 1 CS50 web Harvard course implementation by github.com/dmitrichd
#Simple dynamic library that stores data in a Heroky postgre database
#Involves Python, FLASK, GIT, HEROKU, PSQL, sqlalchemy
#Only for demonstration purposes.
#CREDENTIALS:
#https://github.com/dmitrichd/cs50-web-project1.github
#https://dashboard.heroku.com/apps/cs50-web-project--1

import os
import requests
import json

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

#index page redirects to login page if user is not in session, or to librarry if user is in
@app.route("/", methods=["GET", "POST"])
def index():
    if "username" in session:
        return render_template("library.html", username = session["username"])
    return redirect(url_for("login"))

#login page adds user to session if successful
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

# logout just pops the user out of session and redirects tologin page
@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.pop("username", None)
    return render_template("login.html")

#registration form driver. Checks if user name already exists, but does not verify user input
# Can even create an empty user
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

#serches for books in the library. No check for user input, hence will search for even one char in the search string
#if no result found, returns "nothing found"
@app.route("/library", methods=["GET", "POST"])
def library():
    if request.method == "POST":
        isbn = request.form.get("isbn")
        title = request.form.get("title")
        author = request.form.get("author")
        if isbn:
            search_result = db.execute("SELECT * FROM books_t WHERE isbn LIKE :isbn", {"isbn" : '%'+isbn+'%'}).fetchall()
        if title:
            search_result = db.execute("SELECT * FROM books_t WHERE LOWER(title) LIKE :title", {"title" : '%'+title+'%'}).fetchall()
        if author:
            search_result = db.execute("SELECT * FROM books_t WHERE LOWER(author) LIKE :author", {"author" : '%'+author+'%'}).fetchall()
        if not len(search_result):
            return render_template("results.html", error = "Nothing found!")
        return render_template("results.html", search_result = search_result)

    return render_template("library.html", username = session["username"])

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

    #get book data from database
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

    #lets add a review
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

#API driver returns a json answer with data from database
@app.route("/api/<string:isbn>", methods=["GET"])
def api(isbn):
    book = db.execute("SELECT title, author, year, isbn "
    "FROM books_t "
    "WHERE isbn = :isbn ",
    {"isbn" : isbn}).fetchone()

    res = db.execute("SELECT COUNT(reviews_t.review) "
    "FROM reviews_t "
    "INNER JOIN books_t "
    "ON books_t.id = reviews_t.bid "
    "WHERE books_t.isbn = :isbn ",
    {"isbn" : isbn}).fetchone()

    if res is None:
        review_count = 0
    else:
        review_count = int(res[0])

    res = db.execute("SELECT AVG(reviews_t.review) OVER() "
    "FROM reviews_t "
    "INNER JOIN books_t "
    "ON books_t.id = reviews_t.bid "
    "WHERE books_t.isbn = :isbn ",
    {"isbn" : isbn}).fetchone()

    if res is None:
        average_score = 0
    else:
        average_score = int(res[0])

    #need to convert ResProxy object to list cause jsonify wouldn't take it as an argument
    book = list(book)
    return jsonify({
    "title": book[0],
    "author": book[1],
    "year": book[2],
    "isbn": book[3],
    "review_count": review_count,
    "average_score": average_score
    })
