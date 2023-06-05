import pandas as pd
import os.path


def load_deezer_data(dir_paths, cols):
    """Load data from deezer dataset"""
    dfs = []
    for dir in dir_paths:
        for file in os.listdir(dir):
            if file.endswith(".csv"):
                dfs.append(pd.read_csv(os.path.join(dir, file), usecols=cols))
    
    final = pd.concat(dfs)
    
    return final.rename(columns={"track_name": "name", "artist_name": "artist"})
