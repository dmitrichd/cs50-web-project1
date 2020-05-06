import os

from flask import Flask, session, render_template, request, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.sql import text
from sqlalchemy.orm import scoped_session, sessionmaker

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

session["logged_in"] = False

@app.route("/", methods=["GET", "POST"])
    def index():
        if session["logged_in"] == True:
            return redirect(url_for("library"))
        else:
            return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
    def login():
        error = False
        if request.method == "POST":
            name = request.form.get("name")
            password = request.form.get("password")
            if db.execute("SELECT username, password FROM user_t WHERE username = :name AND password = :password",
            {"name" : name, "password" : password}):
                session["logged_in"] = True
                return redirect(url_for("library"))
            else:
                error = True
                return render_template("login.html", error = error)
        return render_template("login.html")

@app.route("/library", methods=["POST"])
    def library():
        return

@app.route("/showbook>", methods=["POST"])
    def showbook():
        return
