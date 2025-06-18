PROJECT_ID = gcp-agent-chatbot
SERVICE_NAME = anchortel-ui
REGION = us-central1

#build:
#	gcloud builds submit . --tag gcr.io/$(PROJECT_ID)/$(SERVICE_NAME)

build:
	gcloud builds submit . --tag gcr.io/gcp-agent-chatbot/anchortel-ui

#deploy:
#	gcloud run deploy $(SERVICE_NAME) \
#		--image gcr.io/$(PROJECT_ID)/$(SERVICE_NAME) \
#		--region $(REGION) \
#		--platform managed \
#		--allow-unauthenticated

deploy:
	gcloud run deploy anchortel-ui \
		--image gcr.io/gcp-agent-chatbot/anchortel-ui \
		--region us-central1 \
		--platform managed \
		--allow-unauthenticated
