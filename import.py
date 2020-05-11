#This is implementation of Project 1 CS50 Web Harvard database data upload program
# needs half an hour to write 50K rows to heroku database

import os
from flask import Flask, session, render_template, request
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import csv

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route('/')

def main():
    db.execute("DROP TABLE IF EXISTS books_t")
    db.execute("CREATE TABLE books_t ("
    "id SERIAL PRIMARY KEY,"
    "isbn VARCHAR NOT NULL,"
    "title VARCHAR NOT NULL,"
    "author VARCHAR NOT NULL,"
    "year INTEGER NOT NULL)")
    db.commit()

    f = open("books.csv")
    reader = csv.DictReader(f)
    for line in reader:
        isbn = line["isbn"]
        title = line["title"]
        author = line["author"]
        year = line["year"]
        db.execute("INSERT INTO books_t (isbn, title, author, year) VALUES"
        "(:isbn, :title, :author, :year)",
        {"isbn" : isbn, "title" : title, "author" : author, "year" : year})
        db.commit()
    return "<h1>Job Done!!!</h1>"

if __name__ == "__main__":
    main()
