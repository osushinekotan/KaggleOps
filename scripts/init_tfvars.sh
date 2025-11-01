#!/bin/bash

set -euo pipefail

ENV_FILE="${1:-.env}"
TFVARS_TEMPLATE="terraform.tfvars.example"
TFVARS_OUTPUT="terraform.tfvars"

if [ -f "$ENV_FILE" ]; then
  echo "Loading $ENV_FILE"
  set -a
  source "$ENV_FILE"
  set +a
fi

for var in PROJECT_ID REGION BUCKET_NAME KAGGLE_COMPETITION_NAME; do
  if [ -z "${!var:-}" ]; then
    echo "Error: $var is not set in $ENV_FILE or environment"
    exit 1
  fi
done

# Auto-detect GitHub repository from git remote
GITHUB_REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)

if [ -z "$GITHUB_REPO" ]; then
  echo "Error: Could not detect GitHub repository from git remote origin"
  echo "Please set up git remote origin first:"
  echo "  git remote add origin git@github.com:username/repo-name.git"
  exit 1
fi

echo "Detected GitHub repository: $GITHUB_REPO"

# Check if envsubst is available
if ! command -v envsubst >/dev/null 2>&1; then
  echo "Error: envsubst command not found. Please install gettext package:"
  echo "  apt-get install gettext-base  # Debian/Ubuntu"
  echo "  yum install gettext           # CentOS/RHEL"
  exit 1
fi

# Export variables for envsubst
export PROJECT_ID REGION BUCKET_NAME KAGGLE_COMPETITION_NAME GITHUB_REPO

# Use envsubst to replace environment variables in template
envsubst < "$TFVARS_TEMPLATE" > "$TFVARS_OUTPUT"

echo "✓ Generated $TFVARS_OUTPUT"
