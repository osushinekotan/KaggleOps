# Infrastructure Setup

This guide walks you through setting up GCP infrastructure with Terraform.

## Prerequisites

- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed
- GCP project created
- [Terraform](https://www.terraform.io/downloads) installed
- Git repository initialized with remote origin configured

## Setup Steps

### 1. Authenticate to Google Cloud

```bash
# Authenticate for local development
gcloud auth application-default login

# Authenticate gcloud CLI
gcloud auth login

# Authenticate to GitHub
gh auth login
```

### 2. Configure Environment Variables

```bash
# Copy and edit .env file
cp .env.example .env

# Edit .env and set:
# - PROJECT_ID: Your GCP project ID
# - REGION: GCP region (e.g., asia-northeast1)
# - BUCKET_NAME: GCS bucket name for data storage
# - KAGGLE_USERNAME: Your Kaggle username
# - KAGGLE_KEY: Your Kaggle API key
# - KAGGLE_COMPETITION_NAME: Competition name
```

### 3. Create GCS Bucket for Terraform State

```bash
PROJECT_ID=your-project-id
REGION=asia-northeast1
BUCKET_NAME=${PROJECT_ID}-terraform-state

# Create bucket
gsutil mb -p ${PROJECT_ID} -l ${REGION} gs://${BUCKET_NAME}

# Enable versioning
gsutil versioning set on gs://${BUCKET_NAME}
```

### 4. Initialize Terraform

```bash
cd terraform/environments/dev

# Generate terraform.tfvars from .env
# This script auto-detects GitHub repository from git remote origin
/workspace/scripts/init_tfvars.sh /workspace/.env

# Set access token and initialize
export GOOGLE_OAUTH_ACCESS_TOKEN=$(gcloud auth application-default print-access-token)
terraform init
```

### 5. Review and Apply Terraform Configuration

```bash
# Review planned changes
terraform plan

# Apply changes
terraform apply
```

**Created Resources:**

- Service accounts (Vertex AI, GitHub Actions)
- GCS bucket for data storage
- Artifact Registry for Docker images
- Workload Identity Pool and Provider for GitHub Actions

### 6. Export Terraform Outputs to .env

```bash
cd ../../..

cat >> .env << EOF

# Workload Identity Federation (from terraform output)
WIF_PROVIDER=$(cd terraform/environments/dev && terraform output -raw workload_identity_provider)
WIF_SERVICE_ACCOUNT=$(cd terraform/environments/dev && terraform output -json service_account_emails | jq -r '.github_actions')
EOF
```

## Next Steps

### For GitHub Actions Setup

1. Install [GitHub CLI](https://cli.github.com/) if not already installed
2. Run the automated secrets setup script:
   ```bash
   # From repository root
   gh auth login
   ./scripts/set_github_secrets.sh
   ```

This automatically sets all secrets from your `.env` file, including the Workload Identity Federation credentials.

See [02_github_actions.md](02_github_actions.md) for more details.

### For Local Development

Push Docker image to Artifact Registry:

```bash
# Ensure environment variables are set (from .env)
source .env

# Build and push image using Cloud Build
make push-image
```
