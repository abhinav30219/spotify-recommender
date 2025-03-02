# recommender.py
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st
import numpy as np
from typing import Dict, List, Tuple, Union
from datetime import datetime

# Constants
spotify_data = pd.read_csv("sampled_spotify_songs.csv")
similarity_matrix = np.load("similarity_matrix.npy")

# Map era preferences to year ranges
ERA_RANGES = {
    "60s & 70s": (1960, 1979),
    "80s": (1980, 1989),
    "90s": (1990, 1999),
    "2000s": (2000, 2009),
    "2010s": (2010, 2019),
    "Latest": (2020, datetime.now().year)
}

# Store user ratings in memory
user_ratings: Dict[str, int] = {}

def adjust_similarity_scores(song: str, base_similarities: np.ndarray) -> np.ndarray:
    """Adjust similarity scores based on user ratings."""
    adjusted_scores = base_similarities.copy()
    
    # Get the indices of rated songs
    for rated_song, rating in user_ratings.items():
        rated_idx = find_index_from_title(rated_song)
        if rated_idx is not None:
            # Calculate rating weight (-1 to 1)
            # 1: rating of 5
            # 0.5: rating of 4
            # 0: rating of 3
            # -0.5: rating of 2
            # -1: rating of 1
            rating_weight = (rating - 3) / 2
            
            # Adjust similarities based on rating weight
            similar_songs = similarity_matrix[rated_idx]
            adjusted_scores += similar_songs * rating_weight * 0.5  # 0.5 to dampen the effect

    return adjusted_scores

def add_rating(song: str, rating: int) -> None:
    """Add or update a song rating."""
    if 1 <= rating <= 5:
        # Find the original song name since the displayed name is under 'Song' column
        song_idx = find_index_from_title(song)
        if song_idx is not None:
            original_name = spotify_data.loc[song_idx, "name"]
            user_ratings[original_name] = rating

def find_title_from_index(index):
    """Finds the song title based on its index."""
    try:
        return spotify_data.loc[index, "name"]
    except IndexError:
        return None

def find_index_from_title(title):
    """Finds the song index based on its title."""
    indices = spotify_data[spotify_data['name'] == title].index
    if len(indices) == 0:
        return None
    return indices[0]

#################################################################
# Popularity-based Recommendation
#################################################################
def most_popular_songs(data, num_songs):
    """Returns the top 'num_songs' most popular songs."""
    sorted_data = data.sort_values('popularity', ascending=False)
    result = sorted_data[["name", "artists", "popularity"]].head(num_songs)
    # Rename columns to match content-based recommendations
    result.rename(columns={
        "name": "Song",
        "artists": "Artist",
        "popularity": "Popularity"
    }, inplace=True)
    return result

#################################################################
# Content-Based Recommendation
#################################################################
def k_largest_indices(sim_list, K):
    """Returns the indices of the top K similar songs."""
    similar_songs = list(enumerate(sim_list))
    sorted_similar_songs = sorted(similar_songs, key=lambda x: x[1], reverse=True)[1:]  # Exclude self
    similar_songs_indices = [x[0] for x in sorted_similar_songs[:K]]
    return similar_songs_indices

def k_most_similar_songs(song: str, K: int) -> pd.DataFrame:
    """Returns the top K songs similar to the given song, considering user ratings."""
    song_index = find_index_from_title(song)
    if song_index is None:
        return pd.DataFrame({"Error": [f"Song '{song}' not found in the dataset."]})

    # Get base similarity scores
    base_similarity_scores = similarity_matrix[song_index]
    
    # Adjust scores based on ratings
    adjusted_scores = adjust_similarity_scores(song, base_similarity_scores)
    
    # Get indices of most similar songs
    similar_indices = k_largest_indices(adjusted_scores, K + 1)
    
    # Filter out the selected song's index
    similar_indices = [i for i in similar_indices if i != song_index][:K]

    # Retrieve song details
    similar_songs = spotify_data.iloc[similar_indices][["name", "artists", "popularity"]]
    similar_songs = similar_songs.reset_index(drop=True)
    
    # Add current ratings if they exist
    similar_songs["Rating"] = similar_songs["name"].map(lambda x: user_ratings.get(x, None))
    
    # Rename columns for display
    similar_songs.rename(columns={
        "name": "Song",
        "artists": "Artist",
        "popularity": "Popularity"
    }, inplace=True)
    
    return similar_songs

def get_user_ratings() -> Dict[str, int]:
    """Return the current user ratings."""
    return user_ratings

def get_personalized_recommendations(
    K: int,
    birth_year: int,
    language_prefs: List[str],
    allow_explicit: bool,
    era_prefs: List[str]
) -> pd.DataFrame:
    """Get personalized recommendations based on user preferences."""
    # Create a copy of the data to filter
    filtered_data = spotify_data.copy()
    
    # Filter by explicit content if needed
    if not allow_explicit:
        filtered_data = filtered_data[filtered_data['explicit'] == 0]
    
    # Filter by era preferences
    year_mask = pd.Series(False, index=filtered_data.index)
    for era in era_prefs:
        start_year, end_year = ERA_RANGES[era]
        year_mask |= (filtered_data['year'].between(start_year, end_year))
    filtered_data = filtered_data[year_mask]
    
    # Calculate year relevance score (higher score for songs from user's generation)
    user_generation_start = birth_year - 10
    user_generation_end = birth_year + 20
    filtered_data['year_relevance'] = filtered_data['year'].apply(
        lambda x: 1.0 if user_generation_start <= x <= user_generation_end else 0.5
    )
    
    # Combine popularity and year relevance for final score
    filtered_data['final_score'] = (
        filtered_data['popularity'] * 0.7 + 
        filtered_data['year_relevance'] * 30
    )
    
    # Sort by final score and get top K
    result = filtered_data.nlargest(K, 'final_score')[["name", "artists", "popularity", "year"]]
    
    # Add current ratings if they exist
    result["Rating"] = result["name"].map(lambda x: user_ratings.get(x, None))
    
    # Rename columns for consistency
    result.rename(columns={
        "name": "Song",
        "artists": "Artist",
        "popularity": "Popularity",
        "year": "Year"
    }, inplace=True)
    
    return result

def get_recommendations_from_ratings(K: int) -> Union[pd.DataFrame, None]:
    """Get recommendations based on user's ratings."""
    if not user_ratings:
        return None
        
    # Get highly rated songs (4-5 stars)
    highly_rated = [song for song, rating in user_ratings.items() if rating >= 4]
    if not highly_rated:
        return None
    
    # Combine recommendations from each highly rated song
    all_recommendations = []
    for song in highly_rated:
        recs = k_most_similar_songs(song, K)
        if "Error" not in recs.columns:
            all_recommendations.append(recs)
    
    if not all_recommendations:
        return None
    
    # Combine and remove duplicates
    combined = pd.concat(all_recommendations).drop_duplicates(subset=['Song'])
    
    # Sort by popularity and return top K
    return combined.nlargest(K, 'Popularity')
