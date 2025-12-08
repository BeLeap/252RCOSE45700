from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain.schema import SystemMessage
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_ollama import ChatOllama, OllamaEmbeddings
from pydantic import BaseModel, Field, PositiveInt

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class HistoryTurn(BaseModel):
    role: str = Field(..., description="Role of the speaker, e.g., 'user' or 'assistant'.")
    content: str = Field(..., min_length=1, description="Message content.")


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User query to run against the index.")
    top_k: PositiveInt = Field(5, description="Number of chunks to retrieve.")
    history: Optional[List[HistoryTurn]] = Field(
        default=None,
        description="Optional prior turns to enable multi-turn context.",
    )


class RagConfig(BaseModel):
    embedding_backend: str = Field(default=os.getenv("RAG_EMBEDDING_BACKEND", "google"))
    embedding_model: str = Field(default=os.getenv("RAG_EMBEDDING_MODEL", "gemini-embedding-001"))
    llm_backend: str = Field(default=os.getenv("RAG_LLM_BACKEND", "google"))
    llm_model: str = Field(default=os.getenv("RAG_LLM_MODEL", "gemini-3-pro-preview"))
    index_dir: Path = Field(default=Path(os.getenv("RAG_INDEX_DIR", "data/faiss_store")))
    index_path: Path = Field(default=Path(os.getenv("RAG_INDEX_PATH", "data/faiss.index")))
    metadata_path: Path = Field(default=Path(os.getenv("RAG_METADATA_PATH", "data/faiss-meta.json")))
    default_top_k: PositiveInt = Field(default=int(os.getenv("RAG_TOP_K", "5")))


app = FastAPI(title="RAG Server", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_metadata(path: Path) -> List[Dict]:
    if not path.exists():
        raise FileNotFoundError(f"Metadata file not found at {path}")
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
        return content if isinstance(content, list) else []
    except Exception as exc:  # pylint: disable=broad-except
        raise RuntimeError(f"Failed to read metadata at {path}: {exc}") from exc


def get_embeddings(config: RagConfig):
    if config.embedding_backend == "google":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY is required for google embeddings.")
        model_name = normalize_google_model(config.embedding_model)
        return GoogleGenerativeAIEmbeddings(model=model_name, google_api_key=api_key)

    if config.embedding_backend == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL")
        return OllamaEmbeddings(model=config.embedding_model, base_url=base_url)

    raise RuntimeError(f"Unsupported embedding backend: {config.embedding_backend}")


def get_llm(config: RagConfig):
    if config.llm_backend == "google":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY is required for google LLM backend.")
        return ChatGoogleGenerativeAI(
            model=config.llm_model,
            google_api_key=api_key,
            streaming=True,
            temperature=0,
        )

    if config.llm_backend == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL")
        return ChatOllama(
            model=config.llm_model,
            base_url=base_url,
            temperature=0,
        )

    raise RuntimeError(f"Unsupported LLM backend: {config.llm_backend}")


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


def load_faiss_store(config: RagConfig, embeddings) -> FAISS:
    if not config.index_dir.exists():
        raise FileNotFoundError(f"Index directory not found at {config.index_dir}")
    store = FAISS.load_local(
        str(config.index_dir),
        embeddings,
        allow_dangerous_deserialization=True,
    )
    return store


@lru_cache(maxsize=1)
def get_config() -> RagConfig:
    return RagConfig()


class RagState:
    def __init__(self):
        self.store: Optional[FAISS] = None
        self.metadata: List[Dict] = []
        self.config: RagConfig = get_config()

    def load(self) -> None:
        config = self.config
        embeddings = get_embeddings(config)
        self.store = load_faiss_store(config, embeddings)
        self.metadata = load_metadata(config.metadata_path)
        logger.info("Loaded FAISS index from %s", config.index_dir)

    def ensure_ready(self) -> None:
        if self.store is None or self.metadata is None:
            self.load()


state = RagState()


def build_prompt(query: str, docs: Iterable[Tuple], history: Optional[List[HistoryTurn]] = None) -> str:
    context_lines = []
    for idx, (doc, score) in enumerate(docs, start=1):
        citation = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page")
        chunk_id = doc.metadata.get("chunk_id")
        preview = doc.page_content.replace("\n", " ")
        context_lines.append(
            f"[{idx}] source={citation} page={page} chunk={chunk_id} score={score:.4f}: {preview}"
        )
    context = "\n".join(context_lines)
    history_text = ""
    if history:
        formatted_turns = []
        for turn in history:
            role = turn.role.lower()
            if role not in {"user", "assistant"}:
                role = "user"
            formatted_turns.append(f"{role}: {turn.content}")
        history_text = "\nPrevious conversation:\n" + "\n".join(formatted_turns) + "\n"

    return (
        "You are a helpful assistant. Answer the user question using ONLY the provided context. "
        "Cite sources with their source and chunk id. If the answer is not in the context, say you "
        "do not know.\n"
        f"{history_text}\n"
        f"Context:\n{context}\n\nQuestion: {query}"
    )


def format_sse(event: str, data: Dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def stream_response(llm, prompt: str, citations: List[Dict]):
    def event_generator():
        yield format_sse("citations", {"citations": citations})
        for chunk in llm.stream([SystemMessage(content=prompt)]):
            if chunk.content:
                yield format_sse("token", {"token": chunk.content})
        yield format_sse("done", {"status": "ok"})

    return event_generator()


@app.on_event("startup")
def startup_event():
    try:
        state.load()
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Failed to preload index: %s", exc)


@app.get("/health")
def health():
    config = state.config
    ready = state.store is not None
    meta_count = len(state.metadata) if state.metadata else 0
    return {
        "status": "ok" if ready else "not_loaded",
        "index_dir": str(config.index_dir),
        "metadata_path": str(config.metadata_path),
        "metadata_count": meta_count,
    }


@app.post("/reload")
def reload_index():
    try:
        state.load()
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"status": "reloaded"}


@app.post("/query")
def query_rag(request: QueryRequest = Body(...)):
    state.ensure_ready()
    if state.store is None:
        raise HTTPException(status_code=503, detail="Index not loaded.")

    k = request.top_k or state.config.default_top_k
    results = state.store.similarity_search_with_score(request.query, k=k)
    citations = []
    for doc, score in results:
        safe_score = float(score) if score is not None else None
        citations.append(
            {
                "source": doc.metadata.get("source"),
                "chunk_id": doc.metadata.get("chunk_id"),
                "page": doc.metadata.get("page"),
                "path": doc.metadata.get("path"),
                "score": safe_score,
                "preview": doc.page_content[:200].replace("\n", " "),
            }
        )

    prompt = build_prompt(request.query, results, request.history)
    try:
        llm = get_llm(state.config)
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    generator = stream_response(llm, prompt, citations)
    return StreamingResponse(generator, media_type="text/event-stream")
