import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from sklearn.decomposition import TruncatedSVD
import os

print("🚀 Training started...")

# =========================
# 📁 CREATE FOLDERS
# =========================

os.makedirs("chroma_db", exist_ok=True)
os.makedirs("models", exist_ok=True)

# =========================
# 📊 LOAD DATA
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

print("✅ Data loaded")

# =========================
# 🧹 CLEAN DATA
# =========================

movies['clean_title'] = movies['title'].str.lower().str.replace(r"\(\d{4}\)", "", regex=True)
movies['content'] = movies['clean_title'] + " " + movies['genres']

# =========================
# 🤖 EMBEDDINGS (CONTENT MODEL)
# =========================

model = SentenceTransformer('all-MiniLM-L6-v2')

print("⏳ Generating embeddings...")
embeddings = model.encode(movies['content'].tolist())

# =========================
# 🧠 STORE IN CHROMADB
# =========================

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="movies")

print("Before storing:", collection.count())

collection.add(
    documents=movies['content'].tolist(),
    embeddings=embeddings.tolist(),
    ids=[str(i) for i in movies.index]
)

print("After storing:", collection.count())

# =========================
# 🤝 COLLABORATIVE TRAINING (SVD)
# =========================

print("⏳ Training collaborative model...")

user_movie_matrix = ratings.pivot_table(
    index='userId',
    columns='movieId',
    values='rating'
).fillna(0)

print("Matrix shape:", user_movie_matrix.shape)

svd = TruncatedSVD(n_components=50)
user_factors = svd.fit_transform(user_movie_matrix)
movie_factors = svd.components_

# =========================
# 💾 SAVE MODELS
# =========================

np.save("models/user_factors.npy", user_factors)
np.save("models/movie_factors.npy", movie_factors)

print("✅ SVD model saved")

# =========================
# 🎉 DONE
# =========================

print("🎉 TRAINING COMPLETE")