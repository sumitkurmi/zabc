# AI-Assisted Network Complaint Portal (MNNIT Allahabad)

An AI-assisted web portal where students report network problems and troubleshoot issues using a Retrieval-Augmented Generation (RAG) assistant. Built with React, Vite, TypeScript, Tailwind CSS, FastAPI, MongoDB, and ChromaDB.

---

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

---

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
PYTHONPATH=. python3 scripts_db/create_indexes.py
PYTHONPATH=. python3 scripts_db/seed_categories.py
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
If using college ethernet then at `https://{ your ip address }:8000`

Get you ip adress by running 
```bash
# On terminal
ipconfig
```

---

## 🔑 Admin Credentials

Default Admin Login:
- **Username**: `admin`
- **Password**: `admin123`

To generate a new bcrypt password hash, run:
```bash
PYTHONPATH=. python3 scripts/hash_password.py <your_new_password>
```

---

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
