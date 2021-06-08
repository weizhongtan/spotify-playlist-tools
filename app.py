from flask import Flask, url_for, redirect, render_template, request, make_response
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SERVER_SECRET')

redirectURL = "http://localhost:8080/callback/"
state = "foobar"


@app.route("/")
def index():
    is_logged_in = request.cookies.get('is_logged_in') == 'true'
    print('is_logged_in:', is_logged_in)
    return render_template('index.html', name='wzt', is_logged_in=is_logged_in)


@app.route("/auth")
def auth():
    resp = redirect(url_for('index'))
    resp.set_cookie('is_logged_in', 'true')
    return resp


@app.route("/logout")
def logout():
    resp = redirect(url_for('index'))
    resp.set_cookie('is_logged_in', 'false')
    return resp
