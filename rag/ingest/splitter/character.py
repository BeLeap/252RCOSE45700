from langchain_core.documents import Document
from langchain_text_splitters import CharacterTextSplitter

from ingest.splitter import Splitter

class CharacterSplitter(Splitter):
    def split(self, docs: list[Document]) -> list[Document]:
        splitter = CharacterTextSplitter(
            separator="\n\n",
            chunk_size=500,
            chunk_overlap=200,
            length_function=len,
            is_separator_regex=False,
        )

        splitted_docs = splitter.split_documents(docs)

        print(f"{len(docs)} documents splitted into {len(splitted_docs)} documents.")

        return splitted_docs
