#!/bin/bash

if [ ! -f ./apps/api/.env ]; then
    echo "Copying .env.example to .env for the API..."
    cp ./apps/api/.env.example ./apps/api/.env
fi

# if [ ! -f ./apps/web/.env ]; then
#     echo "Copying .env.example to .env for the Web App..."
#     cp ./apps/web/.env.example ./apps/web/.env
# fi

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Homebrew is not installed. Please install Homebrew first."
    echo "Visit https://brew.sh for installation instructions."
    exit 1
fi

# Check if git-lfs is installed
if ! command -v git-lfs &> /dev/null; then
    echo "git-lfs is not installed. Installing..."
    brew install git-lfs
fi

# Check if pnpm is installed
if ! command -v pnpm &> /dev/null; then
    echo "pnpm is not installed. Installing..."
    curl -fsSL https://get.pnpm.io/install.sh | sh -
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Sync the dependencies and virtual environment
echo "Syncing dependencies and virtual environment..."
cd ./apps/api && uv sync && cd ../..

# Sync the database schema
echo "Syncing database schema..."
cd ./apps/api && uv run prisma db push && cd ../..

# Installing pnpm dependencies
echo "Installing pnpm dependencies..."
pnpm install

echo ""
echo "Done! You can now start the development server with 'pnpm turbo run dev'"
