import os
from dotenv import load_dotenv
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from agent_logic import handle_query
from fastapi.middleware.cors import CORSMiddleware
from initialize_db import init_db
import logging
import time
import secrets
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.responses import FileResponse

# Initialize logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

init_db()
app = FastAPI(docs_url="/docs", redoc_url="/redoc")


# Load environment variables
def init_env():
    dotenv_path = Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=dotenv_path)

    # Required environment variables
    required_vars = ["OPENAI_API_KEY", "AUTH_USERNAME", "AUTH_PASSWORD"]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

    logging.info("Env loaded. OpenAI key ends with: %s", os.getenv("OPENAI_API_KEY")[-7:])

init_env()
# test if the environment variable is set


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication setup
security = HTTPBasic()

def verify_user(credentials: HTTPBasicCredentials = Depends(security)):
    env_username = os.getenv("AUTH_USERNAME")
    env_password = os.getenv("AUTH_PASSWORD")

    if not env_username or not env_password:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication credentials not found in environment."
        )

    correct_username = secrets.compare_digest(credentials.username, env_username)
    correct_password = secrets.compare_digest(credentials.password, env_password)

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/test")
def health():
    return {"status": "ok"}

class ChatInput(BaseModel):
    message: str
    user_id: str

@app.post("/chat")
async def chat(request: ChatInput, username: str = Depends(verify_user)):
    logs: list[str] = []
    start_time = time.time()
    try:
        logs.append(f"🔵 Received message from {request.user_id}: {request.message}")
        response = await handle_query(request.user_id, request.message, logs)  # pass logs
        duration = time.time() - start_time
        logs.append(f"🟢 Responded in {duration:.2f}s: {response!r}")
        return {"response": response, "logs": logs}
    except Exception as e:
        logs.append(f"❌ Error: {e}")
        return {"response": "", "logs": logs}


# app.mount(
#     "/",
#     StaticFiles(directory="frontend/public", html=True),
#     name="frontend"
# )

# Optional fallback root route for sanity
@app.get("/")
def root():
    return {"status": "Backend is running."}