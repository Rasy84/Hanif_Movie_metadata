"""
Movie Metadata RAG Assistant — Flask + TF-IDF retrieval + Ollama.
"""
from __future__ import annotations

import ast
import os
import re
from pathlib import Path

import pandas as pd
import requests
from flask import Flask, render_template, request
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "movies_metadata.csv"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "minimax-m2.1:cloud"

USEFUL_COLS = [
    "title",
    "overview",
    "genres",
    "release_date",
    "vote_average",
    "vote_count",
    "popularity",
]

# Populated by build_retrieval_index()
_movies_df: pd.DataFrame | None = None
_tfidf_matrix = None
_vectorizer: TfidfVectorizer | None = None


def load_movies() -> pd.DataFrame:
    """Load movies_metadata.csv, keep useful columns, drop bad rows."""
    df = pd.read_csv(CSV_PATH, low_memory=False)
    missing = [c for c in USEFUL_COLS if c not in df.columns]
    for c in missing:
        df[c] = pd.NA
    df = df[USEFUL_COLS].copy()
    df["title"] = df["title"].astype(str).str.strip()
    df["overview"] = df["overview"].astype(str).str.strip()
    df = df[(df["title"].notna()) & (df["title"] != "") & (df["title"].str.lower() != "nan")]
    df = df[(df["overview"].notna()) & (df["overview"] != "") & (df["overview"].str.lower() != "nan")]
    df["genres_readable"] = df["genres"].apply(clean_genres)
    df = df.reset_index(drop=True)
    return df


def clean_genres(genres_val) -> str:
    """Convert list/dict-style genre text into readable genre names."""
    if pd.isna(genres_val) or genres_val is None:
        return ""
    s = str(genres_val).strip()
    if not s or s.lower() == "nan":
        return ""
    try:
        parsed = ast.literal_eval(s)
    except (ValueError, SyntaxError):
        return s
    names: list[str] = []
    if isinstance(parsed, list):
        for item in parsed:
            if isinstance(item, dict) and "name" in item:
                names.append(str(item["name"]))
    elif isinstance(parsed, dict) and "name" in parsed:
        names.append(str(parsed["name"]))
    return ", ".join(names)


def build_retrieval_index(df: pd.DataFrame) -> None:
    """Fit TF-IDF on title + overview + genres for cosine retrieval."""
    global _movies_df, _tfidf_matrix, _vectorizer
    parts = (
        df["title"].fillna("").astype(str)
        + " "
        + df["overview"].fillna("").astype(str)
        + " "
        + df["genres_readable"].fillna("").astype(str)
    )
    corpus = parts.tolist()
    _vectorizer = TfidfVectorizer(
        max_features=50_000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.85,
        strip_accents="unicode",
    )
    _tfidf_matrix = _vectorizer.fit_transform(corpus)
    _movies_df = df


def choose_top_k(question: str, k_max: int = 12) -> int:
    """
    Pick how many rows to retrieve from wording (e.g. singular best → 1,
    cost/budget queries → more rows, explicit numbers honored).
    """
    q = re.sub(r"\s+", " ", (question or "").strip().lower())
    if not q:
        return 5

    digit_patterns = [
        r"\btop\s+(\d{1,2})\b",
        r"\bfirst\s+(\d{1,2})\b",
        r"\b(\d{1,2})\s+(?:best|top)\s+(?:movies|films)\b",
        r"\b(?:give|show)\s+me\s+(\d{1,2})\b",
        r"\b(\d{1,2})\s+(?:movies|films|results|titles|picks)\b",
    ]
    for pat in digit_patterns:
        m = re.search(pat, q)
        if m:
            return max(1, min(int(m.group(1)), k_max))

    if re.search(
        r"\b(?:expensive|cheapest|cheap|budget|cost|costly|price|money|richest)\b", q
    ):
        return min(10, k_max)

    if re.search(
        r"\b(?:list|several|many|some|few|recommendations?|suggestions?|examples?|options?)\b",
        q,
    ):
        return min(8, k_max)

    if re.search(r"\bcompare\b|\bvs\.?\b", q):
        return min(6, k_max)

    # One pick: "best movie", "best comedy movie", "top sci-fi film" (singular only)
    if re.search(
        r"\b(?:best|top|greatest)\s+(?:(?:\S+\s+){0,4})(?:movie|film)\b",
        q,
    ) and not re.search(r"\b(?:movies|films)\b", q):
        return 1

    if re.search(
        r"\b(?:the\s+)?(?:single|one|a\s+single|just\s+one)\s+(?:movie|film|pick)\b", q
    ) or re.search(
        r"\b(?:what(?:\'s| is)\s+the\s+)?(?:best|top|greatest)\s+(?:movie|film)\b", q
    ):
        return 1

    if re.search(r"\b(?:best|top|greatest)\s+(?:movies|films)\b", q) or re.search(
        r"\b(?:best|top|greatest)\b.*\b(?:movies|films)\b", q
    ):
        return min(7, k_max)

    return 5


