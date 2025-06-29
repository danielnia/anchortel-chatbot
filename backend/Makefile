# Load .env in backend directory
include .env
export $(shell sed 's/=.*//' .env)

# Run backend locally
run-server:
	uvicorn main:app --host 0.0.0.0 --port 8080 --reload

# GCP login
login:
	gcloud auth login

# Set the correct project
set-project:
	gcloud config set project gcp-agent-chatbot

# Enable required GCP services
enable-cloud-run-api:
	gcloud services enable run

# Build and deploy to Cloud Run from backend/
deploy:
	gcloud builds submit --tag gcr.io/gcp-agent-chatbot/fastapi-backend . && \
	gcloud run deploy fastapi-backend \
	  --image gcr.io/gcp-agent-chatbot/fastapi-backend \
	  --region us-central1 \
	  --platform managed \
	  --allow-unauthenticated \
	  --set-env-vars OPENAI_API_KEY=$$OPENAI_API_KEY,AUTH_USERNAME=$$AUTH_USERNAME,AUTH_PASSWORD=$$AUTH_PASSWORD

evaluate:
	python evaluation_pipeline.py \
    --reference_file "D:\1- Courses\LLM\CusomerServiceChatBot\trash\Anchortel_info.txt" \
    --n_parts 4 \
    --m_questions 5 \
    --output evaluation_report.csv \
    --qa_model gpt-4o-mini \
    --agent_backend remote \
    --agent_url https://fastapi-backend-1020577311422.us-central1.run.app/chat \
	--auth_username anchortel_user \
	--auth_password S3cureP@ss2024!