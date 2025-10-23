#!/usr/bin/env bash
set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  AAFC Herbarium DWC Extraction - Interactive Setup            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Check for uv
echo -e "${BLUE}Step 1/4:${NC} Checking for uv package manager..."
if command -v uv >/dev/null 2>&1; then
  UV_VERSION=$(uv --version 2>&1 || echo "unknown")
  echo -e "  ${GREEN}✓${NC} Found: $UV_VERSION"
else
  echo -e "  ${RED}✗${NC} uv not found"
  echo ""
  echo -e "${YELLOW}uv is required to manage Python dependencies.${NC}"
  echo ""
  echo "Install options:"
  echo "  macOS:   brew install uv"
  echo "  Linux:   curl -LsSf https://astral.sh/uv/install.sh | sh"
  echo "  Windows: powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\""
  echo ""
  read -p "Would you like to install uv now via curl? (y/N): " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Installing uv...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    echo -e "${GREEN}✓${NC} uv installed"
    echo -e "${YELLOW}⚠${NC}  You may need to restart your shell or run:"
    echo "     export PATH=\"\$HOME/.local/bin:\$PATH\""
  else
    echo -e "${RED}✗${NC} Cannot continue without uv. Please install it and run this script again."
    exit 1
  fi
fi
echo ""

# Step 2: Install dependencies
echo -e "${BLUE}Step 2/4:${NC} Installing Python dependencies..."
echo ""
echo "This will install:"
echo "  • Core dependencies (OCR engines, Darwin Core tools)"
echo "  • Development tools (ruff, pytest, mkdocs)"
echo ""
read -p "Continue? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
  echo -e "${BLUE}Running: uv sync --dev${NC}"
  uv sync --dev
  echo -e "${GREEN}✓${NC} Dependencies installed"
else
  echo -e "${YELLOW}⚠${NC}  Skipped dependency installation"
fi
echo ""

# Step 3: Environment configuration
echo -e "${BLUE}Step 3/4:${NC} Setting up environment configuration..."
if [ -f .env ]; then
  echo -e "  ${YELLOW}!${NC} .env file already exists"
  read -p "Overwrite with template? (y/N): " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    cp .env.example .env
    echo -e "  ${GREEN}✓${NC} .env overwritten from template"
  else
    echo -e "  ${BLUE}→${NC} Keeping existing .env"
  fi
else
  cp .env.example .env
  echo -e "  ${GREEN}✓${NC} Created .env from template"
fi
echo ""
echo -e "${YELLOW}API Key Setup:${NC}"
echo "  Your .env file currently has empty API keys."
echo ""
echo "  For macOS users:"
echo -e "    ${GREEN}✓${NC} Apple Vision API works out-of-the-box (FREE, no setup needed)"
echo ""
echo "  For Windows/Linux users or cloud APIs:"
echo "    • OpenAI: Get key from https://platform.openai.com/api-keys"
echo "    • Add to .env: OPENAI_API_KEY=sk-..."
echo ""
read -p "Open .env file now to add API keys? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  if command -v nano >/dev/null 2>&1; then
    nano .env
  elif command -v vim >/dev/null 2>&1; then
    vim .env
  elif command -v code >/dev/null 2>&1; then
    code .env
  else
    echo -e "${YELLOW}⚠${NC}  No editor found. Please manually edit .env"
  fi
fi
echo ""

# Step 4: Verify setup
echo -e "${BLUE}Step 4/4:${NC} Verifying setup..."
echo ""
read -p "Run dependency check now? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
  echo -e "${BLUE}Running: python cli.py check-deps${NC}"
  uv run python cli.py check-deps || true
else
  echo -e "${YELLOW}⚠${NC}  Skipped verification (run 'python cli.py check-deps' later)"
fi
echo ""

# Success summary
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Setup Complete! 🎉                                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo ""
echo "1. Verify your setup:"
echo -e "   ${BLUE}\$${NC} python cli.py check-deps"
echo ""
echo "2. Process specimen images:"
echo -e "   ${BLUE}\$${NC} python cli.py process --input photos/ --output results/"
echo ""
echo "3. Review extracted data:"
echo -e "   ${BLUE}\$${NC} python -m src.review.web_app --extraction-dir results/ --port 5002"
echo -e "   ${BLUE}\$${NC} open http://127.0.0.1:5002"
echo ""
echo "4. Learn more:"
echo "   • Documentation: https://aafc.devvyn.ca"
echo "   • README: cat README.md"
echo "   • Getting Started: docs/getting-started/installation.md"
echo ""
echo -e "${YELLOW}Need help?${NC} Check docs/troubleshooting.md or open an issue:"
echo "   https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues"
echo ""
