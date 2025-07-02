# Load .env in backend directory
include .env
export

# Run backend locally
run-server:
	uvicorn main:app --host 0.0.0.0 --port 8080 --reload

# GCP login
login:
	gcloud auth login

# Set the correct project
set-project:
	gcloud config set project $(PROJECT_ID)

# Enable required GCP services
enable-cloud-run-api:
	gcloud services enable run

# Build and deploy to Cloud Run from backend/
build:
	gcloud builds submit --tag $(BACKEND_IMAGE_URL) .

deploy:
	gcloud  \
	  run deploy $(BACKEND_SERVICE_NAME) \
	  --image $(BACKEND_IMAGE_URL) \
	  --region $(REGION) \
	  --platform managed \
	  --allow-unauthenticated \
	  --set-env-vars OPENAI_API_KEY=$(OPENAI_API_KEY),AUTH_USERNAME=$(AUTH_USERNAME),AUTH_PASSWORD=$(AUTH_PASSWORD)
