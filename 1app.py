from flask import Flask, render_template
app = Flask(__name__)

@app.route('/')
@app.route('/<string:username>')

def hello(username = None):
    return render_template('hello.html', name = username)
