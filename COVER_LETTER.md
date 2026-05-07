# Cover Letter

**Student name:** Abu Hanif  
**Course:** DSA 502  
**Project:** Movie Metadata RAG Assistant (`Hanif_Movie_metadata`)

Dear Instructor,

Please accept this submission for my mini-project **Movie Metadata RAG Assistant**. The application is a Flask web service that loads movie metadata from `movies_metadata.csv`, cleans and normalizes key fields (including human-readable genres), and implements retrieval with **TF-IDF vectorization** and **cosine similarity** to surface the top matching films for each user question. Retrieved rows are packaged into a concise context block and sent to the **Ollama** HTTP API so an LLM can produce a **grounded** response based strictly on that context.

This work demonstrates practical integration of **classical information retrieval**, a **Python data pipeline**, and **modern LLM response generation** in a single end-to-end workflow suitable for coursework in data structures, algorithms, and applied systems.

## Screenshots (running app)

Figures are in **`screenshots/`** (paths below use `./screenshots/...` so they resolve in GitHub and in local editors).

### Home screen — search bar and example prompts

![Movie Metadata RAG Assistant — home screen](./screenshots/01_home.png)

### Example: “Best comedy movie” — retrieved rows and similarity scores

![Movie Metadata RAG Assistant — best comedy search](./screenshots/02_search_best_comedy.png)

### Example: “Romance and drama in New York City” — results table

![Movie Metadata RAG Assistant — romance and drama NYC](./screenshots/03_romance_nyc.png)

### Example: “Movies similar to a magical board game adventure” — retrieval

![Movie Metadata RAG Assistant — magical board game query](./screenshots/04_magical_board_game.png)

### Additional sample search

![Movie Metadata RAG Assistant — additional sample](./screenshots/05_sample_search.png)

Sincerely,  
Abu Hanif
