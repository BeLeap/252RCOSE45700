# COSE457

## Ingest

Prepare a Python environment (e.g., `python -m venv .venv && source .venv/bin/activate`) and install dependencies:

```
pip install -r requirements.txt
```

By default ingestion uses Ollama embeddings (`nomic-embed-text:latest`). Ensure Ollama is running locally (or set `OLLAMA_BASE_URL`) and then build the FAISS index (defaults download the provided S3 PDFs):

```
python scripts/ingest.py \
  --sources https://korea-sw-26-s3.s3.us-east-1.amazonaws.com/2019-Shareholder-Letter.pdf \
           https://korea-sw-26-s3.s3.us-east-1.amazonaws.com/2020-Shareholder-Letter.pdf \
           https://korea-sw-26-s3.s3.us-east-1.amazonaws.com/2021-Shareholder-Letter.pdf \
           https://korea-sw-26-s3.s3.us-east-1.amazonaws.com/2022-Shareholder-Letter.pdf \
  --verify-query "What was emphasized about cash flow?"
```

To use Gemini embeddings instead, provide `--embedding-backend google --embedding-model gemini-embedding-001` and set `GOOGLE_API_KEY`.

Artifacts are written to `data/faiss_store/`, `data/faiss.index`, and `data/faiss-meta.json`. Customize chunking with `--chunk-size`/`--chunk-overlap` or point `--sources` to local files or directories.

## Server

Start the FastAPI RAG server (expects the FAISS artifacts above). By default it uses Ollama embeddings (`RAG_EMBEDDING_BACKEND=ollama`, `RAG_EMBEDDING_MODEL=nomic-embed-text:latest`) and Ollama `phi3:3.8b` for generation (`RAG_LLM_BACKEND=ollama`, `RAG_LLM_MODEL=phi3:3.8b`). Ensure Ollama is running and the model is available locally (`ollama pull phi3:3.8b`):

```
uvicorn server.main:app --reload --port 8000
```

Key endpoints:
- `GET /health` — index/metadata status.
- `POST /reload` — reload FAISS store and metadata from disk.
- `POST /query` — body `{ "query": "...", "top_k": 5 }`, responds with `text/event-stream` streaming tokens and a first `citations` event containing source metadata.

Configurable via env vars: `RAG_EMBEDDING_BACKEND`, `RAG_EMBEDDING_MODEL`, `RAG_LLM_BACKEND`, `RAG_LLM_MODEL`, `RAG_INDEX_DIR`, `RAG_INDEX_PATH`, `RAG_METADATA_PATH`, `RAG_TOP_K`, `GOOGLE_API_KEY`, `OLLAMA_BASE_URL`.

To switch generation to Gemini instead of Ollama: set `RAG_LLM_BACKEND=google`, `RAG_LLM_MODEL=gemini-3-pro-preview`, and provide `GOOGLE_API_KEY`.

## Client (Web UI)

A minimal web UI lives in `client/` and streams responses over `text/event-stream` from `POST /query`.

Start a simple static server (example using Python):

```
cd client
python -m http.server 3000
```

Then open `http://localhost:3000`. Configure the RAG server URL, choose `top_k`, and send a question. The UI displays streamed tokens and the citations from the first SSE event. `Check health` pings `/health` to confirm the index is loaded.

Multi-turn: the UI keeps the transcript locally and sends previous turns as `history` on each query so the server can include conversational context in the prompt.
