from flask import Flask, url_for, redirect, render_template, request, make_response
from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SERVER_SECRET')

redirect_uri = "http://localhost:5000/callback/"
state = "foobar"

auth_manager = SpotifyOAuth(
    client_id=os.getenv('CLIENT_ID'),
    client_secret=os.getenv('CLIENT_SECRET'),
    redirect_uri=redirect_uri,
    scope="user-read-private,playlist-read-private"
)


@app.route("/")
def index():
    sp = spotipy.Spotify(auth_manager=auth_manager)
    username = sp.me()['display_name']
    return render_template('index.html', username=username)


@app.route("/login")
def login():
    resp = redirect(auth_manager.get_authorize_url())
    return resp


@app.route("/logout")
def logout():
    resp = redirect(url_for('index'))
    resp.set_cookie('is_logged_in', 'false')
    return resp


@app.route("/callback/")
def callback():
    auth_manager.get_access_token(code=request.args.get('code'))
    return redirect(url_for('index'))
