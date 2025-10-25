include .env
export


# ============================================================================
# Setup & Initialization
# ============================================================================

.PHONY: _write_submission_code
_write_submission_code:
	python -m src.kaggle_utils.write submission-code

.PHONY: _scrape_competition
_scrape_competition:
	./scripts/scrape_competition.sh

.PHONY: _write_sub_meta
_write_sub_meta:
	python -m src.kaggle_utils.write submission-metadata

.PHONY: _write_deps_meta
_write_deps_meta:
	python -m src.kaggle_utils.write deps-metadata

.PHONY: setup
setup: _write_submission_code _scrape_competition _write_sub_meta _write_deps_meta
	@echo "Setup completed"

.PHONY: dl-comp
dl-comp:
	python -m src.kaggle_utils.download competition-dataset

# ============================================================================
# Code Quality
# ============================================================================

.PHONY: fmt
fmt:
	pre-commit run --all-files

.PHONY: mypy
mypy:
	mypy .

# ============================================================================
# Training
# ============================================================================

.PHONY: train-local
train-local: gcs-pull
ifndef TRAIN_SCRIPT
	$(error TRAIN_SCRIPT is not set. Example: make train-local TRAIN_SCRIPT=src/train.py)
endif
	@echo "Running training script: $(TRAIN_SCRIPT)"
	python -m $(subst /,.,$(patsubst %.py,%,$(TRAIN_SCRIPT)))
	$(MAKE) gcs-push
	@echo "Training completed and results pushed to GCS"

.PHONY: train-vertex
train-vertex:
ifndef PROJECT_ID
	$(error PROJECT_ID is not set)
endif
ifndef BUCKET_NAME
	$(error BUCKET_NAME is not set)
endif
ifndef CONTAINER_URI
	$(error CONTAINER_URI is not set)
endif
ifndef TRAIN_SCRIPT
	$(error TRAIN_SCRIPT is not set. Example: make train-vertex TRAIN_SCRIPT=src/train.py)
endif
ifndef VERTEX_MACHINE_TYPE
	$(error VERTEX_MACHINE_TYPE is not set)
endif
	@echo "Submitting training job to Vertex AI: $(TRAIN_SCRIPT)"
	python -m src.kaggle_ops.cusom_job \
		--script-path $(TRAIN_SCRIPT) \
		--project-id $(PROJECT_ID) \
		--bucket-name $(BUCKET_NAME) \
		--container-uri $(CONTAINER_URI) \
		--display-name "training-$(notdir $(TRAIN_SCRIPT:.py=))" \
		--machine-type $(VERTEX_MACHINE_TYPE)

# ============================================================================
# Kaggle Operations (Local)
# ============================================================================

.PHONY: submit-local
submit-local:
ifndef EXP_NAME
	$(error EXP_NAME is not set)
endif
	python -m src.submit --exp-name $(EXP_NAME)

.PHONY: push-deps
push-deps:
	python -m src.kaggle_utils.write deps-code
	@if [ ! -f codes/deps/code.ipynb ]; then \
		echo "code.ipynb not found in codes/deps. Skipping push."; \
		exit 0; \
	fi
	cd codes/deps && kaggle k push && cd ../..

# ============================================================================
# GCS Synchronization
# ============================================================================

.PHONY: gcs-pull
gcs-pull:
ifndef BUCKET_NAME
	$(error BUCKET_NAME is not set)
endif
	@echo "Syncing from GCS to local (GCS is source of truth)..."
	gcloud storage rsync -r gs://$(BUCKET_NAME)/input ./data
	@echo "Pull from GCS completed"

.PHONY: gcs-push
gcs-push:
ifndef BUCKET_NAME
	$(error BUCKET_NAME is not set)
endif
	@echo "Syncing from local to GCS..."
	gcloud storage rsync -r ./data gs://$(BUCKET_NAME)
	@echo "Push to GCS completed"


# ============================================================================
# Vertex AI Operations
# ============================================================================

.PHONY: submit-vertex
submit-vertex:
ifndef PROJECT_ID
	$(error PROJECT_ID is not set)
endif
ifndef BUCKET_NAME
	$(error BUCKET_NAME is not set)
endif
ifndef CONTAINER_URI
	$(error CONTAINER_URI is not set)
endif
ifndef EXP_NAME
	$(error EXP_NAME is not set)
endif
	python -m src.kaggle_ops.cusom_job \
		--script-path src/submit.py \
		--project-id $(PROJECT_ID) \
		--bucket-name $(BUCKET_NAME) \
		--container-uri $(CONTAINER_URI) \
		--display-name "push-submission" \
		--machine-type "n1-standard-4" \
		--args --exp-name $(EXP_NAME)

# ============================================================================
# Docker Image
# ============================================================================

.PHONY: build-push-image
build-push-image:
ifndef GCP_PROJECT_ID
	$(error GCP_PROJECT_ID is not set)
endif
ifndef GAR_REGION
	$(error GAR_REGION is not set)
endif
ifndef GAR_REPOSITORY
	$(error GAR_REPOSITORY is not set)
endif
	./scripts/build_and_push_image.sh
