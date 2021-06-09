from flask import Flask, url_for, redirect, render_template, request, make_response, session
from flask_session import Session
from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import uuid

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SERVER_SECRET')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'

Session(app)

caches_folder = './.spotify_caches/'
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)


def session_cache_path():
    return caches_folder + session.get('uuid')


@app.route("/")
def index():
    if not session.get('uuid'):
        # Step 1. Visitor is unknown, give random ID
        session['uuid'] = str(uuid.uuid4())

    cache_handler = spotipy.cache_handler.CacheFileHandler(
        cache_path=session_cache_path()
    )
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        scope='user-read-private,playlist-read-private',
        cache_handler=cache_handler,
        show_dialog=True
    )

    if request.args.get("code"):
        # Step 3. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        return redirect(url_for('index'))

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        # Step 2. Display sign in link when no token
        return render_template('index.html')

    # Step 4. Signed in, display data
    sp = spotipy.Spotify(auth_manager=auth_manager)
    username = sp.me()['display_name']
    return render_template('index.html', username=username)


@app.route("/login")
def login():
    cache_handler = spotipy.cache_handler.CacheFileHandler(
        cache_path=session_cache_path()
    )
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    resp = redirect(auth_manager.get_authorize_url())
    return resp


@app.route("/logout")
def logout():
    try:
        # Remove the CACHE file (.cache-test) so that a new user can authorize.
        os.remove(session_cache_path())
        session.clear()
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))
    return redirect(url_for('index'))
