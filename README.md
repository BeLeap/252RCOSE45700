# COSE457

Prepare a Python environment (e.g., `python -m venv .venv && source .venv/bin/activate`) and install dependencies:

```
pip install -r requirements.txt
```

## Ingest

By default ingestion uses Google embeddings (`gemini-embedding-001`). Set `GOOGLE_API_KEY` and then build the FAISS index (defaults download the provided S3 PDFs):

```
python scripts/ingest.py \
  --verify-query "What was emphasized about cash flow?"
```

Note: the Google API expects model ids prefixed with `models/`; the script will normalize common names (e.g., `gemini-embedding-001` → `models/embedding-001`, `text-embedding-004` → `models/text-embedding-004`).

Artifacts are written to `data/faiss_store/`, `data/faiss.index`, and `data/faiss-meta.json`. Customize chunking with `--chunk-size`/`--chunk-overlap` or point `--sources` to local files or directories.

## Server

Start the FastAPI RAG server (expects the FAISS artifacts above). It uses Google embeddings (`RAG_EMBEDDING_MODEL=gemini-embedding-001`) and Gemini for generation (`RAG_LLM_MODEL=gemini-3-pro-preview`, requires `GOOGLE_API_KEY`):

```
uvicorn server.main:app --reload --port 8000
```

Key endpoints:
- `GET /health` — index/metadata status.
- `POST /reload` — reload FAISS store and metadata from disk.
- `POST /query` — body `{ "query": "...", "top_k": 5 }`, responds with `text/event-stream` streaming tokens and a first `citations` event containing source metadata.

Configurable via env vars: `RAG_EMBEDDING_MODEL`, `RAG_LLM_MODEL`, `RAG_INDEX_DIR`, `RAG_INDEX_PATH`, `RAG_METADATA_PATH`, `RAG_TOP_K`, `GOOGLE_API_KEY`.

## Client (Web UI)

A minimal web UI lives in `client/` and streams responses over `text/event-stream` from `POST /query`.

Start a simple static server (example using Python):

```
cd client
python -m http.server 3000
```

Then open `http://localhost:3000`. Configure the RAG server URL, choose `top_k`, and send a question. The UI displays streamed tokens and the citations from the first SSE event. `Check health` pings `/health` to confirm the index is loaded.

Multi-turn: the UI keeps the transcript locally and sends previous turns as `history` on each query so the server can include conversational context in the prompt.

## Demonstration

[demonstration](https://gist.github.com/user-attachments/assets/90c885d4-02b4-4814-9abc-c930541c1eb5)
