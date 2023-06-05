from rapidfuzz import process
import json

# Genius api wrapper 
def get_lyrics(genius, query_list):
    song_array = []
    lyrics_array = []
    for artist, song in query_list:    
        try:
            song = genius.search_song(song, artist)
            print("Server response received for", song.title, "by", song.artist)
            song_array.append(song.title)
            lyrics_array.append(song.lyrics)
            
        except:
            print("Error searching for song:", song, "by", artist)
            # Append empty string to lyrics array
            lyrics_array.append("DUMMY: NO MATCH FOUND")
            song_array.append("DUMMY: NO MATCH FOUND")
            continue
    return song_array, lyrics_array

# Genius api wrapper 
def genius_wrapper(genius, query_list, x=3000):
    song_dict = {}
    response_counter = 0
    failure_counter = 0
    for artist, song in query_list:    
        try:
            song = genius.search_song(song, artist)
            response_counter += 1
            if response_counter % 100 == 0:
                print(f"Response received for {response_counter} songs")
            
            song_dict[f"{song.artist}_{song.title}"] = [song.lyrics]
            

            # Write to file every X requests
            if response_counter % x == 0:
                with open("lyrics.json", "a") as f:
                    json.dump(song_dict, f)
                    f.write("\n")
                song_dict = {}
            
        except:
            failure_counter += 1
            if failure_counter % 100 == 0:
                print(f"No match found for {failure_counter} songs")
            # Append empty string to lyrics array
            song_dict[f"DUMMY_{failure_counter}"] = ["NO MATCH FOUND"]
            
    # Write remaining data to file
    with open("lyrics.json", "a") as f:
        json.dump(song_dict, f)
            
    return song_dict

# Create rapidfuzz function to match song names
def fuzzy_match(row, song_df, threshold=80):
    name, artist = row["name"], row["artist"]
    best_match, score, index = process.extractOne((name, artist), song_df[["name", "artist"]].apply(tuple, axis=1))
    if score >= threshold:
        return index
    else:
        return None
