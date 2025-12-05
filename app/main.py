# main.py
from typing import Dict
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    UnstructuredFileLoader,
    CSVLoader,
    TextLoader,
    PyPDFLoader,
)

from db import init_db, log_chat, log_doc_chunk

import uuid
import os
import requests

app = FastAPI()
security = HTTPBasic()

# -----------------------------
# Init DB + Vector DB
# -----------------------------
init_db()

embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vectordb = Chroma(
    persist_directory="chroma_db",
    embedding_function=embedding_function,
    collection_name="company_docs",
)

# -----------------------------
# Dummy Users DB
# -----------------------------
users_db: Dict[str, Dict[str, str]] = {
    "Deb": {"password": "password123", "role": "engineering"},
    "Ved": {"password": "securepass", "role": "marketing"},
    "Binoy": {"password": "financepass", "role": "finance"},
    "sangit": {"password": "hrpass123", "role": "hr"},
    "sandhya": {"password": "ceopass", "role": "c-levelexecutives"},
    "Karabi": {"password": "employeepass", "role": "employee"},
}


def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    username = credentials.username
    password = credentials.password
    user = users_db.get(username)

    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"username": username, "role": user["role"]}


@app.get("/login")
def login(user: Dict[str, str] = Depends(authenticate)):
    return {"message": f"Welcome {user['username']}!", "role": user["role"]}


# -----------------------------
# Chat Request Model
# -----------------------------
class ChatRequest(BaseModel):
    user: Dict[str, str]
    message: str


# -----------------------------
# CHAT Endpoint
# -----------------------------
@app.post("/chat")
def chat(req: ChatRequest):
    user = req.user
    message = req.message
    role = user["role"].lower()

    # Determine allowed docs
    if "c-levelexecutives" in role:
        docs = vectordb.similarity_search(message, k=4)
    elif role == "employee":
        docs = vectordb.similarity_search(message, k=4, filter={"role": "general"})
    else:
        docs = vectordb.similarity_search(message, k=4, filter={"role": role})

    if not docs:
        return {
            "username": user["username"],
            "role": user["role"],
            "query": message,
            "response": "No relevant documents found for your role.",
            "sources": []
        }

    # Build extended context
    context = "\n\n-----\n\n".join([d.page_content for d in docs])

    # High-quality system prompt
    prompt = f"""
You are FinSolve-AI, an enterprise assistant. 
Your task is to give **long, detailed, well-structured answers** using ONLY the context provided.

### Instructions:
- Provide a **clear, multi-paragraph answer**
- Include explanations, examples, reasoning steps
- If the context contains multiple points, **summarize and connect them**
- Never guess beyond the provided context
- Write in a professional but easy-to-understand tone
- Minimum length: **6–10 sentences**

### User Role:
{user['role']}

### Context:
{context}

### Question:
{message}

### Final Answer (detailed and structured):
"""

    # Call Ollama LLM with extended generation parameters
    payload = {
        "model": "llama3.2",
        "prompt": prompt,
        "stream": False,

        # Important: allow long answers
        "num_predict": -1,        # unlimited tokens
        "temperature": 0.2,       # more factual
        "top_p": 0.9,             # smoother generation
        "repeat_penalty": 1.1     # avoid short repetitive output
    }

    response = requests.post("http://localhost:11434/api/generate", json=payload)

    if response.status_code != 200:
        raise HTTPException(500, f"Ollama error: {response.text}")

    llm_answer = response.json().get("response", "").strip()

    sources_list = [d.metadata.get("source", "unknown") for d in docs]
    chunk_ids = [d.metadata.get("chunk_id", "") for d in docs]

    # Save audit log
    log_chat(
        username=user["username"],
        role=user["role"],
        query=message,
        chunk_ids=chunk_ids,
        answer_text=llm_answer
    )

    return {
        "username": user["username"],
        "role": user["role"],
        "query": message,
        "response": llm_answer,
        "sources": sources_list
    }

    # Prepare for UI + logging
    docs_list = [{"content": d.page_content, "metadata": d.metadata} for d in docs]
    sources_list = [d.metadata.get("source", "unknown") for d in docs]
    # ✅ use chunk_id everywhere
    chunk_ids = [d.metadata.get("chunk_id", "") for d in docs]

    # Log into DuckDB
    log_chat(
        username=user["username"],
        role=user["role"],
        query=message,
        chunk_ids=chunk_ids,
        answer_text=llm_answer,
    )

    return {
        "username": user["username"],
        "role": user["role"],
        "query": message,
        "response": llm_answer,
        "docs": docs_list,
        "sources": sources_list,
    }


# -----------------------------
# Upload Documents (Admin Only)
# -----------------------------
@app.post("/upload-docs")
def upload_docs(
    role: str = Form(...),
    file: UploadFile = File(...),
    user: Dict[str, str] = Depends(authenticate),
):
    # only c-level can upload
    if "c-levelexecutives" not in user["role"].lower():
        raise HTTPException(status_code=403, detail="Not allowed")

    filename = file.filename
    temp_path = f"temp_{filename}"

    with open(temp_path, "wb") as f:
        f.write(file.file.read())

    # Load file
    if filename.endswith(".md") or filename.endswith(".txt"):
        try:
            loader = UnstructuredFileLoader(temp_path)
            docs = loader.load()
        except Exception:
            loader = TextLoader(temp_path, encoding="utf-8")
            docs = loader.load()
    elif filename.endswith(".csv"):
        loader = CSVLoader(temp_path)
        docs = loader.load()
    elif filename.endswith(".pdf"):
        loader = PyPDFLoader(temp_path)
        docs = loader.load()
    else:
        os.remove(temp_path)
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # Split docs
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_docs = splitter.split_documents(docs)

    # Store in Chroma + DuckDB
    for d in split_docs:
        d.metadata["role"] = role.lower()
        d.metadata["department"] = role.lower()
        d.metadata["source"] = filename
        d.metadata["file_name"] = filename

        chunk_id = str(uuid.uuid4())
        d.metadata["chunk_id"] = chunk_id  # ✅ consistent

        log_doc_chunk(
            chunk_id=chunk_id,
            file_name=filename,
            role=role.lower(),
            department=role.lower(),
            source=filename,
        )

    vectordb.add_documents(split_docs)

    os.remove(temp_path)

    return {"message": f"Uploaded {len(split_docs)} chunks to role '{role}'."}


# -----------------------------
# Roles Endpoint (for UI)
# -----------------------------
@app.get("/roles")
def get_roles():
    return {"roles": sorted(list(set([u["role"] for u in users_db.values()])))}


# -----------------------------
# Create User
# -----------------------------
@app.post("/create-user")
def create_user(
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    user: Dict[str, str] = Depends(authenticate),
):
    if "c-levelexecutives" not in user["role"].lower():
        raise HTTPException(status_code=403, detail="Not allowed")

    if username in users_db:
        raise HTTPException(status_code=400, detail="User already exists")

    users_db[username] = {"password": password, "role": role}

    return {"message": f"User '{username}' created."}


# -----------------------------
# Create Role (dummy, stored in memory)
# -----------------------------
@app.post("/create-role")
def create_role(
    role_name: str = Form(...),
    user: Dict[str, str] = Depends(authenticate),
):
    if "c-levelexecutives" not in user["role"].lower():
        raise HTTPException(status_code=403, detail="Not allowed")

    # In a real app you would persist this in DB; for now, just echo back
    return {"message": f"Role '{role_name}' added."}
