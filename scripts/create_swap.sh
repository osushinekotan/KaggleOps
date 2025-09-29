#!/bin/bash
set -e

# Check root
if [[ $EUID -ne 0 ]]; then
   echo "Run as root: sudo $0 [size_in_gb]"
   exit 1
fi

# Get size (default 4GB)
SWAP_SIZE="${1:-4}"
if ! [[ "$SWAP_SIZE" =~ ^[0-9]+$ ]]; then
    echo "Invalid size. Use integer (e.g., 4)"
    exit 1
fi

# Check existing swap
if swapon --show | grep -q .; then
    echo "Swap already exists"
    swapon --show
    exit 1
fi

# Create swap
echo "Creating ${SWAP_SIZE}GB swap..."
fallocate -l ${SWAP_SIZE}G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

# Persist
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Optimize
echo 'vm.swappiness=10' >> /etc/sysctl.conf
sysctl -p > /dev/null 2>&1

# Show result
echo "Done:"
free -h
