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

To use Ollama embeddings instead, pass `--embedding-backend ollama --embedding-model nomic-embed-text:latest` (requires Ollama running locally or `OLLAMA_BASE_URL`).
Note: the Google API expects model ids prefixed with `models/`; the script will normalize common names (e.g., `gemini-embedding-001` → `models/embedding-001`, `text-embedding-004` → `models/text-embedding-004`).

Artifacts are written to `data/faiss_store/`, `data/faiss.index`, and `data/faiss-meta.json`. Customize chunking with `--chunk-size`/`--chunk-overlap` or point `--sources` to local files or directories.

## Server

Start the FastAPI RAG server (expects the FAISS artifacts above). By default it uses Google embeddings (`RAG_EMBEDDING_BACKEND=google`, `RAG_EMBEDDING_MODEL=gemini-embedding-001`) and Gemini for generation (`RAG_LLM_BACKEND=google`, `RAG_LLM_MODEL=gemini-3-pro-preview`, requires `GOOGLE_API_KEY`):

```
uvicorn server.main:app --reload --port 8000
```

Key endpoints:
- `GET /health` — index/metadata status.
- `POST /reload` — reload FAISS store and metadata from disk.
- `POST /query` — body `{ "query": "...", "top_k": 5 }`, responds with `text/event-stream` streaming tokens and a first `citations` event containing source metadata.

Configurable via env vars: `RAG_EMBEDDING_BACKEND`, `RAG_EMBEDDING_MODEL`, `RAG_LLM_BACKEND`, `RAG_LLM_MODEL`, `RAG_INDEX_DIR`, `RAG_INDEX_PATH`, `RAG_METADATA_PATH`, `RAG_TOP_K`, `GOOGLE_API_KEY`, `OLLAMA_BASE_URL`.

To switch generation to Ollama instead: set `RAG_LLM_BACKEND=ollama`, `RAG_LLM_MODEL=phi3:3.8b`, and ensure Ollama is running (`ollama pull phi3:3.8b`).

## Client (Web UI)

A minimal web UI lives in `client/` and streams responses over `text/event-stream` from `POST /query`.

Start a simple static server (example using Python):

```
cd client
python -m http.server 3000
```

Then open `http://localhost:3000`. Configure the RAG server URL, choose `top_k`, and send a question. The UI displays streamed tokens and the citations from the first SSE event. `Check health` pings `/health` to confirm the index is loaded.

Multi-turn: the UI keeps the transcript locally and sends previous turns as `history` on each query so the server can include conversational context in the prompt.

## Ollama Demonstration

[demonstration](https://gist.github.com/user-attachments/assets/f97ec6ec-ae5c-48a6-981a-c51edfad94c8)
