#!/bin/bash

# OpenDiscourse Environment Setup Script
# Installs pyenv, uv, and configures the development environment

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting OpenDiscourse Environment Setup...${NC}"

# 1. Check/Install pyenv
if ! command -v pyenv &> /dev/null; then
    echo -e "${BLUE}📦 Installing pyenv...${NC}"
    curl https://pyenv.run | bash

    # Add to shell config if not present
    if [ -n "$ZSH_VERSION" ]; then
        CONFIG_FILE="$HOME/.zshrc"
    else
        CONFIG_FILE="$HOME/.bashrc"
    fi

    echo -e "${BLUE}📝 Adding pyenv to $CONFIG_FILE...${NC}"
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> "$CONFIG_FILE"
    echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> "$CONFIG_FILE"
    echo 'eval "$(pyenv init -)"' >> "$CONFIG_FILE"

    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
else
    echo -e "${GREEN}✅ pyenv is already installed.${NC}"
fi

# 2. Check/Install uv
if ! command -v uv &> /dev/null; then
    echo -e "${BLUE}📦 Installing uv...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source "$HOME/.cargo/env" 2>/dev/null || true
else
    echo -e "${GREEN}✅ uv is already installed.${NC}"
fi

# 3. Install Python Version
PYTHON_VERSION="3.12.0"
if [ -f ".python-version" ]; then
    PYTHON_VERSION=$(cat .python-version)
fi

echo -e "${BLUE}🐍 Installing Python $PYTHON_VERSION...${NC}"
pyenv install -s "$PYTHON_VERSION"
pyenv local "$PYTHON_VERSION"

# 4. Create Virtual Environment
echo -e "${BLUE}🔨 Creating virtual environment...${NC}"
uv venv .venv

# 5. Install Dependencies
echo -e "${BLUE}📥 Installing dependencies...${NC}"
source .venv/bin/activate
if [ -f "requirements.txt" ]; then
    uv pip install -r requirements.txt
fi

# 6. Setup Auto-activation Hook
echo -e "${GREEN}✅ Setup complete!${NC}"
echo -e "${BLUE}ℹ️  To automatically activate the virtual environment when entering this directory, add the following to your shell config (.zshrc or .bashrc):${NC}"

cat << 'EOF'

# OpenDiscourse Auto-activation
opendiscourse_auto_activate() {
    if [[ "$PWD" == *"/opendiscourse"* ]]; then
        if [ -d "$PWD/.venv" ]; then
            if [[ "$VIRTUAL_ENV" != "$PWD/.venv" ]]; then
                source "$PWD/.venv/bin/activate"
            fi
        fi
    fi
}
chpwd_functions+=(opendiscourse_auto_activate)
EOF
