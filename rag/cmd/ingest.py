import argparse
import glob
from langchain_unstructured import UnstructuredLoader


def main():
    parser = argparse.ArgumentParser(prog="ingest")
    parser.add_argument("--path")

    args = parser.parse_args()

    target_files = glob.glob(args.path)
    print(f"{len(target_files)} files will be ingested!")

    loader = UnstructuredLoader(
        target_files,
        chunking_strategy="basic",
        max_characters=999999999,
    )

    docs = loader.load()

    print(f"{len(docs)} documents to load")


if __name__ == "__main__":
    main()
