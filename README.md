# Hanif_Movie_metadata — Movie Metadata RAG Assistant

## Purpose

This project is a small **retrieval-augmented generation (RAG)** web application. It loads a public movie metadata dataset, finds the most relevant films for a natural-language question using **TF-IDF vectors and cosine similarity**, builds a **compact text context** from the top matches, and sends that context to **Ollama** so the language model can produce a **grounded** answer that uses only the retrieved movie information.

## Dataset description

The app reads `movies_metadata.csv` (TMDB / “The Movies Dataset” style metadata). The file contains on the order of **45,453** rows with columns such as `title`, `overview`, `genres`, `release_date`, `vote_average`, `vote_count`, and `popularity`. Only these columns are retained for retrieval and display; `genres` is parsed from list/dictionary-style text into readable genre names.

## RAG workflow

**Question → Retrieve → Build Context → LLM Answer**

1. The user enters a question (or keywords) in the browser.
2. **Retrieve:** The question is encoded with the same TF-IDF vectorizer used for the corpus. **Cosine similarity** scores every movie; the **top 5** rows are kept, with scores shown in the UI.
3. **Build context:** Those rows are formatted into a short, human-readable block (titles, dates, genres, votes, popularity, trimmed overviews).
4. **LLM answer:** That block is sent in the prompt to Ollama (`/api/generate`) with instructions to answer **only** from the context and to admit when the context is insufficient.

## Setup steps

1. **Python 3.10+** recommended.
2. Place `movies_metadata.csv` in the project root next to `app.py` (included when you clone or copy this folder).
3. Create a virtual environment (optional but recommended):

   ```text
   python -m venv .venv
   .venv\Scripts\activate
   ```

## Ollama setup

Check Ollama is installed:

```text
ollama --version
```

Run the required model (downloads or verifies the cloud tag as needed):

```text
ollama run minimax-m2.1:cloud
```

Keep the Ollama service running so `http://localhost:11434` accepts API requests.

**Cloud models and “unauthorized”:** If the UI showed an auth error, sign in with **`ollama signin`** or create an API key at [ollama.com/settings/keys](https://ollama.com/settings/keys) and set **`OLLAMA_API_KEY`** before starting Flask (Windows PowerShell: `$env:OLLAMA_API_KEY="your_key"`). The app sends `Authorization: Bearer …` when that variable is set. Retrieval and the results table work even when the LLM step is skipped.

## Installation

```text
pip install -r requirements.txt
```

## Run

```text
python app.py
```

## Open

In your browser, go to:

```text
http://127.0.0.1:5005
```

## Sample questions

- “Animated family comedy about toys”
- “Romance and drama in New York City”
- “Space science fiction adventure”
- “Psychological thriller mystery”
- “Movies similar to a magical board game adventure”

## Screenshot instruction

After a successful search, capture the page showing the **retrieved movies table** and **AI answer card**. Save the image under `screenshots/` as **`app_sample.png`**. See `screenshots/APP_SAMPLE_SCREENSHOT.txt` for a short checklist.

## GitHub submission note

If you submit this project on GitHub, avoid committing secrets (`.env` is gitignored). The dataset file is large; confirm your course policy on whether `movies_metadata.csv` should be included in the repo or downloaded separately, and use Git LFS or an external link if required.
