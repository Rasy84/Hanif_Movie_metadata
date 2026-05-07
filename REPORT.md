# Movie Metadata RAG Assistant  
### Technical Report — Abu Hanif · DSA 502

---

## Introduction

This report describes **Hanif_Movie_metadata**, a Flask web application that combines classical information retrieval with a large language model served through **Ollama**. The goal is to answer user questions about movies using **only** metadata that has been retrieved from a structured dataset, which mirrors a practical RAG pipeline: **retrieve credible context first**, then **generate** a careful natural-language response.

## Dataset overview

The source file is **`movies_metadata.csv`**, with approximately **45,453** rows of movie records. For this project, the following fields are kept:

- **title**, **overview** — primary textual signals for semantic similarity.
- **genres** — stored as serialized list-of-dictionaries text in the CSV; converted to a comma-separated list of genre names for readability and search.
- **release_date**, **vote_average**, **vote_count**, **popularity** — included for grounding facts in the LLM context and for display in the results table.

Rows with missing or empty **title** or **overview** are removed so the retrieval corpus remains high quality.

## Data cleaning steps

1. **Column selection:** Only the columns listed above are read into the working DataFrame.
2. **Title and overview:** Stripped of surrounding whitespace; rows with blank or invalid text are dropped.
3. **Genres:** Parsed safely with `ast.literal_eval` where possible; `name` fields are extracted and joined into a single readable string. Unparseable values fall back to the raw string or empty text so retrieval does not crash.

## Retrieval method explanation

Each movie is represented by a single **aggregate text field** formed by concatenating **title**, **overview**, and **genres** (readable). The user question is treated as another piece of text in the same space.

**TF-IDF (Term Frequency–Inverse Document Frequency)** converts each document into a sparse vector. Informally:

- **Term frequency** rewards words that appear in a document.
- **Inverse document frequency** down-weights words that appear in many movies (generic words).

The vectorizer is configured with word and short phrase features (`ngram_range` including bigrams), frequency cutoffs (`min_df`, `max_df`), and a cap on vocabulary size for scalability on ~45k documents.

## TF-IDF + cosine similarity explanation

After vectorization, each movie and the user question are points in a high-dimensional space. **Cosine similarity** measures the cosine of the angle between two vectors. It ranges (for non-negative TF-IDF weights) in a way that favors documents whose weighted word patterns point in a similar direction to the query, regardless of document length.

For each query, the app computes similarity against **all** rows, sorts scores in descending order, and returns the **top 5** matches. Those scores are shown in the UI as **similarity** values so users can see how confident the ranker is relative to the query wording.

## Ollama grounded answer method

The top movies are serialized into a **compact context block** that includes structured fields and a trimmed overview. The application POSTs to:

`http://localhost:11434/api/generate`

with **`model`: `minimax-m2.1:cloud`** and **`stream`: false**.

The prompt explicitly instructs the model to:

- Use **only** the provided movie context.
- Avoid outside knowledge or invention.
- State clearly when the retrieved movies **do not** contain enough information.

This is the core “**grounding**” mechanism: the LLM is not asked to be a general movie encyclopedia; it is asked to behave like a **reader** of the retrieved passages.

## App features

- Flask routes for **GET** and **POST** on `/`.
- **TF-IDF retrieval** with **cosine similarity**, top **5** movies.
- **Responsive** UI with example questions, results table, AI answer card, and dedicated error display when Ollama is unreachable or returns an error.
- **Client-side validation messaging** for empty questions.

## Testing examples

**Local smoke tests (manual):**

1. Start Ollama with the required model; start the Flask app on port **5005**.
2. Submit “Animated family comedy about toys” — expect family animation/comedy titles near the top; the answer should summarize only those rows.
3. Stop Ollama and submit any query — expect the **error card** explaining that localhost:11434 is not reachable.
4. Submit an empty query — expect the **validation** message without a server error.

## Limitations

- **Bag-of-words retrieval** does not capture deep semantics the way embeddings might; similar wording matters more than true meaning.
- **TF-IDF training** excludes very rare tokens (`min_df`), which can slightly affect niche queries.
- The LLM may still **hallucinate** if it ignores instructions; the prompt mitigates but does not guarantee compliance.
- **Cloud models** depend on network and Ollama account/cloud availability; timeouts are possible.
- Very short or ambiguous queries can return relevant-looking titles that do not fully answer the user’s intent.

## Conclusion

The project demonstrates a minimal but complete **RAG loop** in Python: **pandas** for data preparation, **scikit-learn** for **TF-IDF** indexing and **cosine similarity** retrieval, **Flask** for the HTTP interface, and **Ollama** for **grounded** generation over retrieved metadata. It is suitable as a course artifact showing how classical IR can feed modern LLM APIs responsibly when paired with strict prompting.
