import streamlit as st
import pandas as pd
import uuid
from recommender import (
    most_popular_songs, 
    k_most_similar_songs, 
    spotify_data, 
    add_rating,
    get_user_ratings,
    get_personalized_recommendations,
    get_recommendations_from_ratings
)

# Set page config
st.set_page_config(
    page_title="Spotify Song Recommender",
    page_icon="🎵",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    /* Main background and text colors */
    .stApp {
        background-color: #121212;
        color: #ffffff;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #000000;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #1DB954 !important;
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: #1DB954;
        color: white;
        border-radius: 20px;
        padding: 10px 24px;
        border: none;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #1ed760;
        border: none;
    }
    
    /* Container styling */
    div[data-testid="stVerticalBlock"] {
        background-color: #282828;
        padding: 20px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background-color: #1DB954;
    }
    
    /* Text inputs */
    .stTextInput>div>div>input {
        background-color: #282828;
        color: white;
        border: 1px solid #404040;
    }
    
    /* Selectbox */
    .stSelectbox>div>div {
        background-color: #282828;
        color: white;
    }
    
    /* Section divider */
    .section-divider {
        border-top: 1px solid #404040;
        margin: 30px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    if 'step' not in st.session_state:
        st.session_state.step = 1
    if 'user_name' not in st.session_state:
        st.session_state.user_name = ""
    if 'birth_year' not in st.session_state:
        st.session_state.birth_year = None
    if 'language_pref' not in st.session_state:
        st.session_state.language_pref = None
    if 'explicit_pref' not in st.session_state:
        st.session_state.explicit_pref = None
    if 'era_pref' not in st.session_state:
        st.session_state.era_pref = None
    if 'setup_complete' not in st.session_state:
        st.session_state.setup_complete = False
    if 'section_ids' not in st.session_state:
        st.session_state.section_ids = {
            'personal': str(uuid.uuid4())[:8],
            'ratings': str(uuid.uuid4())[:8],
            'explore': str(uuid.uuid4())[:8]
        }
    if 'temp_ratings' not in st.session_state:
        st.session_state.temp_ratings = {}

init_session_state()

def display_song_card(row: pd.Series, idx: int, cols, section: str):
    """Display a song card with rating functionality."""
    # Create unique keys for this song
    song_key = f"{section}_{idx}_{row['Song']}"
    rating_key = f"rating_{song_key}"
    
    # Initialize rating in session state if not exists
    if rating_key not in st.session_state.temp_ratings:
        st.session_state.temp_ratings[rating_key] = 1
    
    with cols[idx % 3]:
        with st.container():
            # Song info using native Streamlit components
            st.markdown(f"### {row['Song']}")
            st.markdown(f"**Artist:** {row['Artist']}")
            st.markdown(
                f"**Popularity:** {row['Popularity']}" + 
                (f" • **Year:** {row['Year']}" if 'Year' in row else ""),
                help="Song popularity score from Spotify"
            )
            
            # Current rating from database
            current_rating = row.get('Rating')
            if current_rating and pd.notna(current_rating):
                st.write(f"Your Rating: {'⭐' * int(current_rating)}")
            
            # Rating input
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write("Rate:")
                for i in range(1, 6):
                    if st.button(
                        "⭐" * i, 
                        key=f"star_{i}_{song_key}",
                        help=f"Rate {i} stars",
                        use_container_width=True
                    ):
                        st.session_state.temp_ratings[rating_key] = i
                
            # Show current selection
            st.write(f"Selected: {'⭐' * st.session_state.temp_ratings[rating_key]}")
            
            # Submit button
            if st.button("Submit Rating", key=f"submit_{song_key}", use_container_width=True):
                rating = st.session_state.temp_ratings[rating_key]
                add_rating(row['Song'], rating)
                st.success(f"Rating submitted: {'⭐' * rating}")
                st.rerun()

def show_welcome():
    """Show the welcome screen and onboarding process."""
    if st.session_state.step == 1:
        st.markdown("<h1 style='text-align: center; margin-top: 100px;'>Welcome to Your Personal Music Journey 🎵</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 20px;'>Let's get to know you better to create your perfect playlist!</p>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            user_name = st.text_input("Hey there! What should we call you?", key="name_input")
            if st.button("Let's Begin!", key="start_button"):
                if user_name:
                    st.session_state.user_name = user_name
                    st.session_state.step = 2
                    st.rerun()
                else:
                    st.error("Please tell us your name!")

    elif st.session_state.step == 2:
        st.markdown(f"<h2>Nice to meet you, {st.session_state.user_name}! 👋</h2>", unsafe_allow_html=True)
        birth_year = st.number_input("When were you born?", min_value=1940, max_value=2010, value=1990)
        if st.button("Next"):
            st.session_state.birth_year = birth_year
            st.session_state.step = 3
            st.rerun()

    elif st.session_state.step == 3:
        st.markdown("<h2>What languages do you prefer for music? 🌍</h2>", unsafe_allow_html=True)
        languages = st.multiselect(
            "Select your preferred languages",
            ["English", "Spanish", "French", "Korean", "Japanese", "Hindi", "Other"],
            default=["English"]
        )
        if st.button("Next"):
            if languages:
                st.session_state.language_pref = languages
                st.session_state.step = 4
                st.rerun()
            else:
                st.error("Please select at least one language!")

    elif st.session_state.step == 4:
        st.markdown("<h2>How do you feel about explicit content? 🤔</h2>", unsafe_allow_html=True)
        explicit_pref = st.radio(
            "Select your preference",
            ["Include explicit content", "Exclude explicit content"],
            index=0
        )
        if st.button("Next"):
            st.session_state.explicit_pref = explicit_pref == "Include explicit content"
            st.session_state.step = 5
            st.rerun()

    elif st.session_state.step == 5:
        st.markdown("<h2>What era of music speaks to you? 🎸</h2>", unsafe_allow_html=True)
        era_pref = st.multiselect(
            "Select your preferred eras",
            ["60s & 70s", "80s", "90s", "2000s", "2010s", "Latest"],
            default=["2010s", "Latest"]
        )
        if st.button("Finish"):
            if era_pref:
                st.session_state.era_pref = era_pref
                st.session_state.setup_complete = True
                st.rerun()
            else:
                st.error("Please select at least one era!")

    # Show progress bar
    progress = st.session_state.step / 5  # Value between 0 and 1
    st.progress(progress)

def show_main_interface():
    """Show the main recommendation interface with both personalized and rating-based recommendations."""
    st.title(f"Welcome Back, {st.session_state.user_name}! 🎵")
    
    # Sidebar settings
    st.sidebar.header("Settings")
    k = st.sidebar.slider("Number of recommendations per section", 3, 15, value=6)
    
    # Get personalized recommendations
    personal_recs = get_personalized_recommendations(
        k,
        st.session_state.birth_year,
        st.session_state.language_pref,
        st.session_state.explicit_pref,
        st.session_state.era_pref
    )
    
    # Display personalized recommendations
    st.markdown("## Recommended for You 🎯")
    if not personal_recs.empty:
        cols = st.columns(3)
        for idx, row in personal_recs.iterrows():
            display_song_card(row, idx, cols, f"personal_{st.session_state.section_ids['personal']}")
    
    # Display rating-based recommendations if available
    rating_recs = get_recommendations_from_ratings(k)
    if rating_recs is not None:
        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
        st.markdown("## Based on Your Ratings ⭐")
        cols = st.columns(3)
        for idx, row in rating_recs.iterrows():
            display_song_card(row, idx, cols, f"ratings_{st.session_state.section_ids['ratings']}")
    
    # Option to explore more
    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    st.markdown("## Explore More 🔍")
    explore_method = st.radio(
        "Choose a method:",
        ["Similar to a Song", "Most Popular"]
    )
    
    if explore_method == "Similar to a Song":
        song = st.selectbox(
            "Pick a song!",
            sorted(spotify_data["name"].unique()),
            index=0
        )
        explore_recs = k_most_similar_songs(song, k)
    else:
        explore_recs = most_popular_songs(spotify_data, k)
    
    if not explore_recs.empty and "Error" not in explore_recs.columns:
        cols = st.columns(3)
        for idx, row in explore_recs.iterrows():
            display_song_card(row, idx, cols, f"explore_{st.session_state.section_ids['explore']}")

# Main app logic
if not st.session_state.setup_complete:
    show_welcome()
else:
    show_main_interface()
