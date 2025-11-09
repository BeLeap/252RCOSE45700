from langchain_core.documents import Document
from langchain_text_splitters import CharacterTextSplitter

def split(docs: list[Document]) -> list[Document]:
    splitter = CharacterTextSplitter(
        separator="\n\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )

    splitted_docs = splitter.split_documents(docs)

    print(f"{len(docs)} documents splitted into {len(splitted_docs)} documents.")

    return splitted_docs
