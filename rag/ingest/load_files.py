from langchain_unstructured import UnstructuredLoader

def load_files(target_files: list[str]):
    loader = UnstructuredLoader(
        target_files,
        chunking_strategy="basic",
        max_characters=999999999,
    )

    docs = loader.load()

    print(f"{len(docs)} documents to load")
