from flask import Flask, render_template, request, session
from flask_session import Session

app = Flask(__name__)

notes = []

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route('/', methods=["POST", "GET"])

def hello():
    if request.method == "POST":
        name = request.form.get("name")
        return render_template('hello.html', name = name)
    return render_template('hello.html')

@app.route('/links', methods=["POST", "GET"])

def links():
    if session.get("notes") is None:
        session["notes"] = []
    if request.method == "POST":
        note = request.form.get("note")
        session["notes"].append(note)
    return render_template('links.html', notes = session["notes"])
