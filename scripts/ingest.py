#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Sequence, Tuple
from urllib.parse import urlparse

import faiss
import requests
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

DEFAULT_SOURCES = [
    "https://korea-sw-26-s3.s3.us-east-1.amazonaws.com/2019-Shareholder-Letter.pdf",
    "https://korea-sw-26-s3.s3.us-east-1.amazonaws.com/2020-Shareholder-Letter.pdf",
    "https://korea-sw-26-s3.s3.us-east-1.amazonaws.com/2021-Shareholder-Letter.pdf",
    "https://korea-sw-26-s3.s3.us-east-1.amazonaws.com/2022-Shareholder-Letter.pdf",
]


class IngestError(Exception):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build FAISS index from documents.")
    parser.add_argument(
        "--sources",
        nargs="+",
        default=DEFAULT_SOURCES,
        help="Local file/dir paths or URLs to ingest. Defaults to the provided S3 PDFs.",
    )
    parser.add_argument(
        "--download-dir",
        default="documents",
        help="Directory to store downloaded sources.",
    )
    parser.add_argument(
        "--index-dir",
        default="data/faiss_store",
        help="Directory to store the LangChain FAISS artifacts.",
    )
    parser.add_argument(
        "--index-path",
        default="data/faiss.index",
        help="Path to a standalone faiss index file.",
    )
    parser.add_argument(
        "--metadata-path",
        default="data/faiss-meta.json",
        help="Path to write chunk metadata for downstream use.",
    )
    parser.add_argument(
        "--embedding-backend",
        choices=["ollama", "google"],
        default="google",
        help="Embedding provider backend. Defaults to google.",
    )
    parser.add_argument(
        "--embedding-model",
        default="gemini-embedding-001",
        help="Embedding model id (backend-specific). Defaults to gemini-embedding-001 for Google.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=800,
        help="Chunk size for RecursiveCharacterTextSplitter.",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="Chunk overlap for RecursiveCharacterTextSplitter.",
    )
    parser.add_argument(
        "--verify-query",
        help="Optional query to verify the index by running a similarity search.",
    )
    parser.add_argument(
        "--verify-top-k",
        type=int,
        default=3,
        help="Number of results to show when verifying the index.",
    )
    return parser.parse_args()


def normalize_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    non_empty = [line for line in lines if line]
    return "\n".join(non_empty)


def download_url(url: str, download_dir: Path) -> Path:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise IngestError(f"Unsupported URL scheme for {url}")

    filename = Path(parsed.path).name or "downloaded"
    destination = download_dir / filename
    download_dir.mkdir(parents=True, exist_ok=True)

    if destination.exists():
        return destination

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise IngestError(f"Failed to download {url}: {exc}") from exc

    destination.write_bytes(response.content)
    return destination


def prepare_sources(sources: Sequence[str], download_dir: Path) -> List[Tuple[Path, str]]:
    prepared: List[Tuple[Path, str]] = []
    for item in sources:
        parsed = urlparse(item)
        if parsed.scheme in ("http", "https"):
            path = download_url(item, download_dir)
            prepared.append((path, item))
        else:
            path = Path(item).expanduser()
            if not path.exists():
                raise IngestError(f"Source not found: {item}")
            prepared.append((path, str(path)))
    return prepared


def load_from_path(path: Path, source_label: str) -> List:
    documents = []
    if path.is_dir():
        for file_path in sorted(path.rglob("*")):
            if file_path.is_file():
                documents.extend(load_file(file_path, source_label))
    else:
        documents.extend(load_file(path, source_label))
    return documents


def load_file(file_path: Path, source_label: str) -> List:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        loader = PyPDFLoader(str(file_path))
    else:
        loader = TextLoader(str(file_path), autodetect_encoding=True)

    docs = loader.load()
    for doc in docs:
        doc.page_content = normalize_text(doc.page_content)
        doc.metadata["source"] = source_label
        doc.metadata["path"] = str(file_path)
    return docs


def chunk_documents(documents: List, chunk_size: int, chunk_overlap: int) -> List:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.split_documents(documents)
    for idx, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = idx
        chunk.metadata["chunk_size"] = len(chunk.page_content)
    return chunks


def build_embeddings(backend: str, model: str):
    if backend == "google":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise IngestError("GOOGLE_API_KEY is not set.")
        normalized_model = normalize_google_model(model)
        return GoogleGenerativeAIEmbeddings(model=normalized_model, google_api_key=api_key)

    if backend == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL")
        # base_url can be None to use default localhost
        return OllamaEmbeddings(model=model, base_url=base_url)

    raise IngestError(f"Unsupported embedding backend: {backend}")


def normalize_google_model(model: str) -> str:
    legacy_map = {
        "gemini-embedding-001": "models/embedding-001",
        "embedding-001": "models/embedding-001",
        "text-embedding-004": "models/text-embedding-004",
    }
    if model in legacy_map:
        return legacy_map[model]
    if model.startswith("models/"):
        return model
    return f"models/{model}"


def persist_index(
    vector_store: FAISS,
    index_dir: Path,
    index_path: Path,
    metadata_path: Path,
) -> None:
    index_dir.mkdir(parents=True, exist_ok=True)
    vector_store.save_local(str(index_dir))

    index_path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(vector_store.index, str(index_path))

    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = []
    for doc_id, doc in vector_store.docstore._dict.items():
        metadata.append(
            {
                "doc_id": doc_id,
                "source": doc.metadata.get("source"),
                "path": doc.metadata.get("path"),
                "chunk_id": doc.metadata.get("chunk_id"),
                "chunk_size": doc.metadata.get("chunk_size"),
                "page": doc.metadata.get("page"),
                "preview": doc.page_content[:160].replace("\n", " "),
            }
        )
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def verify_index(vector_store: FAISS, query: str, top_k: int) -> None:
    print(f"Verifying index with query: {query!r}")
    results = vector_store.similarity_search_with_score(query, k=top_k)
    for rank, (doc, score) in enumerate(results, start=1):
        source = doc.metadata.get("source", "unknown")
        chunk_id = doc.metadata.get("chunk_id")
        page = doc.metadata.get("page")
        print(f"[{rank}] score={score:.4f} source={source} chunk_id={chunk_id} page={page}")
        preview = doc.page_content[:200].replace("\n", " ")
        print(f"      preview: {preview}")


def main() -> int:
    args = parse_args()

    if args.chunk_size <= args.chunk_overlap:
        print("chunk-size must be greater than chunk-overlap", file=sys.stderr)
        return 1

    try:
        prepared_sources = prepare_sources(args.sources, Path(args.download_dir))
        documents = []
        for path, source_label in prepared_sources:
            documents.extend(load_from_path(path, source_label))
        if not documents:
            raise IngestError("No documents were loaded.")

        chunks = chunk_documents(documents, args.chunk_size, args.chunk_overlap)
        embeddings = build_embeddings(args.embedding_backend, args.embedding_model)
        vector_store = FAISS.from_documents(chunks, embeddings)
        persist_index(
            vector_store,
            Path(args.index_dir),
            Path(args.index_path),
            Path(args.metadata_path),
        )

        if args.verify_query:
            verify_index(vector_store, args.verify_query, args.verify_top_k)

        print(
            f"Ingest complete. Stored {len(chunks)} chunks from {len(documents)} documents "
            f"into {args.index_dir} and {args.index_path} with metadata at {args.metadata_path}."
        )
        return 0
    except IngestError as exc:
        print(f"Ingest failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
