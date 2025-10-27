#!/bin/bash
set -e

echo "Running post-create setup..."

# Install Python dependencies
echo "Installing Python dependencies..."
uv pip install -r pyproject.toml --system

# Install envsubst (from gettext-base package) and bash-completion
echo "Installing envsubst and bash-completion..."
apt-get update
apt-get install -y gettext-base bash-completion

# Setup git bash completion
echo "Setting up git bash completion..."
echo 'source /usr/share/bash-completion/completions/git' >> ~/.bashrc

echo "Post-create setup completed!"