def retrieve_movies(question: str, top_k: int = 5) -> list[dict]:
    """Return top_k rows with cosine similarity scores vs. the question."""
    if _movies_df is None or _vectorizer is None or _tfidf_matrix is None:
        raise RuntimeError("Retrieval index not built. Call build_retrieval_index first.")
    q = (question or "").strip()
    if not q:
        return []
    q_vec = _vectorizer.transform([q])
    sims = cosine_similarity(q_vec, _tfidf_matrix).flatten()
    top_idx = sims.argsort()[::-1][:top_k]
    out: list[dict] = []
    for rank, idx in enumerate(top_idx, start=1):
        idx = int(idx)
        row = _movies_df.iloc[idx]
        score = float(sims[idx])
        title = str(row.get("title", ""))
        overview = str(row.get("overview", ""))
        genres_display = str(row.get("genres_readable", ""))
        rd = row.get("release_date", "")
        release_date = "" if pd.isna(rd) else str(rd).split(" ")[0]
        va = row.get("vote_average", "")
        if pd.isna(va):
            vote_average = ""
        else:
            try:
                vote_average = round(float(va), 1)
            except (ValueError, TypeError):
                vote_average = str(va)
        vc = row.get("vote_count", "")
        if pd.isna(vc):
            vote_count = ""
        else:
            try:
                vote_count = int(float(vc))
            except (ValueError, TypeError):
                vote_count = str(vc)
        pop = row.get("popularity", "")
        if pd.isna(pop):
            popularity = ""
        else:
            try:
                popularity = round(float(pop), 3)
            except (ValueError, TypeError):
                popularity = str(pop)
        out.append(
            {
                "rank": rank,
                "title": title,
                "genres": genres_display,
                "release_date": release_date,
                "vote_average": vote_average,
                "vote_count": vote_count,
                "popularity": popularity,
                "overview": overview,
                "similarity": score,
            }
        )
    return out


def build_context(rows: list[dict]) -> str:
    """Build a compact grounded context string from retrieved rows."""
    chunks: list[str] = []
    for r in rows:
        ov = str(r.get("overview", ""))
        if len(ov) > 600:
            ov = ov[:600].rstrip() + "…"
        chunks.append(
            f"[{r['rank']}] {r['title']} | Released: {r.get('release_date', 'n/a')} | "
            f"Genres: {r.get('genres', '')} | Rating: {r.get('vote_average', 'n/a')} "
            f"({r.get('vote_count', 'n/a')} votes) | Popularity: {r.get('popularity', 'n/a')}\n"
            f"Overview: {ov}"
        )
    return "\n\n---\n\n".join(chunks)


def ask_ollama(question: str, context: str) -> tuple[str | None, str | None]:
    """
    Call Ollama /api/generate with a grounded prompt.
    Returns (answer, error_message). One of them is always None.
    """
    prompt = (
        "You are a movie metadata assistant. Answer the user's question using ONLY the "
        "information in the MOVIE CONTEXT below. Do not use outside knowledge or invent "
        "facts. If the context does not contain enough information to answer, say clearly "
        "that you cannot answer from the retrieved movies only, and briefly say what is "
        "missing.\n\n"
        f"MOVIE CONTEXT:\n{context}\n\n"
        f"USER QUESTION:\n{question}\n\n"
        "GROUNDED ANSWER:"
    )
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    headers: dict[str, str] = {"Content-Type": "application/json"}
    api_key = (os.environ.get("OLLAMA_API_KEY") or "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        resp = requests.post(OLLAMA_URL, json=payload, headers=headers, timeout=180)
    except requests.exceptions.ConnectionError:
        return None, (
            "Cannot reach Ollama at http://localhost:11434. "
            "Start Ollama and ensure it is listening (e.g. run `ollama serve`)."
        )
    except requests.exceptions.Timeout:
        return None, "Ollama request timed out. The cloud model may be slow or unavailable."
    except requests.exceptions.RequestException as exc:
        return None, f"Request error while calling Ollama: {exc}"
    try:
        data = resp.json()
    except ValueError:
        return None, f"Ollama returned a non-JSON response (HTTP {resp.status_code})."

    if isinstance(data, dict) and data.get("error"):
        err = str(data["error"])
        err_l = err.lower()
        if resp.status_code in (401, 403) or "unauthorized" in err_l or "401" in err_l:
            return None, None
        return None, err

    if resp.status_code != 200:
        err = data.get("error") if isinstance(data, dict) else None
        err_l = (str(err) if err else "").lower()
        if resp.status_code in (401, 403) or "unauthorized" in err_l:
            return None, None
        return None, (
            str(err)
            if err
            else f"Ollama HTTP {resp.status_code}. Pull the model with: "
            f"ollama run {OLLAMA_MODEL}"
        )
    if not isinstance(data, dict) or "response" not in data:
        return None, "Unexpected response from Ollama (missing 'response' field)."
    return (str(data.get("response", "")).strip(), None)


app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    question = ""
    retrieved: list[dict] = []
    top_k = 0
    answer: str | None = None
    error: str | None = None
    input_error: str | None = None

    if request.method == "POST":
        question = (request.form.get("question") or "").strip()
        if not question:
            input_error = "Please enter a question or keywords to search."
        else:
            top_k = choose_top_k(question)
            retrieved = retrieve_movies(question, top_k=top_k)
            answer, error = ask_ollama(question, build_context(retrieved))

    return render_template(
        "index.html",
        question=question,
        retrieved=retrieved,
        top_k=top_k,
        answer=answer,
        error=error,
        input_error=input_error,
    )


def init_app() -> None:
    print("Loading movies from CSV (first run may take 30–60 seconds to build TF-IDF)…", flush=True)
    df = load_movies()
    print(f"Loaded {len(df):,} movies. Building TF-IDF index…", flush=True)
    build_retrieval_index(df)
    print("Retrieval index ready.", flush=True)


init_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5005, debug=False)

