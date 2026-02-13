#!/bin/bash
# =============================================================================
# SETUP LOCAL MAC - Framework Probabiliste DQ
# =============================================================================
# Usage: ./setup_mac.sh [--clean | --run | --full]
#   --clean : Nettoie caches et ancien venv uniquement
#   --run   : Lance l'app (suppose venv deja installe)
#   --full  : Clean + install + run (defaut)
# =============================================================================

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"

echo -e "${BLUE}=============================================${NC}"
echo -e "${BLUE}  Framework Probabiliste DQ - Setup Mac     ${NC}"
echo -e "${BLUE}=============================================${NC}"
echo ""

# --- Etape 1: Nettoyage complet des caches ---
clean_all() {
    echo -e "${YELLOW}[1/4] Nettoyage des caches...${NC}"

    # Python bytecode
    find "$PROJECT_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$PROJECT_DIR" -name "*.pyc" -delete 2>/dev/null || true
    find "$PROJECT_DIR" -name "*.pyo" -delete 2>/dev/null || true
    echo -e "  ${GREEN}OK${NC} __pycache__ et .pyc supprimes"

    # Streamlit caches (local au projet)
    rm -rf "$PROJECT_DIR/.streamlit/cache" 2>/dev/null || true
    rm -rf "$PROJECT_DIR/.streamlit/file_cache" 2>/dev/null || true
    echo -e "  ${GREEN}OK${NC} Cache Streamlit projet supprime"

    # Streamlit cache global (~/.streamlit)
    rm -rf "$HOME/.streamlit/cache" 2>/dev/null || true
    rm -rf "$HOME/.streamlit/file_cache" 2>/dev/null || true
    echo -e "  ${GREEN}OK${NC} Cache Streamlit global supprime"

    # Pytest cache
    rm -rf "$PROJECT_DIR/.pytest_cache" 2>/dev/null || true
    find "$PROJECT_DIR" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    echo -e "  ${GREEN}OK${NC} Cache pytest supprime"

    # macOS artifacts
    find "$PROJECT_DIR" -name ".DS_Store" -delete 2>/dev/null || true
    echo -e "  ${GREEN}OK${NC} .DS_Store supprimes"

    # Ancien venv
    if [ -d "$VENV_DIR" ]; then
        echo -e "  ${YELLOW}Suppression ancien venv...${NC}"
        rm -rf "$VENV_DIR"
        echo -e "  ${GREEN}OK${NC} Ancien venv supprime"
    fi

    # Autres venvs possibles
    for d in env .venv ENV; do
        if [ -d "$PROJECT_DIR/$d" ]; then
            rm -rf "$PROJECT_DIR/$d"
            echo -e "  ${GREEN}OK${NC} Ancien $d supprime"
        fi
    done

    echo ""
}

# --- Etape 2: Verification Python ---
check_python() {
    echo -e "${YELLOW}[2/4] Verification Python...${NC}"

    # Trouver python3
    if command -v python3 &>/dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &>/dev/null; then
        PYTHON_CMD="python"
    else
        echo -e "  ${RED}ERREUR: Python 3 non trouve.${NC}"
        echo -e "  Installe avec: ${BLUE}brew install python3${NC}"
        exit 1
    fi

    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
        echo -e "  ${RED}ERREUR: Python 3.9+ requis (actuel: $PYTHON_VERSION)${NC}"
        echo -e "  Mets a jour avec: ${BLUE}brew install python@3.11${NC}"
        exit 1
    fi

    echo -e "  ${GREEN}OK${NC} Python $PYTHON_VERSION ($PYTHON_CMD)"
    echo ""
}

# --- Etape 3: Creation venv + installation ---
install_deps() {
    echo -e "${YELLOW}[3/4] Creation environnement virtuel et installation...${NC}"

    $PYTHON_CMD -m venv "$VENV_DIR"
    echo -e "  ${GREEN}OK${NC} venv cree"

    # Activer venv
    source "$VENV_DIR/bin/activate"
    echo -e "  ${GREEN}OK${NC} venv active"

    # Upgrade pip
    pip install --upgrade pip --quiet
    echo -e "  ${GREEN}OK${NC} pip mis a jour"

    # Installer dependances
    echo -e "  Installation des dependances..."
    pip install -r "$PROJECT_DIR/requirements.txt"
    echo -e "  ${GREEN}OK${NC} Dependances installees"

    echo ""
}

# --- Etape 4: Lancement ---
run_app() {
    echo -e "${YELLOW}[4/4] Lancement de l'application...${NC}"

    # S'assurer que le venv est active
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
    else
        echo -e "  ${RED}ERREUR: venv non trouve. Lance d'abord: ./setup_mac.sh --full${NC}"
        exit 1
    fi

    # Verifier que streamlit est installe
    if ! command -v streamlit &>/dev/null; then
        echo -e "  ${RED}ERREUR: streamlit non installe dans le venv.${NC}"
        echo -e "  Lance: ./setup_mac.sh --full${NC}"
        exit 1
    fi

    STREAMLIT_VERSION=$(streamlit --version 2>&1)
    echo -e "  ${GREEN}OK${NC} $STREAMLIT_VERSION"

    echo ""
    echo -e "${GREEN}=============================================${NC}"
    echo -e "${GREEN}  Application prete !                        ${NC}"
    echo -e "${GREEN}  URL: http://localhost:8501                  ${NC}"
    echo -e "${GREEN}=============================================${NC}"
    echo -e "${YELLOW}  Ctrl+C pour arreter le serveur${NC}"
    echo ""

    # Lancer avec cache desactive pour premier lancement
    streamlit run "$PROJECT_DIR/app.py" \
        --server.port 8501 \
        --server.headless false \
        --global.dataFrameSerialization arrow
}

# --- Main ---
MODE="${1:---full}"

case "$MODE" in
    --clean)
        clean_all
        echo -e "${GREEN}Nettoyage termine. Lance ./setup_mac.sh --run pour demarrer.${NC}"
        ;;
    --run)
        run_app
        ;;
    --full)
        clean_all
        check_python
        install_deps
        run_app
        ;;
    *)
        echo "Usage: ./setup_mac.sh [--clean | --run | --full]"
        echo "  --clean : Nettoie caches et ancien venv"
        echo "  --run   : Lance l'app"
        echo "  --full  : Clean + install + run (defaut)"
        exit 1
        ;;
esac
