#!/bin/bash
# =============================================================================
# PALANTIR - Build Script para Linux
# Gera pacote executável com todas as dependências
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
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
    echo -e "${BLUE}        PALANTIR - BUILD UNIFICADO LINUX${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""
    echo "Uso: $0 [modo]"
    echo ""
    echo "Modos disponíveis:"
    echo -e "  ${GREEN}onefolder${NC}, ${GREEN}1${NC}     - Gera pasta dist/Palantir/"
    echo -e "  ${GREEN}appimage${NC}, ${GREEN}2${NC}      - Gera AppImage (requer FUSE)"
    echo -e "  ${GREEN}all${NC}, ${GREEN}a${NC}            - Gera todos os formatos (padrão)"
    echo -e "  ${GREEN}help${NC}, ${GREEN}h${NC}           - Mostra esta ajuda"
    echo ""
    echo "Exemplos:"
    echo "  $0              # Build completo"
    echo "  $0 onefolder    # Apenas pasta executável"
    echo "  $0 appimage     # Apenas AppImage"
    echo ""
    echo -e "${BLUE}============================================================${NC}"
}

# Função para imprimir status
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Verifica argumentos
MODE="all"
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
print_success "Python $PYTHON_VERSION detectado"

# Verifica se está no ambiente virtual
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}ℹ${NC} Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativa ambiente virtual
source venv/bin/activate

# Atualiza pip
print_success "Atualizando pip..."
pip install --upgrade pip -q

