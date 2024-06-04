import glob

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings


def index():
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    docs = []
    for file in glob.glob("documents/*.txt"):
        # Load the document, split it into chunks, embed each chunk and load it into the vector store.
        raw_documents = TextLoader(file).load()
        docs.extend(raw_documents)

    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    documents = text_splitter.split_documents(docs)
    db = FAISS.from_documents(documents, embeddings)

    return db
