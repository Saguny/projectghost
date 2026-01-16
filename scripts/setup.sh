#!/bin/bash
set -e

echo "=================================="
echo "Project Ghost Setup"
echo "=================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "\n${YELLOW}Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo -e "${RED}Error: Python 3.10+ required (found $python_version)${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $python_version${NC}"

# Create virtual environment
echo -e "\n${YELLOW}Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate || . venv/Scripts/activate

# Upgrade pip
echo -e "\n${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip --quiet
echo -e "${GREEN}✓ pip upgraded${NC}"

# Install dependencies
echo -e "\n${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt --quiet
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create directories
echo -e "\n${YELLOW}Creating data directories...${NC}"
mkdir -p data/logs
mkdir -p data/vector_db
mkdir -p data/memory_snapshots
echo -e "${GREEN}✓ Directories created${NC}"

# Setup environment file
if [ ! -f ".env" ]; then
    echo -e "\n${YELLOW}Creating .env file...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env created${NC}"
    echo -e "${YELLOW}⚠  Please edit .env with your Discord token!${NC}"
else
    echo -e "${GREEN}✓ .env exists${NC}"
fi

# Check Ollama
echo -e "\n${YELLOW}Checking Ollama...${NC}"
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama installed${NC}"
    
    # Check if Ollama is running
    if curl -s http://localhost:11434/api/tags &> /dev/null; then
        echo -e "${GREEN}✓ Ollama is running${NC}"
    else
        echo -e "${YELLOW}⚠  Ollama not running. Start with: ollama serve${NC}"
    fi
else
    echo -e "${YELLOW}⚠  Ollama not found${NC}"
    echo -e "   Install from: https://ollama.ai/"
fi

# Summary
echo -e "\n${GREEN}=================================="
echo "Setup Complete!"
echo "==================================${NC}"
echo ""
echo "Next steps:"
echo "1. Edit .env with your Discord token"
echo "2. Pull an Ollama model: ollama pull mistral-nemo"
echo "3. Run the bot: python main.py"
echo ""
echo "For help, see README.md"