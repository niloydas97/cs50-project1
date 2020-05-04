from io import TextIOWrapper
import csv
from flask import Flask, render_template, request, redirect, url_for, flash, session,  jsonify
from flask_session import Session
from helpers import login_required
from passlib.handlers.sha2_crypt import sha512_crypt
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests  # for goodreads API
import json
import os

app = Flask (__name__)
# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = "3p3200170"
Session


# Set up database
engine = create_engine ("postgres://lwqicgjlaxxgrp:6a496476fac6d1caed3b8eb614368d3b8376905c523a1470733895b7dc1ab046@ec2-52-202-22-140.compute-1.amazonaws.com:5432/df3jj5abngsvgu")
db = scoped_session (sessionmaker (bind=engine))

#
# # Check for environment variable
# if not os.getenv("DATABASE_URL"):
#     raise RuntimeError("DATABASE_URL is not set")
#
# # Set up database
# engine = create_engine(os.getenv("DATABASE_URL"))
# db = scoped_session(sessionmaker(bind=engine))


# Home
@app.route ("/", methods=["GET","POST"])
def index():
    if 'loggedin' not in session:
        return redirect (url_for ('login'))
    if request.method=='POST'and request.form['getbook'] != '':
        data = (request.form['getbook'])

        books = db.execute("SELECT isbn, title, author, year FROM books WHERE \
                        isbn LIKE :title OR \
                        title LIKE :title OR \
                        author LIKE :title LIMIT 15 ", {'title': '%' + data + '%'}).fetchall()
        return render_template('search.html', books = books)
    return render_template ("index.html")



