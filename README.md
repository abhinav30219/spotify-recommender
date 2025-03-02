# Spotify Song Recommender

A Streamlit-based application that provides personalized song recommendations based on user preferences and ratings.

## Features

- **Personalized Recommendations**: Get song recommendations based on your age, language preferences, and era preferences
- **Rating System**: Rate songs to improve future recommendations
- **Similar Song Discovery**: Find songs similar to ones you already enjoy
- **Popular Song Exploration**: Discover trending songs on Spotify
- **User-Friendly Interface**: Clean, Spotify-themed UI for an intuitive experience

## Screenshots

(Add screenshots of your application here)

## Installation

### Prerequisites

- Python 3.8+
- Git LFS (for handling large files)

### Setup

1. **Clone the repository**

```bash
git clone https://github.com/abhinav30219/spotify-recommender.git
cd spotify-recommender
```

2. **Set up a virtual environment**

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

## Usage

1. **Run the Streamlit app**

```bash
streamlit run app.py
```

2. **Access the application**

Open your web browser and go to `http://localhost:8501`

3. **First-time setup**

- Enter your name and preferences
- Start rating songs to improve recommendations

## Data

The application uses:
- A sampled dataset of Spotify songs (`sampled_spotify_songs.csv`)
- A pre-computed similarity matrix for song recommendations (`similarity_matrix.npy`)

## Technical Details

- **Frontend**: Streamlit
- **Backend**: Python (scikit-learn, pandas, numpy)
- **Recommendation Algorithms**:
  - Content-based filtering
  - Popularity-based recommendations
  - User preference filtering

## License

[MIT License](LICENSE)

## Acknowledgments

- Spotify for the inspiration
- Streamlit for the amazing framework
