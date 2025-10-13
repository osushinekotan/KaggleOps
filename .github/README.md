# KaggleOps

## Submission Flow

1. write `.env` file

   ```bash
   cp .env.example .env
   ```

   - `KAGGLE_USERNAME` : Your Kaggle username. (required)
   - `KAGGLE_KEY` : Your Kaggle API key. (required)
   - `KAGGLE_COMPETITION_NAME` : The name of the Kaggle competition. The name can be found in the `DOWNLOAD DATA` tab. (required)

2. install uv: https://docs.astral.sh/uv/getting-started/installation/

3. setup

   ```bash
   uv sync
   . .venv/bin/activate
   ```

   ```bash
   poe setup
   ```

4. download data

   ```bash
   poe dl-comp
   ```

5. upload deps

   ```bash
   poe push-deps
   ```

   - above commands (1~4) need to be run only once.
   - commands 5 to be run every time you want to update the dependencies.

6. experiment & create `inference.py`

   - edit `model_sources` (`codes/submission/kernel_metadata.json`)
   - uploade artifacts to Kaggle

   ```bash
   poe up-art {EXPERIMENT_NAME}
   ```

7. submit to Kaggle

   - update submission metadata (`codes/submission/kernel_metadata.json`)
     - `model_sources` should be updated.
     - If you want to enable GPU or TPU, you can set `enable_gpu` or `enable_tpu` to `true`.

   ```bash
   poe push-sub
   ```

## Options: Auto Submission via GitHub Actions

1. set GitHub secrets

   - `KAGGLE_USERNAME` : Your Kaggle username. (required)
   - `KAGGLE_KEY` : Your Kaggle API key. (required)
   - `KAGGLE_COMPETITION_NAME` : The name of the Kaggle competition. The name can be found in the `DOWNLOAD DATA` tab. (required)

2. push artifacts to Kaggle

   ```bash
   poe up-art {EXPERIMENT_NAME}
   ```

3. update submission metadata

   - `model_sources` : The source code of the model. (required)

4. create a pull request
