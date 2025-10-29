#!/bin/bash

GITHUB_REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)

while IFS='=' read -r key value; do

  [[ "$key" =~ ^#.*$ ]] && continue
  [[ -z "$key" ]] && continue

  value="${value%\"}"
  value="${value#\"}"

  # Trim whitespace
  value=$(echo -n "$value" | tr -d '[:space:]')

  echo -n "$value" | gh secret set "$key" --repo $GITHUB_REPO
  echo "✓ Set $key"
done < .env
