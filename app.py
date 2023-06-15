from flask import Flask, request, url_for, session, redirect, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time 
from time import gmtime, strftime
from credentials import CLIENT_ID, CLIENT_SECRET, SECRET_KEY
import os
import requests
from datetime import datetime


# Defining consts
TOKEN_CODE = "token_info"
MEDIUM_TERM = "medium_term"
SHORT_TERM = "short_term"
LONG_TERM = "long_term"

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=url_for("redirectPage",_external=True), 
        scope="user-top-read user-library-read"
    )

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['SESSION_COOKIE_NAME'] = 'Setlist Cookie'

@app.route('/')
def index():
    name = 'username'
    return render_template('index.html', title='Welcome', username=name)

@app.route('/login')
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/redirect')
def redirectPage():
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_CODE] = token_info    
    return redirect(url_for("getTracks", _external=True))

def get_token():
    token_info = session.get(TOKEN_CODE, None)
    if not token_info: 
        raise Exception("User not logged in")
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60 
    if is_expired: 
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info

def obtener_ciudad_usuario():
    response = requests.get('https://ipapi.co/json/')
    data = response.json()
    ciudad = data.get('city', 'London')
    pais = data.get('country_name', 'UK')
    return f"{ciudad}, {pais}"

@app.route('/getTracks')
def getTracks():
    try: 
        token_info = get_token()
    except Exception as e: 
        print("User not logged in")
        return redirect("/")
    sp = spotipy.Spotify(
        auth=token_info['access_token'],
    )

    current_user_name = sp.current_user()['display_name']
    ciudad_usuario = obtener_ciudad_usuario()

    short_term = sp.current_user_top_tracks(
        limit=23,
        offset=0,
        time_range=SHORT_TERM,
    )
    medium_term = sp.current_user_top_tracks(
        limit=23,
        offset=0,
        time_range=MEDIUM_TERM,
    )
    long_term = sp.current_user_top_tracks(
        limit=23,
        offset=0,
        time_range=LONG_TERM,
    )

    time_range = request.args.get('time_range')  # Obtener el valor del parámetro 'time_range' de la solicitud, si no se proporciona, usar SHORT_TERM
    
    top_tracks = sp.current_user_top_tracks(
        limit=23,  # Obtener 23 canciones
        offset=0,
        time_range=time_range,
    )
    
    top_tracks_songs = []  # Lista vacía para almacenar las canciones individuales
    
    # Obtener las canciones individuales de la lista de canciones principales
    for item in top_tracks['items']:
        # Realizar una solicitud a la API para obtener la información detallada de cada canción
        song_info = sp.track(item['id'])
        top_tracks_songs.append(song_info)

    if os.path.exists(".cache"): 
        os.remove(".cache")

    context = {
        'user_display_name': current_user_name,
        'ciudad': ciudad_usuario,
        'short_term': short_term,
        'medium_term': medium_term,
        'long_term': long_term,
        'top_tracks_songs': top_tracks_songs,
        'currentTime': datetime.now(),
        'get_day_suffix': get_day_suffix
    }

    return render_template('setlist.html', **context)

def get_day_suffix(day):
    if 4 <= day <= 20 or 24 <= day <= 30:
        return "th"
    else:
        return ["st", "nd", "rd"][day % 10 - 1]

@app.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
    if fmt:
        month_name = date.strftime('%B')
        day = date.day
        year = date.year
        day_suffix = get_day_suffix(day)
        formatted_date = f"{month_name} {day}{day_suffix}, {year}"
        return formatted_date
    return ""



@app.template_filter('mmss')
def _jinja2_filter_milliseconds(time, fmt=None):
    time = int(time / 1000)
    minutes = time // 60 
    seconds = time % 60 
    if seconds < 10: 
        return str(minutes) + ":0" + str(seconds)
    return str(minutes) + ":" + str(seconds)