from fastapi import FastAPI
from app.recommender import recommend_movies
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
def home():
    return open("app/templates/index.html").read()

@app.get("/watchlist", response_class=HTMLResponse)
def watchlist():
    return open("app/templates/watchlist.html").read()

@app.get("/history", response_class=HTMLResponse)
def history():
    return open("app/templates/history.html").read()


@app.get("/")
def home():
    return {"message": "Smart Movie Recommender 🚀"}

@app.get("/recommend")
def recommend(movie: str):
    result = recommend_movies(movie)
    return result.to_dict(orient="records")