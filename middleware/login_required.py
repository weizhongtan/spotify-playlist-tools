from functools import wraps
from flask import redirect, url_for
import spotipy
from spotipy.cache_handler import CacheFileHandler
from spotipy.oauth2 import SpotifyOAuth
from lib import session_cache_path


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        cache_handler = CacheFileHandler(
            cache_path=session_cache_path()
        )
        auth_manager = SpotifyOAuth(cache_handler=cache_handler)
        if not auth_manager.validate_token(cache_handler.get_cached_token()):
            return redirect(url_for('index'))

        sp = spotipy.Spotify(auth_manager=auth_manager)

        return f(sp, *args, **kwargs)
    return decorated_function