# Signup
@app.route ("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("user")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm = request.form.get("confirm")
        secure_pass = sha512_crypt.encrypt(str(password))
        if password == confirm:
            username_db  = db.execute('SELECT * FROM Users WHERE username = :username', {"username": username}).fetchone()
            if username_db:
                flash("UserName already exist!", "danger")
            else:
               db.execute("insert into users(username, email, password) VALUES (:username,:email,:password)",
                        {"username": username, "email": email, "password": secure_pass})
               db.commit()
               flash("You have Registered Successfully", "success")
               return redirect (url_for ('login'))
        else:
            flash ("Password Did Not Match", "danger")
            return render_template ("signup.html")

    return render_template ("signup.html")


# login

@app.route ("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get ("username")
        password = request.form.get ("password")
        userdata = db.execute ("select username from users where username=:username",
                               {"username": username}).fetchone ()
        passdata = db.execute ("select password from users where username=:username",
                               {"username": username}).fetchone ()
        if userdata is None:
            flash ("username not found", "warning")
            return render_template ("login.html")

        else:
            for pass_data in passdata:
                if sha512_crypt.verify (password, pass_data):
                    session['loggedin'] = True
                    rows = db.execute("SELECT * FROM users WHERE username = :username",
                                      {"username": username})


                    result = rows.fetchone()
                    # Remember which user has logged in
                    session["id"] = result[0]
                    session["username"] = result[1]


                    flash ("login success", "success")
                    return redirect (url_for ('index'))
                else:
                    flash ("Incorrect Password", "danger")
                    return redirect (url_for ('login'))
    return render_template ("login.html")

# import CSV
@app.route ("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
       # f = pd.read_csv(request.files.get('files'))
        csv_file = request.files['files']
        csv_file = TextIOWrapper(csv_file, encoding='utf-8')
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader)
        for isbn, title, author, year in csv_reader:
             db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                     {"isbn": isbn, "title": title, "author": author, "year": year})
             db.commit()
        flash("csv file has import successfully", "success")

    return render_template ("upload.html")

# Search
@app.route("/search", methods=["GET","POST"])
def search():

    return render_template("search.html")

# Book Info
@app.route("/book/<isbn>", methods=["GET","POST"])
#@login_required
def book(isbn):

        """ Save user review and load same page with reviews updated."""
        if 'loggedin' not in session:
            return redirect (url_for ('login'))

        if request.method == "POST":

            # Save current user info
            currentUser = session["id"]

            # Fetch form data
            rating = request.form.get("rating")
            review = request.form.get("review")

            # Search book_id by ISBN
            row = db.execute("SELECT book_id FROM books WHERE isbn = :isbn",
                             {"isbn": isbn})

            # Save id into variable
            bookId = row.fetchone() # (id,)
            bookId = bookId[0]

            # Check for user submission (ONLY 1 review/user allowed per book)
            row2 = db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND book_id = :book_id",
                              {"user_id": currentUser,
                               "book_id": bookId})

            # A review already exists
            if row2.rowcount == 1:

                flash('You already submitted a review for this book', 'warning')
                return redirect("/book/" + isbn)

            # Convert to save into DB
            rating = int(rating)

            db.execute("INSERT INTO reviews (user_id, book_id, review, rating) VALUES \
                    (:user_id, :book_id, :review, :rating)",
                       {"user_id": currentUser,
                        "book_id": bookId,
                        "review": review,
                        "rating": rating})

            # Commit transactions to DB and close the connection
            db.commit()

            flash('Review submitted!', 'info')

            return redirect("/book/" + isbn)

        # Take the book ISBN and redirect to his page (GET)
        else:

            row = db.execute("SELECT isbn, title, author, year FROM books WHERE \
                        isbn = :isbn",
                             {"isbn": isbn})

            bookInfo = row.fetchall()

            """ GOODREADS reviews """

            # Read API key from env variable


            # Query the api with key and ISBN as parameters
            query = requests.get("https://www.goodreads.com/book/review_counts.json",
                                 params={"key":'O7MUidct1MXle6srvdCzNA', "isbns": isbn})

            # Convert the response to JSON
            response = query.json()

            # "Clean" the JSON before passing it to the bookInfo list
            response = response['books'][0]
            dbdata =[]


            # Append it as the second element on the list. [1]
            bookInfo.append(response)

            """ Users reviews """

            # Search book_id by ISBN
            row = db.execute("SELECT book_id FROM books WHERE isbn = :isbn",
                             {"isbn": isbn})

            # Save id into variable
            book = row.fetchone() # (id,)
            book = book[0]

            # Fetch book reviews
            # Date formatting (https://www.postgresql.org/docs/9.1/functions-formatting.html)
            results = db.execute("SELECT users.username, review, rating \
                            FROM users \
                            INNER JOIN reviews \
                            ON users.id = reviews.user_id \
                            WHERE book_id = :book ",
                             {"book": book})

            reviews = results.fetchall()




        return render_template("book.html", bookInfo=bookInfo, reviews=reviews)

@app.route("/api/<isbn>", methods=['GET'])
def api_call(isbn):

    # COUNT returns rowcount
    # SUM returns sum selected cells' values
    # INNER JOIN associates books with reviews tables

    row = db.execute("SELECT title, author, year, isbn, \
                    COUNT(reviews.id) as review_count, \
                    AVG(reviews.rating) as average_score \
                    FROM books \
                    INNER JOIN reviews \
                    ON books.book_id = reviews.book_id \
                    WHERE isbn = :isbn \
                    GROUP BY title, author, year, isbn",
                     {"isbn": isbn})

    # Error checking
    if row.rowcount != 1:
        return jsonify({"Error": "Invalid book ISBN"}), 422

    # Fetch result from RowProxy
    tmp = row.fetchone()

    # Convert to dict
    result = dict(tmp.items())

    # Round Avg Score to 2 decimal. This returns a string which does not meet the requirement.
    # https://floating-point-gui.de/languages/python/
    result['average_score'] = float('%.2f'%(result['average_score']))

    return jsonify(result)


# LogOut
@app.route ("/logout")
def logout():
    session.clear ()
    flash ("You are now logged out", "success")
    return redirect (url_for ('login'))


if __name__ == "__main__":
    app.run (debug=True)
