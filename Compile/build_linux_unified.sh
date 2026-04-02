#!/bin/bash
# =============================================================================
# Wrapper para o Build Unificado do Palantir Linux
# Facilita a execução do script Python
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Função de ajuda
show_help() {
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}        PALANTIR LINUX - BUILD UNIFICADO${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""
    echo "Uso: $0 [modo]"
    echo ""
    echo "Modos disponíveis:"
    echo -e "  ${GREEN}onefolder${NC}, ${GREEN}1${NC}     - Gera apenas pasta dist/Palantir/"
    echo -e "  ${GREEN}appimage${NC}, ${GREEN}2${NC}      - Gera AppImage + TAR.GZ"
    echo -e "  ${GREEN}all${NC}, ${GREEN}a${NC}            - Gera todos os formatos (padrão)"
    echo -e "  ${GREEN}help${NC}, ${GREEN}h${NC}           - Mostra esta ajuda"
    echo ""
    echo "Exemplos:"
    echo "  $0              # Build completo (todos os formatos)"
    echo "  $0 onefolder    # Apenas pasta executável"
    echo "  $0 appimage     # Apenas AppImage + TAR.GZ"
    echo ""
    echo -e "${BLUE}============================================================${NC}"
}

# Verifica argumentos
case "${1,,}" in
    help|h|-h|--help)
        show_help
        exit 0
        ;;
    onefolder|1|one)
        MODE="onefolder"
        ;;
    appimage|2|app)
        MODE="appimage"
        ;;
    all|a|complete|"")
        MODE="all"
        ;;
    *)
        echo -e "${RED}Argumento desconhecido: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac

# Verifica Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Erro: Python 3 não encontrado!${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION detectado"

# Verifica se está no ambiente virtual
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}ℹ${NC} Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativa ambiente virtual
source venv/bin/activate

# Atualiza pip
echo -e "${GREEN}✓${NC} Atualizando pip..."
pip install --upgrade pip -q

# Executa script Python
echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}        INICIANDO BUILD: ${YELLOW}${MODE^^}${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

python3 Compile/build_linux_unified.py "$MODE"
EXIT_CODE=$?

# Desativa ambiente virtual
deactivate 2>/dev/null

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}        BUILD CONCLUÍDO COM SUCESSO!${NC}"
    echo -e "${GREEN}============================================================${NC}"
else
    echo -e "${RED}============================================================${NC}"
    echo -e "${RED}        BUILD FALHOU!${NC}"
    echo -e "${RED}============================================================${NC}"
fi

exit $EXIT_CODE
