include .env
export

.PHONY: setup
setup:
	python -m src.kaggle_ops.write submission-code
	./scripts/scrape_competition.sh
	python -m src.kaggle_ops.write submission-metadata
	python -m src.kaggle_ops.write deps-metadata
	python -m src.kaggle_ops.write deps-code
	@echo "Setup completed"

.PHONY: dl-comp
dl-comp:
	python -m src.kaggle_ops.download competition-dataset

.PHONY: fmt
fmt:
	pre-commit run --all-files

.PHONY: mypy
mypy:
	mypy .

.PHONY: train-local
train-local: pull
ifndef script
	$(error script is not set. Example: make train-local script=src/train.py)
endif
	@echo "Running training script: $(script)"
	python $(script)
	$(MAKE) push
	@echo "Training completed and results pushed to GCS"

.PHONY: submit-local
submit-local:
ifndef BUCKET_NAME
	$(error BUCKET_NAME is not set)
endif
	$(MAKE) pull-data
	python -m src.submit
	$(MAKE) push-data
	@echo "Submission completed"

.PHONY: submit-vertex
submit-vertex:
ifndef BUCKET_NAME
	$(error BUCKET_NAME is not set)
endif
ifndef PROJECT_ID
	$(error PROJECT_ID is not set)
endif
ifndef REGION
	$(error REGION is not set)
endif
ifndef CONTAINER_URI
	$(error CONTAINER_URI is not set)
endif
	@echo "Submitting via Vertex AI Custom Job..."
	gcloud ai custom-jobs create \
		--project=$(PROJECT_ID) \
		--region=$(REGION) \
		--display-name="kaggle-submission-$(shell date +%Y%m%d-%H%M%S)" \
		--worker-pool-spec=machine-type=n1-standard-4,replica-count=1,container-image-uri=$(CONTAINER_URI) \
		--args="python,-m,src.submit" \
		--env-vars="BUCKET_NAME=$(BUCKET_NAME),KAGGLE_USERNAME=$(KAGGLE_USERNAME),KAGGLE_KEY=$(KAGGLE_KEY),KAGGLE_COMPETITION_NAME=$(KAGGLE_COMPETITION_NAME)"

.PHONY: push-deps
push-deps:
	python -m src.kaggle_ops.write deps-code
	cd codes/deps && kaggle k push && cd ../..

.PHONY: pull-data
pull-data:
ifndef BUCKET_NAME
	$(error BUCKET_NAME is not set)
endif
	@echo "Syncing from GCS to local (GCS is source of truth)..."
	gcloud storage rsync -r gs://$(BUCKET_NAME) ./data
	@echo "Pull from GCS completed"

.PHONY: push-data
push-data:
ifndef BUCKET_NAME
	$(error BUCKET_NAME is not set)
endif
	@echo "Syncing from local to GCS..."
	gcloud storage rsync -r ./data gs://$(BUCKET_NAME)
	@echo "Push to GCS completed"

.PHONY: push-image
push-image:
ifndef PROJECT_ID
	$(error PROJECT_ID is not set)
endif
ifndef REGION
	$(error REGION is not set)
endif
ifndef KAGGLE_COMPETITION_NAME
	$(error KAGGLE_COMPETITION_NAME is not set)
endif
	$(eval GIT_COMMIT := $(shell git rev-parse --short HEAD))
	@echo "Building Docker image with tag: $(GIT_COMMIT)..."
	docker build -t $(REGION)-docker.pkg.dev/$(PROJECT_ID)/kaggle-competition-artifacts/$(KAGGLE_COMPETITION_NAME):$(GIT_COMMIT) .
	docker tag $(REGION)-docker.pkg.dev/$(PROJECT_ID)/kaggle-competition-artifacts/$(KAGGLE_COMPETITION_NAME):$(GIT_COMMIT) $(REGION)-docker.pkg.dev/$(PROJECT_ID)/kaggle-competition-artifacts/$(KAGGLE_COMPETITION_NAME):latest
	@echo "Docker build completed"
	@echo "Configuring Docker authentication for Artifact Registry..."
	gcloud auth configure-docker $(REGION)-docker.pkg.dev
	@echo "Pushing Docker image to Artifact Registry..."
	docker push $(REGION)-docker.pkg.dev/$(PROJECT_ID)/kaggle-competition-artifacts/$(KAGGLE_COMPETITION_NAME):$(GIT_COMMIT)
	docker push $(REGION)-docker.pkg.dev/$(PROJECT_ID)/kaggle-competition-artifacts/$(KAGGLE_COMPETITION_NAME):latest
	@echo "Docker push completed for tags: $(GIT_COMMIT) and latest"
