# COSE457

## Ingest

Prepare a Python environment (e.g., `python -m venv .venv && source .venv/bin/activate`) and install dependencies:

```
pip install -r requirements.txt
```

Set your Gemini API key (`GOOGLE_API_KEY`) in the environment or `.env`, then build the FAISS index (defaults download the provided S3 PDFs):

```
python scripts/ingest.py \
  --sources https://korea-sw-26-s3.s3.us-east-1.amazonaws.com/2019-Shareholder-Letter.pdf \
           https://korea-sw-26-s3.s3.us-east-1.amazonaws.com/2020-Shareholder-Letter.pdf \
           https://korea-sw-26-s3.s3.us-east-1.amazonaws.com/2021-Shareholder-Letter.pdf \
           https://korea-sw-26-s3.s3.us-east-1.amazonaws.com/2022-Shareholder-Letter.pdf \
  --verify-query "What was emphasized about cash flow?"
```

Artifacts are written to `data/faiss_store/`, `data/faiss.index`, and `data/faiss-meta.json`. Customize chunking with `--chunk-size`/`--chunk-overlap` or point `--sources` to local files or directories.
