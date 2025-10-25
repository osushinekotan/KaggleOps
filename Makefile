include .env
export

.PHONY: setup
setup:
	python -m src.kaggle_utils.write submission-code
	./scripts/scrape_competition.sh
	python -m src.kaggle_utils.write submission-metadata
	python -m src.kaggle_utils.write deps-metadata
	@echo "Setup completed"

.PHONY: dl-comp
dl-comp:
	python -m src.kaggle_utils.download competition-dataset

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

.PHONY: pull
pull:
ifndef BUCKET_NAME
	$(error BUCKET_NAME is not set)
endif
	@echo "Syncing from GCS to local (GCS is source of truth)..."
	gcloud storage rsync -r gs://$(BUCKET_NAME) ./data
	@echo "Pull from GCS completed"

.PHONY: push
push:
ifndef BUCKET_NAME
	$(error BUCKET_NAME is not set)
endif
	@echo "Syncing from local to GCS..."
	gcloud storage rsync -r ./data gs://$(BUCKET_NAME)
	@echo "Push to GCS completed"

