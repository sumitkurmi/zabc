# AI-Assisted Network Complaint Portal (MNNIT Allahabad)

An AI-assisted web portal where students report network problems and troubleshoot issues using a Retrieval-Augmented Generation (RAG) assistant. Built with React, Vite, TypeScript, Tailwind CSS, FastAPI, MongoDB, and ChromaDB.

## 📊 Repository Metrics & Stats

<p align="center">
  <img src="https://img.shields.io/github/languages/top/sureshkumarhere/Semester_7_Project?style=for-the-badge&color=blue" alt="Top Language" />
  <img src="https://img.shields.io/github/languages/count/sureshkumarhere/Semester_7_Project?style=for-the-badge&color=green" alt="Total Languages" />
  <img src="https://img.shields.io/github/commit-activity/m/sureshkumarhere/Semester_7_Project?style=for-the-badge&color=orange" alt="Commits per Month" />
  <img src="https://img.shields.io/github/issues-closed/sureshkumarhere/Semester_7_Project?style=for-the-badge&color=purple" alt="Issues Fixed" />
</p>

<p align="center">
  <img src="https://img.shields.io/github/languages/code-size/sureshkumarhere/Semester_7_Project?style=flat-square&label=code%20size" alt="Code Size" />
  <img src="https://img.shields.io/github/contributors/sureshkumarhere/Semester_7_Project?style=flat-square" alt="Contributors" />
  <img src="https://img.shields.io/github/repo-size/sureshkumarhere/Semester_7_Project?style=flat-square" alt="Repo Size" />
  <img src="https://img.shields.io/github/last-commit/sureshkumarhere/Semester_7_Project?style=flat-square" alt="Last Commit" />
</p>



## 🛠️ Tech Stack

| Component | Technology |
| --- | --- |
| **Frontend** | React 18, Vite, TypeScript, Tailwind CSS, TanStack Query, Lucide Icons |
| **Backend** | Python 3.11+, FastAPI, Uvicorn, SlowAPI (Rate Limiting), Pydantic v2 |
| **Database** | MongoDB (Motor async driver) |
| **Vector Store** | ChromaDB (Local persistent directory) |
| **LLM & Embeddings** | A multillm orchestrator with GEMINI ,OPENAI ,GROK ,mock fallback and local `sentence-transformers` |
| **Doc Parsers** | `pypdf`, `python-docx`, plain text reader |
| **Auth** | Bearer JWT (PyJWT), bcrypt password hashing |

## ⚡ Quick Start

### 1. Prerequisites
- **Python 3.11+**
- **Node.js 18+** & **npm**
- **MongoDB** running on `localhost:27017`

### 2. Environment Setup
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 3. Initialize Database & Seed Reference Categories
```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Create MongoDB indexes and seed reference categories
# and keep the connection live via compass of local 127.0.0.1:27017

# For unix/linux 
PYTHONPATH=. 
py scripts_db/create_indexes.py
py scripts_db/seed_categories.py
py scripts_db/seed_demo_chats.py
py scripts_db/create_network_assets_indexes.py
py scripts_db/seed_network_assets_demo.py

# For windows 
$env:PYTHONPATH="."
py scripts_db/create_indexes.py
py scripts_db/seed_categories.py
py scripts_db/seed_demo_chats.py
py scripts_db/create_network_assets_indexes.py
py scripts_db/seed_network_assets_demo.py
pytest backend/tests/test_network_assets.py # Not necessary 
```

### 4. Build Frontend & Run Backend Application

```bash
# Build React Frontend
cd frontend
npm install --legacy-peer-deps
npm run build
cd ..

# Start FastAPI server
PYTHONPATH=. uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

# From next time to run frontend and server both 
npm start
```

Access the portal at `http://localhost:8000`.
If using college ethernet then at `http://{ your ip address }:8000`

Get you ip adress by running 
```bash
# On terminal
ipconfig
```

## 🔑 Admin Credentials

Default Admin Login:
- **Username**: `admin`
- **Password**: `admin123`

To generate a new bcrypt password hash, run:
```bash
PYTHONPATH=. python3 scripts/hash_password.py <your_new_password>
```

## 🧪 Running Tests & Chatbot Evaluation

### Unit & Integration API Tests
```bash
PYTHONPATH=. pytest backend/tests/test_unit.py backend/tests/test_api.py -v
```

### Chatbot Evaluation Set (~30 Prompts)
Runs guard classification and problem classification accuracy check across 30 test prompts (15 on-topic, 10 off-topic, 5 prompt injections):
```bash
PYTHONPATH=. python3 backend/tests/eval_chatbot.py
```


# Knowledge Base Ingestion & RAG Pipeline Architecture

This document details how student chats and uploaded documents (PDF, DOCX, TXT) flow through the RAG pipeline into ChromaDB, and how context is retrieved during student troubleshooting sessions.

---

## 1. Document & Chat Ingestion Pipeline

```
[Uploaded File / Promoted Chat]
        │
        ▼
[Text Extraction Parser]  ──►  PDF (pypdf), DOCX (python-docx), TXT / Chat turns
        │
        ▼
[PII Sanitizer]           ──►  Strips emails, phone numbers, and plain passwords
        │
        ▼
[Text Chunker]            ──►  Splits into ~800 char chunks with ~100 char overlap
        │
        ▼
[Vector Store Embedding]  ──►  Generates vectors and stores in ChromaDB collection 'network_kb'
        │
        ▼
[Database Status Update]  ──►  Updates documents.status to 'INDEXED' with chunk_count
```

---

## 2. RAG Retrieval during Student Chat Turns

1. **User Query Input**: Student sends a troubleshooting query via `POST /api/chat/{id}/message`.
2. **Guard Step**: `guard_and_classify` determines if the query is on-topic. If off-topic, returns fixed refusal.
3. **Similarity Search**: `retrieve_context` queries ChromaDB for the top 6 relevant text chunks.
4. **Similarity Threshold Filtering**: Chunks with similarity score below `0.3` are discarded.
5. **Prompt Injection**: Relevant chunks are injected into `chat_system.txt` under `CONTEXT:` block.
6. **LLM Generation**: LLM generates friendly, beginner-level troubleshooting steps grounded in retrieved context.
