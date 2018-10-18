#DATABASE_URL: postgres://iatnvhyndrywzs:cad16ec57142e7c71475d608cc16e668e649222ea4607224ba70f6a35ec37435@ec2-54-225-97-112.compute-1.amazonaws.com:5432/dbsa319dkemsq3

import os
import requests


import util

from flask import Flask, session, render_template, request, jsonify, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
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


@app.route("/")
def index():
    return render_template("index.htm")

@app.route("/login", methods=["POST"])
def login():
    '''getting into homepage'''
    #getting and verifying the form fields
    usr = request.form.get("nametxt")
    pswd = request.form.get("pswdtxt")
    if usr == None or pswd == None:
        return render_template("error.htm", message="Invalid username or password")
    #encrypting password with sha256
    pswd = util.encrypt(pswd)
    user=db.execute("SELECT * FROM users WHERE usr=:usr AND pswd=:pswd", {"usr":usr, "pswd":pswd}).fetchone()
    if user is None:
        return render_template("error.htm", message="Invalid username or password")
    
    #saving the session
    session["user_id"]=user.id
    return redirect(url_for("home"))

@app.route("/home")
def home():
    #if the user is not logged in, will redirect to home
    try:
        session["user_id"]
    except:
        return redirect(url_for("index"))
    """displaying home"""
    #some example books
    samples = db.execute(
        "SELECT * FROM books ORDER BY RANDOM() LIMIT 15").fetchall()
    user=db.execute("SELECT * FROM users WHERE id=:id", {"id":session["user_id"]}).fetchone()
    return render_template("home.htm", samples=samples, user=user)        

@app.route("/sign_up")
def sign_up():
    """displaying sign up form"""
    return render_template("register.htm")

@app.route("/register", methods=["POST"])
def register(): 
    '''Putting new user into database'''
    #getting and verifying the form fields 
    usr=request.form.get("nametxt")
    pswd=request.form.get("pswdtxt")
    if usr == None or pswd == None:
        return render_template("error.htm", message="Internal error on registration")
    #encrypting password with sha256
    pswd=util.encrypt(pswd)
    #committing into table
    db.execute("INSERT INTO users(usr, pswd) VALUES (:usr, :pswd)",
    {"usr":usr, "pswd":pswd})
    db.commit()

    return render_template("success.htm", message="You're successfully registered")    
    
@app.route("/comment/<int:book_id>")
def comment(book_id):
    try:
        session["user_id"]
    except:
        return redirect(url_for("index"))
    """single book detail view"""
    #getting the book
    book = db.execute("SELECT * FROM books WHERE id=:id",
    {"id": book_id}).fetchone()
    if book is None:
        return render_template("error.htm", message="No Book was found")
    #getting the last 4 reviews joining with the user name        
    reviews = db.execute("SELECT comment, rate, usr FROM reviews JOIN users ON users.id=user_id WHERE book_id=:book_id LIMIT(4)",
    {"book_id": book_id}).fetchall()
    #getting the average stars rate
    avg_rate=0
    if len(reviews) !=0:
        for rev in reviews:
            avg_rate+=rev.rate
        avg_rate=avg_rate/len(reviews)
    #getting the user for session view
    user = db.execute("SELECT * FROM users WHERE id=:id",
    {"id": session["user_id"]}).fetchone()
    #getting info from goodreads api, only the average rating
    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": "dwdsoTU7TSH21w2VveT9Q", "isbns": book.isbn})        
    gdr_rate = (res.json()["books"][0]["average_rating"])
    #return
    return render_template("comment.htm", user=user, book=book, reviews=reviews, avg_rate=avg_rate, gdr_rate=gdr_rate)


@app.route("/search", methods=["GET"])
def search():
    try:
        session["user_id"]
    except:
        return redirect(url_for("index"))
    """I've decided to reuse the home template for searching tasks, limiting the list only to the searched ones"""
    book_title = request.args.get("searchtxt")
    if book_title == None:
        return render_template("error.htm", message="An internal error has ocurred")
    #looking for the books, uncase sensitive
    books=db.execute("SELECT * FROM books WHERE LOWER(title)=LOWER(:book_title)",
    {"book_title": book_title}).fetchall()
    #getting the user for session display
    user=db.execute("SELECT * FROM users WHERE id=:id",
    {"id":session["user_id"]}).fetchone()
    
    return render_template("home.htm", samples=books, user=user, page_title="Search results:")

@app.route("/logout")
def logout():
    #deleting the session key for logout
    if "user_id" in session:
        del session["user_id"]
    return render_template("index.htm")

@app.route("/commented/<int:book_id>", methods=["POST"])
def commented(book_id):
    #insert new comment
    comm=request.form.get("commtxt")
    rate=request.form.get("starsrate")
    db.execute("INSERT INTO reviews(comment, rate, book_id, user_id) VALUES (:comm, :rate, :book_id, :user_id)",
    {"comm": comm, "rate":rate, "book_id":book_id, "user_id": session["user_id"]})
    db.commit()
    return redirect(url_for("comment", book_id=book_id))

@app.route("/api/books/<int:book_id>")
def book_api(book_id):
    #getting the book
    book = db.execute("SELECT * FROM books WHERE id=:id", {"id":book_id}).fetchone()
    if book is None:
        return jsonify({"Error 404": "This book does not exists"})
    #getting reviews for average rate
    reviews = db.execute("SELECT rate FROM reviews WHERE book_id=:book_id LIMIT(4)", {"book_id":book.id}).fetchall()
    avg_rate = 0
    #getting rate if exists
    if len(reviews) != 0:
        for rev in reviews:
            avg_rate += rev.rate
        avg_rate = avg_rate/len(reviews)
    #if rate is not avaliable will return a JSON without rate
    if avg_rate == 0:
        return jsonify({
            "ISBNS":book.isbn,
            "Title": book.title,
            "Author": book.author,
            "Publication Year": book.year
            })
    return jsonify({
        "ISBNS": book.isbn,
        "Title": book.title,
        "Author": book.author,
        "Publication Year": book.year,
        "Average users rating": avg_rate
    })
