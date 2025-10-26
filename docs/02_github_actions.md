# GitHub Actions Setup

## Prerequisites

- Deploy GCP resources with Terraform first (see [01_infra.md](01_infra.md))
- Admin access to your GitHub repository
- [GitHub CLI](https://cli.github.com/) installed

## Setup Steps

### 1. Apply Terraform

See [01_infra.md](01_infra.md) for infrastructure setup.

```bash
cd terraform/environments/dev
terraform output
```

### 2. Configure GitHub Secrets

After adding Terraform outputs to your `.env` file (see [01_infra.md](01_infra.md)):

#### Option A: Automatic Setup (Recommended)

```bash
# Authenticate to GitHub CLI
gh auth login

# Set all secrets from .env
./scripts/set_github_secrets.sh
```

This sets all required secrets from `.env`:
- `PROJECT_ID`
- `REGION`
- `BUCKET_NAME`
- `KAGGLE_USERNAME`
- `KAGGLE_KEY`
- `KAGGLE_COMPETITION_NAME`
- `WIF_PROVIDER` (from Terraform output)
- `WIF_SERVICE_ACCOUNT` (from Terraform output)

#### Option B: Manual Setup

Go to `Settings` > `Secrets and variables` > `Actions` and manually add all secrets from your `.env` file.

## Workflows

### push-kaggle-deps.yml

**Triggers:** Manual, or PR with changes to `codes/deps/requirements.txt`

**What it does:** Pushes dependencies to Kaggle

### build-push-image.yml

**Triggers:** Manual, or push/PR with changes to `Dockerfile`, `src/**`, `pyproject.toml`, `cloudbuild.yaml`

**What it does:** Builds Docker image with Cloud Build and pushes to Artifact Registry

**Image tags:**

- `${SHORT_SHA}` - Git commit hash
- `latest`
