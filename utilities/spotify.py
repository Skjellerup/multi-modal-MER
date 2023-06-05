import pandas as pd
import time
from requests.exceptions import HTTPError
import requests, json, csv 
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# handling token expiration
## OAuth 
def create_spotify(client_id, client_secret):
    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        cache_path= 'data/spotify_token.txt',
        redirect_uri='http://localhost:8080/callback'
    )

    spotify = spotipy.Spotify(auth_manager=auth_manager)

    return auth_manager, spotify

def refresh_access_token(auth_manager):
    current_time = int(time.time())
    token_info = auth_manager.get_cached_token()
    
    if token_info and 'expires_at' in token_info and 'refresh_token' in token_info:
        expires_at = token_info['expires_at']
        refresh_token = token_info['refresh_token']
        print(expires_at, current_time, expires_at - current_time)

        # refresh token if within 1 minute of expiration
        new_token_info = auth_manager.refresh_access_token(refresh_token)
        auth_manager.cache_token(new_token_info)
        return True
    
    return False


def get_song_id(song_name, artist_name, max_retries=5, retry_interval=10, write_interval=20, csv_file='data/song_ids.csv', client_id="4bf77127e0db4f4cab65d5ef9e294807", client_secret="08bc54c2e23f475eb8ad69b20326ad37"):
    auth_manager, _ = create_spotify(client_id, client_secret) 
    print('auth_manager created')  
    auth_token = auth_manager.get_access_token()
    print('auth_token created')
    retries = 0
    song_ids = []
    counter = 0
    BASE_URL = 'https://api.spotify.com/v1/'
    headers = {
        'Authorization': 'Bearer {token}'.format(token=auth_token['access_token'])
    }
    while retries < max_retries:
        try:
            if auth_manager.get_cached_token()['expires_in'] <= 60:
                print('Refreshing token...')
                auth_token = auth_manager.get_cached_token()['access_token']
                print('Token refreshed!')
        except Exception as e:
            print('Error refreshing token:', e)

        
        params = {"q": artist_name, "track": song_name, "type": "track"}
        final = BASE_URL + 'search?'   
        results = requests.get(final, headers=headers, params=params)

        if results.status_code == 200:
            data = json.loads(results.text)
        elif results.status_code == 429:
            print("HTTP 429 error")
            if 'Retry-After' in results.headers:
                retry_interval = int(results.headers['Retry-After'])
                print(f"Retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
                retries += 1
                continue
            else:
                print("Retry-After header not found. Using default retry interval.")
                time.sleep(retry_interval)
                retries += 1
                continue
        
        if data and 'tracks' in data and data['tracks']['items']:
            song_ids.append(data['tracks']['items'][0]['id'])
            counter += 1

            if counter == write_interval:
                print(counter, "song_ids written to file")
                with open(csv_file, 'a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(song_ids)
                    song_ids = []
                counter = 0
            
            if not write_interval or len(song_ids) % write_interval != 0:
                break

    if not song_ids:
        song_ids = ["DUMMY: NO MATCH FOUND"]

    if csv_file and song_ids:
        with open(csv_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(song_ids)

    return song_ids

import requests
import json
import time

def get_song_features(song_ids, max_retries=5, client_id="4bf77127e0db4f4cab65d5ef9e294807", client_secret="08bc54c2e23f475eb8ad69b20326ad37"):
    auth_manager, spotify = create_spotify(client_id, client_secret) 
    print('auth_manager created')  
    auth_token = auth_manager.get_access_token()
    print('auth_token created')
    # bulk request for song features
    BASE_URL = 'https://api.spotify.com/v1/'
    headers = {
        'Authorization': 'Bearer {token}'.format(token=auth_token['access_token'])
    }

    try:
        # Iterate over each chunk of song IDs
        if len(song_ids) % 40 == 0:
            song_id_chunks = [song_ids[i:i+40] for i in range(0, len(song_ids), 40)]
        else:
            song_id_chunks = [song_ids]

        song_features = []
        song_names = []
        artist_names = []

        for chunk in song_id_chunks:
            print(chunk)
            chunk = set(chunk)
            print(chunk)
            retries = 0

            while retries < max_retries:
                try:
                    if auth_manager.get_cached_token()['expires_in'] <= 60:
                        print('Refreshing token...')
                        auth_token = auth_manager.get_cached_token()['access_token']
                        print('Token refreshed!')
                except Exception as e:
                    print('Error refreshing token:', e)

                # Request the audio features for the chunk of song IDs
                try:
                    # build api request from scratch
                    feature_request = BASE_URL + 'audio-features?ids=' + ','.join(chunk)
                    artist_request = BASE_URL + 'tracks?ids=' + ','.join(chunk)

                    # make api request for song features
                    try:
                        results_features = requests.get(feature_request, headers=headers)
                        print('feature: ',results_features.status_code)
                        if results_features.status_code == 200:
                            feature_data = json.loads(results_features.text)
                            song_features.extend(feature_data['audio_features'])
                            print(len(song_features))
                        elif results_features.status_code == 429:
                            print("HTTP 429 error")
                            if 'Retry-After' in results_features.headers:
                                retry_interval = int(results_features.headers['Retry-After'])
                                print(f"Retrying in {retry_interval} seconds...")
                                time.sleep(retry_interval)
                                retries += 1
                                continue
                    except Exception as e:
                        print("Error getting song features:", e)
                        retries += 1

                    # make api request for artist names
                    try:
                        results_artists = requests.get(artist_request, headers=headers)
                        print('artist: ',results_artists.status_code)
                        if results_artists.status_code == 200:
                            artist_data = json.loads(results_artists.text)
                            # add song names to list 
                            song_names.extend([song['name'] for song in artist_data['tracks']])
                            artist_names.extend([artist['artists'][0]['name'] for artist in artist_data['tracks']])
                            print(len(artist_names))
                        elif results_artists.status_code == 429:
                            print("HTTP 429 error")
                            if 'Retry-After' in results_artists.headers:
                                retry_interval = int(results_artists.headers['Retry-After'])
                                print(f"Retrying in {retry_interval} seconds...")
                                time.sleep(retry_interval)
                                retries += 1
                                continue
                    except Exception as e:
                        print("Error getting artist names:", e)
                        retries += 1

                    break
                except Exception as e:
                    print("Error getting song features:", e)
                    retries += 1

        print(list(zip(artist_names, song_features, song_names)))
        return list(zip(artist_names, song_features, song_names))
    except Exception as e:
        print("Error getting song features:", e)
     


def create_song_df(song_names, artist_name, x=50):
     

    print(len(song_names))
    while True:
        # Get list of song IDs
        song_ids = list(set([get_song_id(song_name, artist_name)[0] for song_name, artist_name in zip(song_names, artist_name)]))
        # Get list of song features
        song_artist_features = get_song_features(song_ids)

        song_artist = [song_artist[0] for song_artist in song_artist_features]
        song_features = [song_artist[1] for song_artist in song_artist_features]
        song_names = [song_artist[2] for song_artist in song_artist_features]

        song_data = []

        for i in range(len(song_ids)):
            if song_names[i] == "DUMMY: NO MATCH FOUND":
                print("Dummy song found. Skipping...")
                continue
            try:
                data = {
                    "name": song_names[i],
                    "id": song_ids[i],
                    "artist": song_artist[i],
                    "danceability": song_features[i]["danceability"],
                    "energy": song_features[i]["energy"],
                    "key": song_features[i]["key"],
                    "loudness": song_features[i]["loudness"],
                    "mode": song_features[i]["mode"],
                    "speechiness": song_features[i]["speechiness"],
                    "acousticness": song_features[i]["acousticness"],
                    "instrumentalness": song_features[i]["instrumentalness"],
                    "liveness": song_features[i]["liveness"],
                    "valence": song_features[i]["valence"],
                    "tempo": song_features[i]["tempo"],
                    "duration_ms": song_features[i]["duration_ms"],
                    "time_signature": song_features[i]["time_signature"]
                }
                song_data.append(data)
            except KeyError as ke:
                print("KeyError: ", song_names[i])

            # dump data every x iteration
            if len(song_data) % x == 0:
                with open('multimodal.json', "a") as f:
                    json.dump(song_data, f)

                song_data = []
                print(f"Wrote {len(song_data)} datasets")

            # Write remaining datasets to file
            elif i == len(song_names) - 1:
                with open('multimodal.json', "a") as f:
                    json.dump(song_data, f)
                print(f"Wrote {len(song_data)} datasets")
                song_data = []

            else:
                continue

        return "succeed"





