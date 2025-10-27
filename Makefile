-include .env

GIT_COMMIT := $(shell git rev-parse --short HEAD)
CONTAINER_URI_BASE := $(REGION)-docker.pkg.dev/$(PROJECT_ID)/kaggle-competition-artifacts/$(KAGGLE_COMPETITION_NAME)
CONTAINER_URI_COMMIT := $(CONTAINER_URI_BASE):$(GIT_COMMIT)
CONTAINER_URI_LATEST := $(CONTAINER_URI_BASE):latest

export CONTAINER_URI_LATEST

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
train-local: pull-data
	@echo "Running training script: $(script)"
	python $(script)
	$(MAKE) push-data
	@echo "Training completed and results pushed to GCS"
script ?= src/train.py

.PHONY: push-arts-local
push-arts-local:
ifndef BUCKET_NAME
	$(error BUCKET_NAME is not set)
endif
	$(MAKE) pull-data
	python -m src.kaggle_ops.push --run-env local
	@echo "Artifacts pushed successfully"

.PHONY: push-code-local
push-code-local:
	python -m src.kaggle_ops.upload codes --settings.run-env local
	@echo "Code pushed successfully"

.PHONY: push-sub
push-sub:
	@echo "Pushing submission to Kaggle..."
	cd codes/submission && kaggle k push
	@echo "Submission pushed successfully"

.PHONY: submit-local
submit-local:
ifndef BUCKET_NAME
	$(error BUCKET_NAME is not set)
endif
	$(MAKE) push-arts-local
	$(MAKE) push-code-local
	@echo "Waiting for artifacts to process..."
	sleep 60
	$(MAKE) push-sub
	@echo "Submission completed"

.PHONY: train-vertex
train-vertex: push-image
ifndef script
	$(error script is not set. Example: make train-vertex script=src/train.py)
endif
ifndef PROJECT_ID
	$(error PROJECT_ID is not set)
endif
ifndef REGION
	$(error REGION is not set)
endif
ifndef BUCKET_NAME
	$(error BUCKET_NAME is not set)
endif
	$(eval MACHINE_TYPE ?= n1-standard-4)
	@echo "Running training script via Vertex AI Custom Job: $(script)"
	@echo "Machine type: $(MACHINE_TYPE)"
	@export SCRIPT=$(script) && envsubst < configs/vertex/training-job.yaml > /tmp/vertex-training-job.yaml
	gcloud ai custom-jobs create \
		--project=$(PROJECT_ID) \
		--region=$(REGION) \
		--display-name="kaggle-training-$(shell date +%Y%m%d-%H%M%S)" \
		--config=/tmp/vertex-training-job.yaml

.PHONY: push-arts-vertex
push-arts-vertex:
ifndef BUCKET_NAME
	$(error BUCKET_NAME is not set)
endif
ifndef PROJECT_ID
	$(error PROJECT_ID is not set)
endif
ifndef REGION
	$(error REGION is not set)
endif
	@echo "Parsing experiment names from kernel-metadata.json..."
	$(eval EXP_NAMES := $(shell python -m src.kaggle_ops.parse_exp_names))
	@echo "Experiment names: $(EXP_NAMES)"
	@echo "Pushing artifacts via Vertex AI Custom Job..."
	@export EXP_NAMES=$(EXP_NAMES) && envsubst < configs/vertex/push-artifacts-job.yaml > /tmp/vertex-push-artifacts-job.yaml
	$(eval JOB_ID := $(shell gcloud ai custom-jobs create \
		--project=$(PROJECT_ID) \
		--region=$(REGION) \
		--display-name="kaggle-push-artifacts-$(shell date +%Y%m%d-%H%M%S)" \
		--config=/tmp/vertex-push-artifacts-job.yaml \
		--format="value(name)"))
	@echo "Created Vertex AI job: $(JOB_ID)"
	@echo "Waiting for job completion..."
	./scripts/wait-for-vertex-job.sh "$(JOB_ID)" "$(PROJECT_ID)" "$(REGION)"
	@echo "Artifacts pushed successfully"

.PHONY: submit-vertex
submit-vertex:
ifndef BUCKET_NAME
	$(error BUCKET_NAME is not set)
endif
	$(MAKE) push-arts-vertex
	$(MAKE) push-code-local
	@echo "Waiting for artifacts to process..."
	sleep 60
	$(MAKE) push-sub
	@echo "Submission via Vertex AI completed"

.PHONY: push-deps
push-deps:
	python -m src.kaggle_ops.write deps-code
	cd codes/deps && kaggle k push && cd ../..

.PHONY: pull-data
pull-data:
ifndef BUCKET_NAME
	$(error BUCKET_NAME is not set)
endif
	@echo "Syncing from GCS to local (no clobber sync)..."
	gcloud storage rsync -r --no-clobber gs://$(BUCKET_NAME) ./data
	@echo "Pull from GCS completed"

.PHONY: push-data
push-data:
ifndef BUCKET_NAME
	$(error BUCKET_NAME is not set)
endif
	@echo "Syncing from local to GCS... (no clobber sync)"
	gcloud storage rsync -r --no-clobber ./data gs://$(BUCKET_NAME)
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
	@echo "Submitting build to Cloud Build..."
	gcloud builds submit \
		--config=cloudbuild.yaml \
		--timeout=1h \
		--substitutions=_REGION=$(REGION),_KAGGLE_COMPETITION_NAME=$(KAGGLE_COMPETITION_NAME),SHORT_SHA=$(GIT_COMMIT) \
		--project=$(PROJECT_ID)
	@echo "Cloud Build completed"
