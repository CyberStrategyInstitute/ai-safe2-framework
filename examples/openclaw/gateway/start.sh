#!/bin/bash
set -e

# AI SAFE² Control Gateway - Startup Script
# Version: 2.1

echo "=================================================="
echo "AI SAFE² Control Gateway - Startup"
echo "=================================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo "[1/5] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 not found${NC}"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
echo ""

# Check pip
echo "[2/5] Checking pip..."
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}ERROR: pip3 not found${NC}"
    echo "Install with: sudo apt-get install python3-pip"
    exit 1
fi
echo -e "${GREEN}✓ pip3 found${NC}"
echo ""

# Install dependencies
echo "[3/5] Installing Python dependencies..."
pip3 install --quiet flask requests jsonschema pyyaml 2>&1 | grep -v "already satisfied" || true
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Check API key
echo "[4/5] Checking Anthropic API key..."
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${RED}ERROR: ANTHROPIC_API_KEY environment variable not set${NC}"
    echo ""
    echo "Set it with:"
    echo "  export ANTHROPIC_API_KEY=sk-ant-..."
    echo ""
    echo "Or add to your ~/.bashrc or ~/.zshrc:"
    echo "  echo 'export ANTHROPIC_API_KEY=\"sk-ant-...\"' >> ~/.bashrc"
    echo "  source ~/.bashrc"
    echo ""
    exit 1
fi

# Verify key format
if [[ ! $ANTHROPIC_API_KEY =~ ^sk-ant- ]]; then
    echo -e "${YELLOW}WARNING: API key doesn't match expected format (sk-ant-...)${NC}"
    echo "Continuing anyway..."
fi

echo -e "${GREEN}✓ API key configured${NC}"
echo ""

# Check config file
echo "[5/5] Checking configuration..."
if [ ! -f "config.yaml" ]; then
    echo -e "${RED}ERROR: config.yaml not found${NC}"
    echo "Create it from the template or ensure you're in the gateway directory"
    exit 1
fi

echo -e "${GREEN}✓ Configuration found${NC}"
echo ""

# Verify bind address (security check)
BIND_HOST=$(grep "bind_host:" config.yaml | awk '{print $2}' | tr -d '"')
if [ "$BIND_HOST" = "0.0.0.0" ]; then
    echo -e "${RED}WARNING: Gateway configured to bind to 0.0.0.0 (public internet)${NC}"
    echo "This is a security risk!"
    echo ""
    echo "Recommended: Change bind_host to 127.0.0.1 in config.yaml"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create logs directory if needed
mkdir -p logs

# Display final configuration
echo "=================================================="
echo "Starting AI SAFE² Control Gateway"
echo "=================================================="
echo ""
echo "Configuration:"
echo "  Bind Address: $BIND_HOST"
echo "  Port: $(grep "bind_port:" config.yaml | awk '{print $2}')"
echo "  Risk Threshold: $(grep "risk_threshold:" config.yaml | awk '{print $2}')"
echo "  High-Risk Tools: $(grep "allow_high_risk_tools:" config.yaml | awk '{print $2}')"
echo ""
echo "Logs: ./gateway_audit.log"
echo ""
echo "Health Check: http://$BIND_HOST:$(grep "bind_port:" config.yaml | awk '{print $2}')/health"
echo ""
echo "Press Ctrl+C to stop"
echo "=================================================="
echo ""

# Start gateway
python3 gateway.py
