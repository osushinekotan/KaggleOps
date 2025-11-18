-include .env

GIT_COMMIT := $(shell git rev-parse --short HEAD)
CONTAINER_URI_BASE := $(REGION)-docker.pkg.dev/$(PROJECT_ID)/kaggle-competition-artifacts/$(KAGGLE_COMPETITION_NAME)
CONTAINER_URI_COMMIT := $(CONTAINER_URI_BASE):$(GIT_COMMIT)
CONTAINER_URI_LATEST := $(CONTAINER_URI_BASE):latest

export CONTAINER_URI_LATEST
export CONTAINER_URI_COMMIT

# ====================================================================
# Infrastructure Setup
# ====================================================================
.PHONY: auth
auth:
	@echo "Authenticating with Google Cloud and GitHub..."
	gcloud auth application-default login
	gcloud auth login
	gh auth login
	@echo "All authentication completed"

.PHONY: init-infra
init-infra:
ifndef PROJECT_ID
	$(error PROJECT_ID is not set. Please set it in .env or export it)
endif
ifndef REGION
	$(error REGION is not set. Please set it in .env or export it)
endif
	@echo "Initializing infrastructure..."
	@if [ ! -f .env ]; then \
		echo "Copying .env.example to .env..."; \
		cp .env.example .env; \
		echo ".env file created. Please edit it with your configuration and run this command again."; \
		exit 1; \
	fi
	@echo "Creating Terraform state bucket..."
	@BUCKET_NAME=$(PROJECT_ID)-terraform-state && \
	gsutil mb -p $(PROJECT_ID) -l $(REGION) gs://$$BUCKET_NAME || true && \
	gsutil versioning set on gs://$$BUCKET_NAME
	@echo "Initializing Terraform..."
	cd terraform/environments/dev && \
	../../../scripts/init_tfvars.sh ../../../.env && \
	export GOOGLE_OAUTH_ACCESS_TOKEN=$$(gcloud auth application-default print-access-token) && \
	terraform init
	@echo "Infrastructure initialization completed"

.PHONY: setup-infra
setup-infra:
	@echo "Setting up infrastructure with Terraform..."
	cd terraform/environments/dev && terraform apply
	@echo "Exporting Terraform outputs to .env..."
	@if ! grep -q "^WIF_PROVIDER=" .env 2>/dev/null; then \
		echo "" >> .env; \
		echo "# Workload Identity Federation (from terraform output)" >> .env; \
		echo "WIF_PROVIDER=$$(cd terraform/environments/dev && terraform output -raw workload_identity_provider)" >> .env; \
		echo "WIF_SERVICE_ACCOUNT=$$(cd terraform/environments/dev && terraform output -json service_account_emails | jq -r '.github_actions')" >> .env; \
		echo "Terraform outputs added to .env"; \
	else \
		echo "WIF_PROVIDER already exists in .env. Skipping output export..."; \
		echo "If you want to update, please remove the existing WIF entries first."; \
	fi
	@echo "Setting up GitHub secrets..."
	./scripts/set_github_secrets.sh
	@echo "Infrastructure setup completed"

.PHONY: tf-plan
tf-plan:
	@echo "Running Terraform plan..."
	cd terraform/environments/dev && terraform plan

.PHONY: tf-destroy
tf-destroy:
	@echo "Destroying infrastructure with Terraform..."
	cd terraform/environments/dev && terraform destroy

# ====================================================================
# Kaggle Competition Setup
# ====================================================================
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

push_deps ?= true

.PHONY: submit-local
submit-local:
ifndef BUCKET_NAME
	$(error BUCKET_NAME is not set)
endif
	@if [ "$(push_deps)" = "true" ]; then \
		echo "Pushing dependencies to Kaggle..."; \
		$(MAKE) push-deps; \
	else \
		echo "Skipping push-deps (push_deps=$(push_deps))"; \
	fi
	$(MAKE) push-arts-local
	$(MAKE) push-code-local
	@echo "Waiting for artifacts to process..."
	sleep 60
	$(MAKE) push-sub
	@echo "Submission completed"

script ?= src/train.py
push_image ?= true
machine_type ?= n1-standard-4

.PHONY: train-vertex
train-vertex:
ifndef PROJECT_ID
	$(error PROJECT_ID is not set)
endif
ifndef REGION
	$(error REGION is not set)
endif
ifndef BUCKET_NAME
	$(error BUCKET_NAME is not set)
endif
	@echo "CONTAINER_URI_COMMIT: $(CONTAINER_URI_COMMIT)"
	@if [ "$(push_image)" = "true" ]; then \
		echo "Pushing Docker image..."; \
		$(MAKE) push-image; \
	else \
		echo "Skipping push-image (push_image=$(push_image))"; \
	fi
	@echo "Running training script via Vertex AI Custom Job: $(script)"
	@echo "Machine type: $(machine_type)"
	@echo "CONTAINER_URI_COMMIT: $(CONTAINER_URI_COMMIT)"
	@export SCRIPT=$(script) MACHINE_TYPE=$(machine_type) CONTAINER_URI_COMMIT=$(CONTAINER_URI_COMMIT) && envsubst < configs/vertex/training-job.yaml > /tmp/vertex-training-job.yaml
	@cat /tmp/vertex-training-job.yaml
	@echo "Creating Vertex AI job..."
	@JOB_ID=$$(gcloud ai custom-jobs create \
		--project=$(PROJECT_ID) \
		--region=$(REGION) \
		--display-name="kaggle-training-$$(date +%Y%m%d-%H%M%S)" \
		--config=/tmp/vertex-training-job.yaml \
		--format="value(name)") && \
	echo "Created Vertex AI job: $$JOB_ID" && \
	echo "Waiting for job completion..." && \
	./scripts/wait_for_vertex_job.sh "$$JOB_ID" "$(PROJECT_ID)" "$(REGION)"
	@echo "Training completed"

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
	@export EXP_NAMES=$(EXP_NAMES) CONTAINER_URI_LATEST=$(CONTAINER_URI_LATEST) BUCKET_NAME=$(BUCKET_NAME) KAGGLE_USERNAME=$(KAGGLE_USERNAME) KAGGLE_KEY=$(KAGGLE_KEY) KAGGLE_COMPETITION_NAME=$(KAGGLE_COMPETITION_NAME) && envsubst < configs/vertex/push-artifacts-job.yaml > /tmp/vertex-push-artifacts-job.yaml
	@cat /tmp/vertex-push-artifacts-job.yaml
	@echo "Creating Vertex AI job..."
	@JOB_ID=$$(gcloud ai custom-jobs create \
		--project=$(PROJECT_ID) \
		--region=$(REGION) \
		--display-name="kaggle-push-artifacts-$$(date +%Y%m%d-%H%M%S)" \
		--config=/tmp/vertex-push-artifacts-job.yaml \
		--format="value(name)") && \
	echo "Created Vertex AI job: $$JOB_ID" && \
	echo "Waiting for job completion..." && \
	./scripts/wait_for_vertex_job.sh "$$JOB_ID" "$(PROJECT_ID)" "$(REGION)"
	@echo "Artifacts pushed successfully"

.PHONY: submit-vertex
submit-vertex:
ifndef BUCKET_NAME
	$(error BUCKET_NAME is not set)
endif
	@if [ "$(push_deps)" = "true" ]; then \
		echo "Pushing dependencies to Kaggle..."; \
		$(MAKE) push-deps; \
	else \
		echo "Skipping push-deps (push_deps=$(push_deps))"; \
	fi
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
