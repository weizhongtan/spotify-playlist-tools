from flask import Flask, url_for
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

redirectURL = "http://localhost:8080/callback/"
state = "foobar"


@app.route("/")
def index():
    return f'<h1>this is the index</h1><a href={url_for("auth")}>go to auth</a>'


@app.route("/auth")
def auth():
    return '<h1>this is auth</h1>'
