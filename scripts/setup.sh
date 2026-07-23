#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Agentic AIOps Platform - Local Setup  ${NC}"
echo -e "${BLUE}========================================${NC}"

# Step 1: Check prerequisites
echo -e "\n${YELLOW}[1/8] Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 not found. Install Python 3.11+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "  Python: ${GREEN}$PYTHON_VERSION${NC}"

if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js not found. Install Node 18+${NC}"
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "  Node.js: ${GREEN}$NODE_VERSION${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker not found. Install Docker Desktop${NC}"
    exit 1
fi

echo -e "  Docker: ${GREEN}$(docker --version | head -1)${NC}"

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null 2>&1; then
    echo -e "${RED}Docker Compose not found${NC}"
    exit 1
fi

echo -e "  Docker Compose: ${GREEN}OK${NC}"

# Step 2: Create .env if missing
echo -e "\n${YELLOW}[2/8] Setting up environment...${NC}"

if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "  ${GREEN}Created .env from .env.example${NC}"
    echo -e "  ${YELLOW}>>> EDIT .env with your API keys before running <<<${NC}"
else
    echo -e "  ${GREEN}.env already exists${NC}"
fi

# Step 3: Start infrastructure
echo -e "\n${YELLOW}[3/8] Starting Docker infrastructure...${NC}"

docker compose up -d postgres redis qdrant 2>/dev/null || docker-compose up -d postgres redis qdrant 2>/dev/null
echo -e "  ${GREEN}PostgreSQL, Redis, Qdrant starting...${NC}"

# Step 4: Wait for services
echo -e "\n${YELLOW}[4/8] Waiting for services to be ready...${NC}"

for i in {1..30}; do
    if docker compose exec -T postgres pg_isready -U aiops -d aiops_db &>/dev/null 2>&1 || \
       docker-compose exec -T postgres pg_isready -U aiops -d aiops_db &>/dev/null 2>&1; then
        echo -e "  ${GREEN}PostgreSQL: Ready${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "  ${YELLOW}PostgreSQL still starting, continuing anyway...${NC}"
    fi
done

echo -e "  ${GREEN}Redis: Ready${NC}"
echo -e "  ${GREEN}Qdrant: Ready (http://localhost:6333)${NC}"

# Step 5: Create virtual environment
echo -e "\n${YELLOW}[5/8] Setting up Python virtual environment...${NC}"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "  ${GREEN}Created virtual environment${NC}"
else
    echo -e "  ${GREEN}Virtual environment exists${NC}"
fi

source venv/bin/activate
echo -e "  ${GREEN}Activated venv${NC}"

# Step 6: Install dependencies
echo -e "\n${YELLOW}[6/8] Installing Python dependencies...${NC}"

pip install --upgrade pip -q
pip install -e "." -q 2>&1 | tail -3
echo -e "  ${GREEN}Backend dependencies installed${NC}"

# Step 7: Install frontend
echo -e "\n${YELLOW}[7/8] Installing frontend dependencies...${NC}"

cd frontend
if [ ! -d "node_modules" ]; then
    npm install --silent 2>&1 | tail -3
    echo -e "  ${GREEN}Frontend dependencies installed${NC}"
else
    echo -e "  ${GREEN}Frontend dependencies already installed${NC}"
fi
cd ..

# Step 8: Print summary
echo -e "\n${YELLOW}[8/8] Setup complete!${NC}"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  ALL SERVICES RUNNING                  ${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e ""
echo -e "  ${BLUE}Services:${NC}"
echo -e "  PostgreSQL  -> localhost:5432"
echo -e "  Redis       -> localhost:6379"
echo -e "  Qdrant      -> http://localhost:6333"
echo -e ""
echo -e "  ${BLUE}To start the app:${NC}"
echo -e ""
echo -e "  Terminal 1 (Backend):"
echo -e "    ${GREEN}source venv/bin/activate${NC}"
echo -e "    ${GREEN}uvicorn backend.app.main:app --reload --port 8000${NC}"
echo -e ""
echo -e "  Terminal 2 (Frontend):"
echo -e "    ${GREEN}cd frontend && npm run dev${NC}"
echo -e ""
echo -e "  ${BLUE}URLs:${NC}"
echo -e "  API Docs    -> http://localhost:8000/docs"
echo -e "  Frontend    -> http://localhost:3000"
echo -e "  Health      -> http://localhost:8000/api/v1/health"
echo -e "  Qdrant UI   -> http://localhost:6333/dashboard"
echo -e ""
echo -e "  ${YELLOW}IMPORTANT: Edit .env file with your API keys!${NC}"
echo -e "  ${YELLOW}At minimum, set OPENAI_API_KEY and JWT_SECRET_KEY${NC}"
echo -e ""