# Instala dependências
echo ""
print_info "Instalando dependências Python..."
pip install requests unidecode customtkinter ttkthemes Pillow aria2p pyinstaller urllib3 -q
print_success "Dependências instaladas!"

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}        INICIANDO BUILD: ${YELLOW}${MODE^^}${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Função para build onefolder
build_onefolder() {
    print_info "Criando build OneFolder..."

    python3 -m PyInstaller \
        --name=Palantir \
        --console \
        --clean \
        --noconfirm \
        --add-data="categorias.py:." \
        --add-data="advanced_downloader.py:." \
        --add-data="organize_folders.py:." \
        --add-data="organize_folders_wrapper.py:." \
        --hidden-import=customtkinter \
        --hidden-import=ttkthemes \
        --hidden-import=aria2p \
        --hidden-import=unidecode \
        --hidden-import=PIL \
        --hidden-import=requests \
        --hidden-import=urllib3 \
        --hidden-import=sqlite3 \
        --hidden-import=logging \
        --hidden-import=datetime \
        --hidden-import=concurrent.futures \
        --hidden-import=threading \
        --hidden-import=subprocess \
        --hidden-import=platform \
        --hidden-import=webbrowser \
        --hidden-import=shutil \
        --hidden-import=re \
        --hidden-import=unicodedata \
        --collect-all=customtkinter \
        --collect-all=ttkthemes \
        --collect-all=PIL \
        Palantir-Linux.py

    if [ $? -eq 0 ]; then
        print_success "Build OneFolder concluído!"
        echo ""
        echo -e "${GREEN}Distribuição pronta em: ${PROJECT_DIR}/dist/Palantir/${NC}"
    else
        print_error "Build OneFolder falhou!"
        return 1
    fi
}

# Função para build AppImage
build_appimage() {
    print_info "Criando AppImage..."

    # Verifica FUSE
    if ! ldconfig -p | grep -q "libfuse"; then
        print_error "FUSE não encontrado!"
        print_info "Instale: sudo apt install libfuse2 (Ubuntu/Debian)"
        print_info "Ou: sudo dnf install fuse (Fedora)"
        return 1
    fi

    # Primeiro faz o build onefolder
    build_onefolder || return 1

    # Cria estrutura AppDir
    APPDIR_DIR="${PROJECT_DIR}/AppDir"
    rm -rf "$APPDIR_DIR"
    mkdir -p "$APPDIR_DIR/usr/bin"
    mkdir -p "$APPDIR_DIR/usr/lib/Palantir"
    mkdir -p "$APPDIR_DIR/usr/share/applications"
    mkdir -p "$APPDIR_DIR/usr/share/icons/hicolor/256x256/apps"

    # Copia arquivos
    cp -r "${PROJECT_DIR}/dist/Palantir/"* "$APPDIR_DIR/usr/lib/Palantir/"
    cp "${PROJECT_DIR}/dist/Palantir/Palantir" "$APPDIR_DIR/usr/bin/"

    # Cria AppRun
    cat > "$APPDIR_DIR/AppRun" << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${HERE}/usr/lib/Palantir:${LD_LIBRARY_PATH}"
exec "${HERE}/usr/bin/Palantir" "$@"
EOF
    chmod +x "$APPDIR_DIR/AppRun"

    # Cria arquivo .desktop
    cat > "$APPDIR_DIR/usr/share/applications/palantir.desktop" << 'EOF'
[Desktop Entry]
Type=Application
Name=Palantir
Comment=Gerenciador e Baixador de Vídeos
Exec=Palantir
Icon=palantir
Categories=AudioVideo;Video;
EOF

    # Copia ícone se existir
    if [ -f "${PROJECT_DIR}/palantir.png" ]; then
        cp "${PROJECT_DIR}/palantir.png" "$APPDIR_DIR/usr/share/icons/hicolor/256x256/apps/palantir.png"
        cp "${PROJECT_DIR}/palantir.png" "$APPDIR_DIR/palantir.png"
    fi

    # Baixa appimagetool se não existir
    APPIMAGETOOL="${SCRIPT_DIR}/appimagetool"
    if [ ! -f "$APPIMAGETOOL" ]; then
        print_info "Baixando appimagetool..."
        wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" \
            -O "$APPIMAGETOOL"
        chmod +x "$APPIMAGETOOL"
        print_success "appimagetool baixado"
    fi

    # Cria AppImage
    ARCH=x86_64 "$APPIMAGETOOL" -v "$APPDIR_DIR" "${PROJECT_DIR}/Palantir-x86_64.AppImage"

    if [ $? -eq 0 ]; then
        SIZE=$(du -h "${PROJECT_DIR}/Palantir-x86_64.AppImage" | cut -f1)
        print_success "AppImage criado: Palantir-x86_64.AppImage ($SIZE)"
    else
        print_error "Falha ao criar AppImage"
        return 1
    fi
}

# Executa build no modo selecionado
case "$MODE" in
    onefolder)
        build_onefolder
        ;;
    appimage)
        build_appimage
        ;;
    all)
        build_onefolder
        echo ""
        build_appimage
        ;;
esac

EXIT_CODE=$?

# Desativa ambiente virtual
deactivate 2>/dev/null

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}        BUILD CONCLUÍDO COM SUCESSO!${NC}"
    echo -e "${GREEN}============================================================${NC}"
    echo ""
    if [ "$MODE" = "onefolder" ] || [ "$MODE" = "all" ]; then
        echo -e "  Pasta: ${GREEN}${PROJECT_DIR}/dist/Palantir/${NC}"
        echo -e "  Para executar: ${GREEN}cd ${PROJECT_DIR}/dist/Palantir && ./Palantir${NC}"
    fi
    if [ "$MODE" = "appimage" ] || [ "$MODE" = "all" ]; then
        echo -e "  AppImage: ${GREEN}${PROJECT_DIR}/Palantir-x86_64.AppImage${NC}"
        echo -e "  Para executar: ${GREEN}chmod +x Palantir-x86_64.AppImage && ./Palantir-x86_64.AppImage${NC}"
    fi
else
    echo -e "${RED}============================================================${NC}"
    echo -e "${RED}        BUILD FALHOU!${NC}"
    echo -e "${RED}============================================================${NC}"
fi

exit $EXIT_CODE
