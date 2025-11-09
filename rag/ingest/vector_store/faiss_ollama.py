from langchain_community.vectorstores import FAISS
from langchain_core.vectorstores import VectorStore
from langchain_ollama import OllamaEmbeddings
from langchain_community.docstore.in_memory import InMemoryDocstore
import faiss

def faiss_ollama() -> VectorStore:
    embeddings = OllamaEmbeddings(
        model="phi3:3.8b",
    )
    index = faiss.IndexFlatL2(len(embeddings.embed_query("hello world")))

    return FAISS(
        embedding_function=embeddings,
        index=index,
        docstore=InMemoryDocstore(),
        index_to_docstore_id={},
    )
    
