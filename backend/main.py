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
from typing import Optional
from fastapi import File, UploadFile, Query
from fastapi.responses import StreamingResponse
import pandas as pd
import io
from chatbot_evaluator import generate_reference_questions, compute_ragas_metrics, append_scores_to_dataframe
import asyncio
import traceback
from fastapi.responses import JSONResponse
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings

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
    allow_origins=["http://192.168.99.1:8000", "https://anchortel-ui-1020577311422.us-central1.run.app",
                   "http://127.0.0.1:8000", "http://192.168.56.1:8000", "http://192.168.0.240:8000",
                   "http://localhost:8000"],  # specify your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


## Evaluation methods ##
async def get_chatbot_answer(question, user_id):

    username = os.getenv("AUTH_USERNAME")
    request = ChatInput(message=question, user_id=f"test_user_{user_id}", return_context=True)

    result = await chat_logic(request, username)
    data = result.get("response", {})
    answer = data.get("answer", "")
    source_docs = data.get("source_documents", [])
    print(f"Retrieved docs for user_id {user_id}: {source_docs}")  # <-- Add this line
    return answer, [getattr(doc, "page_content", "") for doc in source_docs]


async def process_ui_dataframe(df):
    async def process_row(row):
        try:
            return await get_chatbot_answer(row["user_input"], row.name)
        except KeyError:
            print("Available columns:", row.index)
            raise

    tasks = [process_row(row) for _, row in df.iterrows()]
    results = await asyncio.gather(*tasks)
    df["response"] = [r[0] for r in results]
    df["retrieved_contexts"] = [r[1] for r in results]
    return df

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
    return_context: Optional[bool] = False

async def chat_logic(request: ChatInput, username: str):
    logs = []
    start_time = time.time()
    try:
        logs.append(f"🔵 Received message from {request.user_id}: {request.message}")
        response = await handle_query(request.user_id, request.message, logs, return_docs=request.return_context)
        duration = time.time() - start_time
        logs.append(f"🟢 Responded in {duration:.2f}s: {response!r}")
        return {"response": response, "logs": logs}
    except Exception as e:
        logs.append(f"❌ Error: {e}")
        return {"response": "", "logs": logs}

@app.post("/chat")
async def chat(request: ChatInput, username: str = Depends(verify_user)):
    return await chat_logic(request, username)

# Optional fallback root route for sanity
@app.get("/")
def root():
    return {"status": "Backend is running."}




# Evaluation endpoint
@app.get("/generate-questions")
async def generate_questions(num_questions: int = Query(..., gt=0)):
    try:
        generator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-3.5-turbo"))
        generator_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())
        print(f"requested number of qs: {num_questions}")
        df = generate_reference_questions(num_questions, generator_llm, generator_embeddings)
        output = io.BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                 headers={"Content-Disposition": "attachment; filename=questions.xlsx"})
    except Exception as e:
        logging.error(f"Error in /generate-questions: {e}\n{traceback.format_exc()}")
        return JSONResponse(status_code=500, content={"detail": "Failed to generate questions."})

@app.post("/evaluate-excel")
async def evaluate_excel(file: UploadFile = File(...)):
    try:
        generator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-3.5-turbo"))
        generator_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        df = await process_ui_dataframe(df)  # <-- Add await here
        results = compute_ragas_metrics(df.to_dict("records"), generator_llm)
        print("RAGAS results:", results)
        df = append_scores_to_dataframe(df, results)
        print("DataFrame with scores:", df.head())
        output = io.BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                 headers={"Content-Disposition": "attachment; filename=evaluated.xlsx"})
    except Exception as e:
        logging.error(f"Error in /evaluate-excel: {e}\n{traceback.format_exc()}")
        return JSONResponse(status_code=500, content={"detail": "Failed to evaluate Excel file."})

