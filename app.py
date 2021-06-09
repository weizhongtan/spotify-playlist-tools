from flask import Flask, url_for, redirect, render_template, request, make_response, session, jsonify
from flask_session import Session
from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import CacheFileHandler
import uuid
import re
from functools import lru_cache
from middleware.login_required import login_required
from lib import caches_folder, session_cache_path

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SERVER_SECRET')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)


@app.route("/")
def index():
    if not session.get('uuid'):
        # Step 1. Visitor is unknown, give random ID
        session['uuid'] = str(uuid.uuid4())

    cache_handler = CacheFileHandler(
        cache_path=session_cache_path()
    )
    auth_manager = SpotifyOAuth(
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
    cache_handler = CacheFileHandler(
        cache_path=session_cache_path()
    )
    auth_manager = SpotifyOAuth(cache_handler=cache_handler)
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


@lru_cache(maxsize=50)
def user_playlist_tracks(cache_path, user_id, playlist_id):
    cache_handler = CacheFileHandler(
        cache_path=cache_path
    )
    auth_manager = SpotifyOAuth(cache_handler=cache_handler)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    print('getting tracks for: ', playlist_id)
    return sp.user_playlist_tracks(user_id, playlist_id=playlist_id)['items']


# API endpoints
@app.route('/search-playlists')
@login_required
def playlists(sp):
    id = sp.me()['id']
    playlists = sp.user_playlists(id)['items']

    pattern = re.compile(request.args.get('track_name'), flags=re.IGNORECASE)

    matched_tracks = []

    for playlist in playlists:
        tracks = user_playlist_tracks(session_cache_path(), id, playlist['id'])
        raw_tracks = [track['track'] for track in tracks]
        for raw_track in raw_tracks:
            if raw_track != None and 'name' in raw_track and raw_track['name'] != None:
                track_name = raw_track['name']
                if pattern.search(track_name):
                    track = {
                        'name': track_name,
                        'artists': [artist['name'] for artist in raw_track['artists']]
                    }
                    matched_tracks.append(track)

    return render_template('results.html', tracks=matched_tracks, headings=['track', 'artists'])


if __name__ == '__main__':
    print('running in prod!')
    app.run(
        threaded=True,
        port=int(os.environ.get(
            "PORT",
            os.environ.get("SPOTIPY_REDIRECT_URI", 8080).split(":")[-1])
        )
    )
