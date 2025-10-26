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

for var in PROJECT_ID REGION BUCKET_NAME; do
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

cat "$TFVARS_TEMPLATE" | \
  sed "s/YOUR_PROJECT_ID/$PROJECT_ID/g" | \
  sed "s/YOUR_REGION/$REGION/g" | \
  sed "s/YOUR_BUCKET_NAME/$BUCKET_NAME/g" | \
  sed "s#YOUR_GITHUB_USERNAME/YOUR_REPO_NAME#$GITHUB_REPO#g" \
  > "$TFVARS_OUTPUT"

echo "✓ Generated $TFVARS_OUTPUT"
