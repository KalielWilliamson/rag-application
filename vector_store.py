import glob
import os
import threading
import time
import uuid

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from conversation_state_store import *


class DocumentIndexer:
    def __init__(self, model_name="all-MiniLM-L6-v2", vector_db_path="vector_db.faiss"):
        self.model_name = model_name
        self.vector_db_path = vector_db_path
        self.embeddings = HuggingFaceEmbeddings(model_name=self.model_name)
        self.text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        self.db = self.load_vector_db()
        self.redis_client = RedisClient()
        self.available_documents = []
        self.index()
        self.listen_for_updates()

    def save_vector_db(self):
        self.db.save_local(self.vector_db_path)

    def load_vector_db(self):
        if os.path.exists(self.vector_db_path):
            return FAISS.load_local(self.vector_db_path, self.embeddings, allow_dangerous_deserialization=True)
        return None

    def reload_vector_db(self):
        self.db = self.load_vector_db()

    def index_single_document(self, document_path=None, raw_text=None):
        if document_path is not None:
            raw_document: str = TextLoader(document_path).load()[0].page_content
            filename = document_path.split('/')[-1]
        elif raw_text is not None:
            raw_document: str = raw_text
            filename = f"{uuid.uuid4()}.txt"
        else:
            raise ValueError("Either document_path or raw_text must be provided")

        with open(f"documents/{filename}.txt", "w") as f:
            f.write(raw_document)

        self.index()

    def get_retriever(self):

        # Load the vector database if it hasn't been loaded yet
        if self.db is None:
            self.db = self.load_vector_db()

        # if the db is still None, then we need to index the documents
        if self.db is None:
            self.index()

        return self.db.as_retriever()

    def index(self):
        self.available_documents = []
        if self.db is None:
            docs = []
            for file in glob.glob("documents/*.txt"):
                print(f"Indexing {file}")
                raw_documents = TextLoader(file).load()
                docs.extend(raw_documents)
                self.available_documents.append(file)

            documents = self.text_splitter.split_documents(docs)
            self.db = FAISS.from_documents(documents, self.embeddings)
            self.save_vector_db()

        return self.db

    def clear(self):
        self.db = None
        self.save_vector_db()
        for file in glob.glob("documents/*.txt"):
            os.remove(file)

    def _listen_for_updates_thread(self):
        while True:
            processed_documents = self.redis_client.get(PROCESSED_DOCUMENTS)
            unprocessed_documents = self.redis_client.get(UNPROCESSED_DOCUMENTS)

            # if there are any unprocessed documents, take them off the queue, save them to disk, and index them
            if unprocessed_documents:
                document = unprocessed_documents.pop(0)
                self.redis_client.set(UNPROCESSED_DOCUMENTS, unprocessed_documents)
                self.index_single_document(raw_text=document)
                self.redis_client.append(PROCESSED_DOCUMENTS, document)

            # if the local db is missing any processed_documents, reload the db
            if processed_documents and (set(processed_documents) != set(self.available_documents)):
                self.reload_vector_db()
                self.available_documents = processed_documents

            time.sleep(1)

    def listen_for_updates(self):
        threading.Thread(target=self._listen_for_updates_thread).start()


if __name__ == "__main__":
    indexer = DocumentIndexer()
    indexer.index()

    while True:
        time.sleep(1)
