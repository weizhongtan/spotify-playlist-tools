from flask import session

caches_folder = './.spotify_caches/'


def session_cache_path():
    return caches_folder + session.get('uuid')
