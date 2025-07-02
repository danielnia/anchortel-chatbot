include .env
export


#build:
#	gcloud builds submit . --tag gcr.io/$(PROJECT_ID)/$(SERVICE_NAME)

build:
	gcloud builds submit . --tag $(UI_IMAGE_URL)

#deploy:
#	gcloud run deploy $(SERVICE_NAME) \
#		--image gcr.io/$(PROJECT_ID)/$(SERVICE_NAME) \
#		--region $(REGION) \
#		--platform managed \
#		--allow-unauthenticated

deploy:
	gcloud run deploy $(UI_SERVICE_NAME) \
		--image $(UI_IMAGE_URL) \
		--region $(REGION)\
		--platform managed \
		--allow-unauthenticated

run-local:
	docker run -p 8080:80 \
		-e MODEL_API_URL=$(MODEL_API_URL) \
		$(UI_IMAGE_URL)

run-local-dev:
	npx http-server public -p 8000