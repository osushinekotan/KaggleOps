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

cat "$TFVARS_TEMPLATE" | \
  sed "s/YOUR_PROJECT_ID/$PROJECT_ID/g" | \
  sed "s/YOUR_REGION/$REGION/g" | \
  sed "s/YOUR_BUCKET_NAME/$BUCKET_NAME/g" \
  > "$TFVARS_OUTPUT"

echo "✓ Generated $TFVARS_OUTPUT"
