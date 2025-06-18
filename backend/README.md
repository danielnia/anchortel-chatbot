    # 🧠 AnchorTel – GenAI-Powered Telecom Chatbot

A full-stack, AI-powered chatbot that simulates a telecom customer support assistant using **FastAPI**, **LangChain**, **OpenAI**, and **Docker**. It includes a secured web UI and a backend with retrieval-augmented generation (RAG). Both frontend and backend are independently containerized and deployed on **Google Cloud Run**.

---

## 📦 Project Structure

```
anchortel/
├── backend/
│   ├── main.py
│   ├── tools.py
│   ├── agent_logic.py
│   ├── rag_store.py
│   ├── initialize_db.py
│   ├── Dockerfile
│   ├── Makefile
│   └── .env              # (not committed)
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── Dockerfile
│   ├── Makefile
│   └── .gcloudignore
```

---

## 🌐 Live Demo

| Component | URL | Access |
|----------|-----|--------|
| 🧠 Backend API | Deployed on Google Cloud Run | Authenticated via UI |
| 💬 Frontend UI | [anchortel-ui](https://anchortel-ui-xxxxxx-uc.a.run.app) | 🔐 `demo` / `anchortel123` |

> Replace with your actual deployment URL. Auth is basic and meant for demo purposes only.

---

## 🔧 Technologies Used

- **FastAPI**, **LangChain**, **OpenAI**, **FAISS**
- **HTML/CSS/JavaScript** for frontend
- **Docker**, **Google Cloud Run**
- **Makefiles**, **http-server**, **dotenv**

---

## 🚀 Backend Setup (FastAPI + LangChain)

### 🔹 Local Setup

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Create `.env`:

```
OPENAI_API_KEY=your_key_here
```

Run the app:

```bash
uvicorn main:app --host 0.0.0.0 --port 8080
```

### 🔹 Cloud Run Deployment

```bash
make build
make deploy
```

> Requires `gcloud` CLI and authenticated project (`gcloud auth login`)

---

## 🧑‍💻 Frontend Setup (Static UI)

### 🔹 Local Testing

```bash
cd frontend/public
npx http-server . -p 8080
```

### 🔹 Dockerized Cloud Deployment

```bash
cd frontend
make build
make deploy
```

> Dockerfile uses `http-server` and binds to port `8080` (required by Cloud Run).

---

## 📬 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat`  | POST   | Main chatbot interface |
| `/test`  | GET    | Health check for backend |

Make sure your frontend JS points to the deployed backend endpoint (e.g., `https://fastapi-backend-xxxxxx.a.run.app/chat`).

---

## 🔐 Security Notes

- API keys and secrets are managed via `.env` and `dotenv`
- Frontend includes basic authentication for demo protection
- Backend should implement CORS and rate limiting in production

---

## ✅ What I Learned

- Deploying GenAI projects to Google Cloud with Docker
- Structuring LangChain agents with tools and vector search
- Using Makefiles for reproducible deployment flows
- Handling environment config securely and port binding in Cloud Run
- Serving production-grade static UIs via containers

---

## 📎 License

MIT License (or your preferred license)
    
