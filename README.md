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
