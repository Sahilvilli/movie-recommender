import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb

# =========================
# SAFE MODEL LOADING
# =========================

user_factors = None
movie_factors = None

def load_models():
    global user_factors, movie_factors

    if user_factors is None or movie_factors is None:
        print("📦 Loading SVD models...")

        user_factors = np.load("models/user_factors.npy")
        movie_factors = np.load("models/movie_factors.npy")

# =========================
# CHROMADB
# =========================

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="movies")
print("Loaded DB size:", collection.count())

# =========================
# LOAD DATA
# =========================

movies = pd.read_csv(
    "data/movies.dat",
    sep="::",
    engine="python",
    encoding="latin-1",
    names=["movieId", "title", "genres"]
)

ratings = pd.read_csv(
    "data/ratings.dat",
    sep="::",
    engine="python",
    encoding="latin-1",
    names=["userId", "movieId", "rating", "timestamp"]
)

# =========================
# ✅ SINGLE CLEAN RATING BLOCK (FIX)
# =========================

movie_stats = ratings.groupby('movieId')['rating'].mean().reset_index()
movie_stats.columns = ['movieId', 'avg_rating']

movies = movies.merge(movie_stats, on='movieId', how='left')

# ensure exists
movies['avg_rating'] = movies['avg_rating'].fillna(0)

# =========================
# USER-MOVIE MATRIX
# =========================

user_movie_matrix = ratings.pivot_table(
    index='userId',
    columns='movieId',
    values='rating'
).fillna(0)

# =========================
# CLEAN DATA
# =========================

movies['clean_title'] = movies['title'].str.lower().str.replace(r"\(\d{4}\)", "", regex=True)
movies['content'] = movies['clean_title'] + " " + movies['genres']

# =========================
# MODEL
# =========================

model = SentenceTransformer('all-MiniLM-L6-v2')

# =========================
# POPULARITY
# =========================

movie_stats = ratings.groupby('movieId').agg({
    'rating': ['mean', 'count']
}).reset_index()

movie_stats.columns = ['movieId', 'avg_rating_pop', 'rating_count']

movies = movies.merge(movie_stats, on="movieId", how="left")

movies.fillna(0, inplace=True)

movies['popularity_score'] = movies['rating_count'] / (movies['rating_count'].max() + 1)

# =========================
# SEARCH
# =========================

def search_movie(query):
    query = query.lower()

    matches = movies[movies['clean_title'].str.contains(query, na=False)]

    if len(matches) > 0:
        print("✅ Movie match:", matches.iloc[0]['title'])
        return matches.iloc[0]['content'], "movie"

    print("🔍 Treating as semantic query")
    return query, "semantic"

# =========================
# RECOMMENDER
# =========================

def recommend_movies(query, top_k=80):

    print("\n🔍 Query:", query)

    load_models()

    movie_content, mode = search_movie(query)

    query_embedding = model.encode([movie_content]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=100
    )

    if not results or 'ids' not in results or len(results['ids']) == 0 or len(results['ids'][0]) == 0:
        return movies.sample(top_k)[['title', 'genres']]

    indices = [int(i) for i in results['ids'][0] if i is not None]

    if len(indices) == 0:
        return movies.sample(top_k)[['title', 'genres']]

    candidates = movies.iloc[indices].copy()

    candidates['content_score'] = 1.0 if mode == "movie" else 0.8
    candidates['popularity_score'] = candidates['popularity_score']

    collab_scores = []

    for idx in indices:
        movie_id = movies.iloc[idx]['movieId']

        try:
            movie_index = list(user_movie_matrix.columns).index(movie_id)
            score = np.mean(movie_factors[:, movie_index])
        except:
            score = 0

        collab_scores.append(score)

    candidates['collab_score'] = collab_scores

    candidates['final_score'] = (
        0.5 * candidates['content_score'] +
        0.3 * candidates['popularity_score'] +
        0.2 * candidates['collab_score']
    )

    candidates = candidates.sort_values(by="final_score", ascending=False)
    top = candidates.head(20)          # best results
    rest = candidates.iloc[20:50].sample(frac=1)  # shuffle rest

    candidates = pd.concat([top, rest])

    final = candidates[['title', 'genres', 'avg_rating']].head(top_k)

    final['title'] = final['title'].apply(clean_title_display)
    final['genres'] = final['genres'].str.replace('|', ', ')

    return final

# =========================
# CLEAN TITLES
# =========================

def clean_title_display(title):
    if ", The" in title:
        return "The " + title.replace(", The", "")
    if ", A" in title:
        return "A " + title.replace(", A", "")
    if ", An" in title:
        return "An " + title.replace(", An", "")
    return title