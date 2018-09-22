#DATABASE_URL: postgres://iatnvhyndrywzs:cad16ec57142e7c71475d608cc16e668e649222ea4607224ba70f6a35ec37435@ec2-54-225-97-112.compute-1.amazonaws.com:5432/dbsa319dkemsq3

import os

import util

from flask import Flask, session, render_template, request
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

@app.route("/home", methods=["POST"])
def home():
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
    session["user_id"]=user.id;
    #some example books
    samples=db.execute("SELECT * FROM books ORDER BY RANDOM() LIMIT 15").fetchall()
    return render_template("home.htm", user=user, samples=samples, page_title="Recent Books")

@app.route("/register")
def register():
    return render_template("register.htm")

@app.route("/registered", methods=["POST"])
def registered(): 
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
    return "Not implemented yet"


@app.route("/search", methods=["GET"])
def search():
    book_title=request.form.get("searchtxt")
    books=db.execute("SELECT * FROM books WHERE title=:book_title",
    {"book_title": book_title}).fetchall()
    user=db.execute("SELECT * FROM users WHERE id=:id",
    {"id":session["user_id"]}).fetchone()
    return render_template("home.htm", samples=books, user=user, page_title="Search results:")

@app.route("/logout")
def logout():
    session["user_id"]=None;
    return render_template("index.htm")
