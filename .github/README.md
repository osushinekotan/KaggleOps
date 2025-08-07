# KaggleOps

## Initialize Project

1. write `.env` file

   ```bash
   cp .env.example .env
   ```

   - `KAGGLE_USERNAME` : Your Kaggle username. (required)
   - `KAGGLE_KEY` : Your Kaggle API key. (required)
   - `KAGGLE_COMPETITION_NAME` : The name of the Kaggle competition. The name can be found in the `DOWNLOAD DATA` tab. (required)

2. setup

   ```bash
   mise install
   mise trust
   mise run setup
   ```

## Options: Auto Submission via GitHub Actions

1. set GitHub secrets

   - `KAGGLE_USERNAME` : Your Kaggle username. (required)
   - `KAGGLE_KEY` : Your Kaggle API key. (required)
   - `KAGGLE_COMPETITION_NAME` : The name of the Kaggle competition. The name can be found in the `DOWNLOAD DATA` tab. (required)

2. push artifacts to Kaggle

   ```bash
   mise run up-art --settings.exp-name {EXPERIMENT_NAME}
   ```

3. update submission metadata

   - `model_sources` : The source code of the model. (required)

4. create a pull request
