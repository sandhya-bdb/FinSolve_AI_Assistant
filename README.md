# 🚀 FinSolve AI Assistant  
### Enterprise RBAC + RAG Chatbot powered by LLMs, DuckDB, ChromaDB & Streamlit

FinSolve AI Assistant is an enterprise-grade **Document Intelligence System** that enables employees across departments to query organization-specific knowledge securely.

It combines:

- 🔐 **Role-Based Access Control (RBAC)**
- 📄 **Retrieval-Augmented Generation (RAG)**
- 🦙 **Local LLM inference via Ollama**
- 🗄️ **Analytics & metadata via DuckDB**
- 🎨 **Premium Streamlit UI**

This project was built for the **CodeBasics Resume Project Challenge (GenAI Track)** and will be continuously improved with new features and scalability enhancements.

---

## ✨ Key Features

### 🔐 Role-Based Access Control (RBAC)
Each user is assigned a role:

| Role | Access |
|------|--------|
| **C-Level Executives** | Full access |
| **Department Heads (HR, Finance, Engineering, Marketing)** | Department-specific documents |
| **Employees** | General documents only |

LLM responses are restricted based on the user’s access permissions.

---

### 📄 Retrieval-Augmented Generation (RAG) Pipeline
- Documents loaded from `/resources/data/{department}`
- Chunked using **RecursiveCharacterTextSplitter**
- Embedded via **HuggingFace MiniLM-L6-v2**
- Persisted in **Chroma VectorDB**
- Retrieved intelligently based on semantic similarity

---

### 🦙 Local LLM Inference via Ollama
Prompts sent to a locally running model (`llama3.2`) via:

```
http://localhost:11434/api/generate
```

Benefits:
- 🔒 Privacy-first
- 💸 Zero cloud cost
- ⚡ Fast local inference

Works with multiple Ollama models (Llama, Mistral, etc.)

---

### 🗄️ DuckDB for Metadata & Audit Logging
Two important tables are maintained:

| Table | Purpose |
|-------|---------|
| **doc_chunks** | Stores RAG chunk metadata |
| **chat_logs** | Logs all conversations + chunk IDs used |

This ensures **transparency**, **auditability**, and **enterprise security**.

---

### 🎨 Premium Streamlit Frontend
A feature-rich modern UI including:

- 🌗 Dark/Light Mode toggle  
- 💬 Chat interface  
- 📤 Document upload (C-level only)  
- ⚙️ Admin controls (User & role creation)  
- 📘 Role explanation panel  
- 🧩 Tabbed navigation  
- 🪄 Clean answer cards  
- 🔐 Secure login using HTTP Basic Auth  

---

## 🏗️ System Architecture

```
             ┌────────────────────────────────┐
             │          Streamlit UI           │
             │  Login · Chat · Upload · Admin  │
             └──────────────┬─────────────────┘
                            │
                            ▼
                ┌──────────────────────┐
                │      FastAPI API     │
                │ Authentication, RAG  │
                └──────────────┬──────┘
                               │
                               ▼
        ┌───────────────────────────────────────────┐
        │                 RAG Engine                 │
        │  ChromaDB (Embeddings) + DuckDB (Logs)    │
        └───────────────────┬───────────────────────┘
                            │
                            ▼
               ┌────────────────────────┐
               │  Ollama Local LLM      │
               │  llama3.2 / mistral    │
               └────────────────────────┘
```

---

## 🛠️ Tech Stack

### Backend
- FastAPI  
- Python 3.11  
- DuckDB  
- ChromaDB  
- LangChain  
- HuggingFace Sentence Transformers  
- Ollama (Local LLM inference)  

### Frontend
- Streamlit  
- Custom CSS (Premium UI styling)  
- Dark/Light mode switch  

---

## 📂 Project Structure

```
RBAC/
 ├── app/
 │   ├── main.py              # FastAPI backend
 │   ├── UI.py                # Premium Streamlit interface
 │   ├── db.py                # DuckDB setup: metadata + logs
 │   ├── embed_doc.py         # Document ingestion + embeddings
 │   └── chroma_db/           # Vector database files
 │
 ├── resources/
 │   └── data/
 │        ├── hr/
 │        ├── finance/
 │        ├── engineering/
 │        ├── marketing/
 │        └── general/
 │
 ├── environment.yml
 ├── requirements.txt
 └── README.md
```

---

## 🔧 Setup Instructions

### 1️⃣ Clone the repository
```bash
git clone https://github.com/yourusername/FinSolve-AI-Assistant.git
cd FinSolve-AI-Assistant/app
```

### 2️⃣ Create the Conda environment
```bash
conda env create -f environment.yml
conda activate rbac_rag_chatbot
```

### 3️⃣ Ingest and embed documents
```bash
python embed_doc.py
```

### 4️⃣ Start the FastAPI backend
```bash
uvicorn main:app --reload
```

### 5️⃣ Start the Streamlit frontend
```bash
streamlit run UI.py
```

### 6️⃣ Start Ollama (Local LLM server)
```bash
ollama run llama3.2
```

---

## 🧪 Sample Query Flow

1. User logs in  
2. RBAC filters allowed documents  
3. Chroma retrieves relevant chunks  
4. Backend injects context into the prompt  
5. Ollama generates a grounded answer  
6. DuckDB logs all activity  

---

## 🔮 Future Enhancements

- 📊 Analytics Dashboard (DuckDB → Streamlit visual insights)  
- 🏢 Multi-tenant enterprise support  
- 🧠 Fine-tuned domain-specific LLMs  
- 🐳 Docker Compose orchestration  
- 🔐 JWT / OAuth2 authentication  
- 🤖 Agent-to-Agent integration via API keys  

---

## 🙌 Acknowledgements

This project was created for the  
**CodeBasics Resume Project Challenge — GenAI Track**  
and is being expanded into a full production-ready solution.

---

## ⭐ Support  

If you find this project inspiring or helpful,  
**please ⭐ star the repository — it means a lot!** 🌟

