"""
Loads department documents, splits into chunks, generates embeddings,
stores metadata in DuckDB, and saves embeddings into Chroma vector DB.
"""

import os
import shutil
import uuid

from langchain_community.document_loaders import (
    UnstructuredFileLoader,
    CSVLoader,
    TextLoader,
    PyPDFLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# DuckDB imports
from db import init_db, log_doc_chunk

# ----------------------------
# Init DuckDB
# ----------------------------
init_db()

# ----------------------------
# Directory / DB config
# ----------------------------
BASE_DIR = "../resources/data"      # folder containing department subfolders
CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "company_docs"

# Embeddings
embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Start fresh Chroma DB
shutil.rmtree(CHROMA_DIR, ignore_errors=True)

all_split_docs = []

# ----------------------------
# Process each department
# ----------------------------
for department in os.listdir(BASE_DIR):
    dept_path = os.path.join(BASE_DIR, department)
    if not os.path.isdir(dept_path):
        continue

    print(f"\n🔍 Processing department: {department}")
    dept_docs = []

    for fname in os.listdir(dept_path):
        file_path = os.path.join(dept_path, fname)
        if not os.path.isfile(file_path):
            continue

        try:
            if fname.endswith(".md") or fname.endswith(".txt"):
                try:
                    loader = UnstructuredFileLoader(file_path)
                    docs = loader.load()
                except Exception:
                    loader = TextLoader(file_path, encoding="utf-8")
                    docs = loader.load()

            elif fname.endswith(".csv"):
                loader = CSVLoader(file_path)
                docs = loader.load()

            elif fname.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
                docs = loader.load()

            else:
                # skip unsupported formats
                continue

            # add basic metadata at document level
            for d in docs:
                d.metadata["file_name"] = fname
                d.metadata["role"] = department.lower()
                d.metadata["department"] = department.lower()
                d.metadata["source"] = fname

            dept_docs.extend(docs)

        except Exception as e:
            print(f"❌ Failed to load {file_path}: {e}")

    if not dept_docs:
        print(f"⚠️ No documents found for: {department}")
        continue

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_docs = splitter.split_documents(dept_docs)

    for doc in split_docs:
        # unique ID for this chunk
        chunk_id = str(uuid.uuid4())
        doc.metadata["chunk_id"] = chunk_id

        # make sure these are present
        role = doc.metadata.get("role", department.lower())
        dept = doc.metadata.get("department", department.lower())
        source = doc.metadata.get("source", doc.metadata.get("file_name", "unknown"))
        file_name = doc.metadata.get("file_name", source)

        # log chunk metadata into DuckDB
        log_doc_chunk(
            chunk_id=chunk_id,
            file_name=file_name,
            role=role,
            department=dept,
            source=source,
        )

    all_split_docs.extend(split_docs)
    print(f"✅ Created {len(split_docs)} chunks for {department}")

# ----------------------------
# Store chunks in Chroma
# ----------------------------
vectordb = Chroma.from_documents(
    documents=all_split_docs,
    embedding=embedding_function,
    persist_directory=CHROMA_DIR,
    collection_name=COLLECTION_NAME,
)

print(f"\n🎉 Successfully stored {len(all_split_docs)} chunks in Chroma DB.")
