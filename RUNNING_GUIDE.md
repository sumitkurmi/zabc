# Complete How-To Run Guide: MNNIT Network Portal

This guide provides step-by-step instructions for running the MNNIT Network Portal locally or deploying it with your custom MongoDB URL and AI LLM API Keys.

---

## 📋 Prerequisites

Before starting, ensure you have the following installed on your machine:
- **Python 3.11+**
- **Node.js 18+** & **npm**
- **MongoDB** (or a MongoDB Atlas URI string)

---

## ⚙️ Step 1: Environment Variable Configuration (`.env`)

Copy `.env.example` to create your active `.env` file in the project root:

```bash
cp .env.example .env
```

Open `.env` and edit the following fields according to your setup:

### 1. Database Connection (MongoDB)
- For local MongoDB:
  ```env
  MONGODB_URI=mongodb://localhost:27017
  MONGODB_DB_NAME=network_portal
  ```
- For MongoDB Atlas (Cloud Database):
  ```env
  MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=maxPoolSize=10
  MONGODB_DB_NAME=network_portal
  ```

### 2. AI Model & LLM Provider API Key
- To use **Anthropic Claude API**:
  ```env
  LLM_PROVIDER=anthropic
  LLM_API_KEY=sk-ant-api03-...  # Paste your Anthropic API Key here
  LLM_MODEL_CHAT=claude-3-5-sonnet-20241022
  LLM_MODEL_GUARD=claude-3-5-haiku-20241022
  ```
- To run without an API Key (Offline / Mock Mode):
  ```env
  LLM_PROVIDER=mock
  LLM_API_KEY=
  ```

### 3. Admin Credentials
- Default admin credentials:
  ```env
  ADMIN_USERNAME=admin
  ADMIN_PASSWORD_HASH=$2b$12$z11TCwrLVRnlzFvMTKV2suLuuSeDTrATQJN2.b0ZARDdcuzbnyyhm
  JWT_SECRET=mnnit-network-portal-jwt-secret-key-32bytes-min
  ```
- To create a custom password hash:
  ```bash
  PYTHONPATH=. python3 scripts/hash_password.py <your_password>
  ```
  Copy the printed `Bcrypt Hash` into `ADMIN_PASSWORD_HASH` in `.env`.

---

## 📦 Step 2: Install Backend Dependencies & Seed Database

1. **Install Python Packages**:
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **Initialize Database Indexes & Reference Categories**:
   ```bash
   PYTHONPATH=. python3 scripts_db/create_indexes.py
   PYTHONPATH=. python3 scripts_db/seed_categories.py
   ```

---

## 💻 Step 3: Install Frontend Dependencies & Build

1. **Navigate to the frontend folder**:
   ```bash
   cd frontend
   ```

2. **Install Node dependencies**:
   ```bash
   npm install --legacy-peer-deps
   ```

3. **Build Frontend Bundle (for production backend serving)**:
   ```bash
   npm run build
   cd ..
   ```

*(Alternatively, for frontend dev mode with hot reloading: run `npm run dev` inside `frontend/` while backend runs on port 8000).*

---

## 🚀 Step 4: Run the Application

Start the FastAPI application server from the root directory:

```bash
PYTHONPATH=. uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

Open your browser and navigate to:
- **Student Complaint Form & Assistant**: `http://localhost:8000/`
- **Admin Login Portal**: `http://localhost:8000/admin/login`
- **Auto-generated API Docs (Swagger UI)**: `http://localhost:8000/docs`

---

## 🐳 Docker Alternative (One-Command Run)

If you prefer running via Docker Compose:

```bash
docker compose up --build
```
This automatically spins up MongoDB and the combined FastAPI/React service on port `8000`.
