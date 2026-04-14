let watchlist = JSON.parse(localStorage.getItem("watchlist")) || [];
let history = JSON.parse(localStorage.getItem("history")) || [];
let currentPage = 0;
let allResults = [];
async function searchMovies() {
    const query = document.getElementById("searchInput").value;
    fetchMovies(query);
}

function searchGenre(genre) {
    fetchMovies(genre);
}


async function fetchMovies(query) {
    const res = await fetch(`/recommend?movie=${query}`);
    const data = await res.json();

    allResults = data;
    currentPage = 0;

    document.getElementById("nextBtn").style.display = "block";
    document.getElementById("prevBtn").style.display = "none";

    displayPage();
}

function addToWatchlist(movie) {
    watchlist.push(movie);
    localStorage.setItem("watchlist", JSON.stringify(watchlist));
    alert("Added to Watchlist!");
}

function displayPage() {
    const container = document.getElementById("moviesContainer");

    container.style.opacity = 0;
    container.style.transform = "translateX(50px)";

    setTimeout(() => {
        container.innerHTML = "";

        const start = currentPage * 16;
        const end = start + 16;

        const pageData = allResults.slice(start, end);

        pageData.forEach(movie => {
            const rating = movie.avg_rating ? (movie.avg_rating / 1).toFixed(1) : "N/A";

            const div = document.createElement("div");
            div.className = "movie-card";

            div.innerHTML = `
                <h3>${movie.title}</h3>
                <p>${movie.genres}</p>
                <p class="rating">⭐ ${rating}/5</p>
                <button onclick='addToWatchlist(${JSON.stringify(movie)})'>+ Watchlist</button>
            `;

            container.appendChild(div);
        });

        container.style.opacity = 1;
        container.style.transform = "translateX(0)";
    }, 200);
    const maxPages = Math.ceil(allResults.length / 16);

// show/hide buttons
    document.getElementById("prevBtn").style.display = currentPage > 0 ? "block" : "none";

    document.getElementById("nextBtn").style.display =
    (currentPage < maxPages - 1 && currentPage < 4) ? "block" : "none";
}
function nextPage() {
    const maxPages = Math.ceil(allResults.length / 16);

    if (currentPage >= maxPages - 1) return;   // stop at actual last page
    if (currentPage >= 4) return;              // max 5 pages

    currentPage++;
    displayPage();
}

function goHome() {
    window.location.href = "/";
}

function goWatchlist() {
    window.location.href = "/watchlist";
}

function goHistory() {
    window.location.href = "/history";
}
function prevPage() {
    if (currentPage === 0) return;

    currentPage--;
    displayPage();
}