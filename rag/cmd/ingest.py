import argparse
import glob

from ingest.load_files import load_files
from ingest.splitter import character
from ingest.vector_store.faiss_ollama import faiss_ollama


def main():
    parser = argparse.ArgumentParser(prog="ingest")
    parser.add_argument("--path")

    args = parser.parse_args()

    target_files = glob.glob(args.path)
    print(f"{len(target_files)} files will be ingested!")

    docs = load_files(target_files=target_files)

    character_splitter = character.CharacterSplitter()
    docs = character_splitter.split(docs)

    vs = faiss_ollama()
    vs.add_documents(docs)

    results = vs.similarity_search("God Object", k=2)
    print(results[0].page_content)


if __name__ == "__main__":
    main()
