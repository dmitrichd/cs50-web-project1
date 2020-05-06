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


@app.route("/", methods=["GET", "POST"])
def index():
    flights = db.execute("SELECT * FROM flights").fetchall()
    if request.method == "POST":
        origin = request.form.get("origin")
        destination = request.form.get("destination")
        duration = request.form.get("duration")
        db.execute("INSERT INTO flights (origin, destination, duration) VALUES (:origin, :destination, :duration)",
        {"origin":origin, "destination":destination, "duration":duration})
        db.commit()
        flash("Flight added!")
    flights = db.execute("SELECT * FROM flights").fetchall()
    return render_template("flights.html", flights = flights)

@app.route("/chosen_flight", methods=["POST"])
def chosen_flight():
    flights = db.execute("SELECT * FROM flights").fetchall()
    if request.method == "POST":
        chosen_flight = request.form.get("chosen_flight")
        chosen_flight = db.execute("SELECT * FROM flights WHERE (destination = :chosen_flight OR origin = :chosen_flight)",
        {"chosen_flight" :chosen_flight}).fetchall()
    return render_template("flights.html", flights = flights, chosen_flight = chosen_flight)
