#!/usr/bin/env bash
# Mini Agent conda installation script
# Usage:
#   bash scripts/setup-conda.sh                 # install current repo in editable mode
#   bash scripts/setup-conda.sh my-env 3.11 dev
# Arguments:
#   $1: conda env name (default: mini-agent)
#   $2: python version (default: 3.11, must satisfy >=3.10)
#   $3: install mode: base|dev (default: dev)

set -euo pipefail

ENV_NAME="${1:-mini-agent}"
PYTHON_VERSION="${2:-3.11}"
INSTALL_MODE="${3:-dev}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

if ! command -v conda >/dev/null 2>&1; then
    echo -e "${RED}Error:${NC} conda command not found."
    echo "Please install Miniconda/Anaconda first."
    exit 1
fi

if [[ "${PYTHON_VERSION}" =~ ^3\.[0-9]+$ ]]; then
    PY_MINOR="${PYTHON_VERSION#3.}"
    if [ "${PY_MINOR}" -lt 10 ]; then
        echo -e "${RED}Error:${NC} Python ${PYTHON_VERSION} is not supported."
        echo "Mini Agent requires Python >= 3.10."
        exit 1
    fi
else
    echo -e "${YELLOW}Warning:${NC} python version format looks unusual: ${PYTHON_VERSION}"
    echo "Continuing, but ensure it satisfies >=3.10."
fi

# Enable `conda activate` in non-interactive shell.
eval "$(conda shell.bash hook)"

echo -e "${BLUE}[1/6]${NC} Creating/updating conda environment: ${ENV_NAME} (python=${PYTHON_VERSION})"
if conda env list | awk '{print $1}' | rg -x "${ENV_NAME}" >/dev/null 2>&1; then
    conda install -n "${ENV_NAME}" -y "python=${PYTHON_VERSION}"
else
    conda create -n "${ENV_NAME}" -y "python=${PYTHON_VERSION}"
fi

echo -e "${BLUE}[2/6]${NC} Activating environment: ${ENV_NAME}"
conda activate "${ENV_NAME}"

echo -e "${BLUE}[3/6]${NC} Upgrading pip/setuptools/wheel"
python -m pip install --upgrade pip setuptools wheel

echo -e "${BLUE}[4/6]${NC} Installing Mini Agent from current repository"
if [ "${INSTALL_MODE}" = "dev" ]; then
    python -m pip install -e ".[dev]"
else
    python -m pip install -e .
fi

echo -e "${BLUE}[5/6]${NC} Initializing git submodules (optional skills)"
git submodule update --init --recursive

echo -e "${BLUE}[6/6]${NC} Preparing local config file"
if [ ! -f "mini_agent/config/config.yaml" ]; then
    cp "mini_agent/config/config-example.yaml" "mini_agent/config/config.yaml"
    echo "Created mini_agent/config/config.yaml from template."
else
    echo "mini_agent/config/config.yaml already exists, skip."
fi

echo ""
echo -e "${GREEN}Environment ready.${NC}"
echo "To start using Mini Agent, run:"
echo "  conda activate ${ENV_NAME}"
echo "  mini-agent --version"
echo "  mini-agent"
