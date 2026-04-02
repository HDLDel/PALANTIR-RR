#!/bin/bash
# =============================================================================
# Script de Instalação do Palantir Linux
# Instala todas as dependências necessárias para compilar e executar
# =============================================================================

set -e  # Para o script em caso de erro

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "        PALANTIR LINUX - INSTALAÇÃO DE DEPENDÊNCIAS"
echo "============================================================"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para imprimir mensagens
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# 1. Verificar se é root (opcional, para instalar pacotes do sistema)
echo "[1/4] Verificando permissões..."
if [ "$EUID" -ne 0 ]; then
    print_info "Executando como usuário normal"
    print_info "Para instalar pacotes do sistema, execute: sudo $0"
else
    print_success "Executando como root"
fi

# 2. Instalar dependências do sistema
echo ""
echo "[2/4] Instalando dependências do sistema..."

# Detectar distribuição
DISTRO_ID=$(grep '^ID=' /etc/os-release 2>/dev/null | cut -d'=' -f2 | tr -d '"')
DISTRO_ID_LIKE=$(grep '^ID_LIKE=' /etc/os-release 2>/dev/null | cut -d'=' -f2 | tr -d '"')

print_info "Detectando distribuição..."
print_info "ID: $DISTRO_ID | ID_LIKE: $DISTRO_ID_LIKE"

# Fedora
if [ "$DISTRO_ID" = "fedora" ] || [[ "$DISTRO_ID_LIKE" == *"fedora"* ]]; then
    print_info "Distribuição Fedora detectada"

    if [ "$EUID" -eq 0 ]; then
        # Atualizar repositórios
        echo "      Atualizando repositórios..."
        dnf update -y -q > /dev/null 2>&1

        # Pacotes essenciais
        DEPS=(
            "python3"
            "python3-pip"
            "python3-tkinter"
            "aria2"
            "mpv"
            "vlc"
            "wget"
            "git"
            "python3-devel"
            "gcc"
            "gcc-c++"
        )

        for pkg in "${DEPS[@]}"; do
            echo "      Instalando $pkg..."
            dnf install -y -q "$pkg" > /dev/null 2>&1 || print_error "Falha ao instalar $pkg"
        done

        print_success "Dependências do sistema instaladas!"
    else
        print_info "Execute como root para instalar pacotes do sistema:"
        echo "      sudo dnf update -y"
        echo "      sudo dnf install -y python3 python3-pip python3-tkinter aria2 mpv vlc wget git python3-devel gcc gcc-c++"
    fi

# Ubuntu/Debian
elif [ "$DISTRO_ID" = "ubuntu" ] || [ "$DISTRO_ID" = "debian" ] || [ "$DISTRO_ID" = "linuxmint" ] || [[ "$DISTRO_ID_LIKE" == *"debian"* ]] || [[ "$DISTRO_ID_LIKE" == *"ubuntu"* ]]; then
    print_info "Distribuição Ubuntu/Debian detectada"

    if [ "$EUID" -eq 0 ]; then
        # Atualizar repositórios
        echo "      Atualizando repositórios..."
        apt-get update -qq > /dev/null 2>&1

        # Pacotes essenciais
        DEPS=(
            "python3"
            "python3-pip"
            "python3-venv"
            "python3-tk"
            "aria2"
            "mpv"
            "vlc"
            "wget"
            "git"
            "python3-dev"
            "build-essential"
        )

        for pkg in "${DEPS[@]}"; do
            echo "      Instalando $pkg..."
            apt-get install -y -qq "$pkg" > /dev/null 2>&1 || print_error "Falha ao instalar $pkg"
        done

        print_success "Dependências do sistema instaladas!"
    else
        print_info "Execute como root para instalar pacotes do sistema:"
        echo "      sudo apt-get update"
        echo "      sudo apt-get install -y python3 python3-pip python3-venv python3-tk aria2 mpv vlc wget git python3-dev build-essential"
    fi

# Arch Linux/Manjaro
elif [ "$DISTRO_ID" = "arch" ] || [ "$DISTRO_ID" = "manjaro" ] || [[ "$DISTRO_ID_LIKE" == *"arch"* ]]; then
    print_info "Arch Linux/Manjaro detectado"

    if [ "$EUID" -eq 0 ]; then
        # Pacotes essenciais
        echo "      Instalando pacotes..."
        pacman -S --noconfirm --quiet \
            python \
            python-pip \
            tk \
            aria2 \
            mpv \
            vlc \
            wget \
            git \
            base-devel || print_error "Falha ao instalar dependências"

        print_success "Dependências do sistema instaladas!"
    else
        print_info "Execute como root para instalar pacotes do sistema:"
        echo "      sudo pacman -S --noconfirm python python-pip tk aria2 mpv vlc wget git base-devel"
    fi

# openSUSE
elif [ "$DISTRO_ID" = "opensuse-leap" ] || [ "$DISTRO_ID" = "opensuse-tumbleweed" ] || [[ "$DISTRO_ID_LIKE" == *"opensuse"* ]]; then
    print_info "openSUSE detectado"

    if [ "$EUID" -eq 0 ]; then
        # Pacotes essenciais
        DEPS=(
            "python3"
            "python3-pip"
            "python3-tk"
            "aria2"
            "mpv"
            "vlc"
            "wget"
            "git"
            "python3-devel"
            "gcc"
            "gcc-c++"
        )

        for pkg in "${DEPS[@]}"; do
            echo "      Instalando $pkg..."
            zypper install -y -q "$pkg" > /dev/null 2>&1 || print_error "Falha ao instalar $pkg"
        done

        print_success "Dependências do sistema instaladas!"
    else
        print_info "Execute como root para instalar pacotes do sistema:"
        echo "      sudo zypper install -y python3 python3-pip python3-tk aria2 mpv vlc wget git python3-devel gcc gcc-c++"
    fi

else
    print_error "Distribuição não detectada ($DISTRO_ID)"
    print_info "Tentando instalação genérica..."
    
    if [ "$EUID" -eq 0 ]; then
        # Tenta dnf primeiro (Fedora/RHEL)
        if command -v dnf &> /dev/null; then
            print_info "Usando dnf..."
            dnf install -y -q python3 python3-pip python3-tkinter aria2 mpv vlc wget git 2>/dev/null && print_success "Instalação via dnf concluída!" || print_error "Falha no dnf"
        # Tenta apt (Debian/Ubuntu)
        elif command -v apt-get &> /dev/null; then
            print_info "Usando apt-get..."
            apt-get update -qq && apt-get install -y -qq python3 python3-pip python3-venv python3-tk aria2 mpv vlc wget git 2>/dev/null && print_success "Instalação via apt concluída!" || print_error "Falha no apt"
        # Tenta pacman (Arch)
        elif command -v pacman &> /dev/null; then
            print_info "Usando pacman..."
            pacman -S --noconfirm --quiet python python-pip tk aria2 mpv vlc wget git 2>/dev/null && print_success "Instalação via pacman concluída!" || print_error "Falha no pacman"
        # Tenta zypper (openSUSE)
        elif command -v zypper &> /dev/null; then
            print_info "Usando zypper..."
            zypper install -y -q python3 python3-pip python3-tk aria2 mpv vlc wget git 2>/dev/null && print_success "Instalação via zypper concluída!" || print_error "Falha no zypper"
        else
            print_error "Gerenciador de pacotes não encontrado!"
        fi
    else
        print_info "Execute como root (sudo) para tentar instalação automática"
    fi
    
    print_info "Ou instale manualmente:"
    echo "      - Python 3.8+"
    echo "      - python3-pip"
    echo "      - python3-tk (ou python3-tkinter)"
    echo "      - aria2"
    echo "      - mpv"
    echo "      - git"
fi

# 3. Instalar dependências Python
echo ""
echo "[3/4] Instalando dependências Python..."

# Criar venv se não existir
if [ ! -d "venv" ]; then
    print_info "Criando ambiente virtual (venv)..."
    python3 -m venv venv
    print_success "Ambiente virtual criado!"
else
    print_success "Ambiente virtual já existe"
fi

# Ativar venv
print_info "Ativando ambiente virtual..."
source venv/bin/activate

# Atualizar pip
print_info "Atualizando pip..."
pip install --upgrade pip -q

# Instalar requirements
if [ -f "requirements.txt" ]; then
    print_info "Instalando dependências do requirements.txt..."
    pip install -r requirements.txt -q
    print_success "Dependências Python instaladas!"
else
    print_error "requirements.txt não encontrado!"
    exit 1
fi

# Instalar pyinstaller e dependências extras (para compilar)
print_info "Instalando PyInstaller e dependências extras..."
pip install pyinstaller websocket-client loguru platformdirs colorama -q

# 5. Criar ícone no menu do sistema
echo ""
echo "[5/5] Criando ícone no menu do sistema..."

LOCAL_APPS="$HOME/.local/share/applications"
LOCAL_ICONS="$HOME/.local/share/icons"
PALANTIR_EXEC="$SCRIPT_DIR/Palantir"
PALANTIR_ICON="$SCRIPT_DIR/Palantir.png"

# Cria diretórios locais se não existirem
mkdir -p "$LOCAL_APPS"
mkdir -p "$LOCAL_ICONS"

# Verifica se o executável existe
if [ -f "$PALANTIR_EXEC" ]; then
    # Torna executável se não for
    if [ ! -x "$PALANTIR_EXEC" ]; then
        chmod +x "$PALANTIR_EXEC"
    fi
    
    # Copia o ícone se existir
    ICON_PATH="application-x-executable"
    if [ -f "$PALANTIR_ICON" ]; then
        cp "$PALANTIR_ICON" "$LOCAL_ICONS/palantir.png"
        ICON_PATH="palantir.png"
        print_success "Ícone instalado em: $LOCAL_ICONS/palantir.png"
    elif [ -f "$SCRIPT_DIR/_internal/Palantir.png" ]; then
        cp "$SCRIPT_DIR/_internal/Palantir.png" "$LOCAL_ICONS/palantir.png"
        ICON_PATH="palantir.png"
        print_success "Ícone instalado em: $LOCAL_ICONS/palantir.png"
    fi
    
    # Cria o arquivo .desktop
    DESKTOP_FILE="$LOCAL_APPS/palantir.desktop"
    
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Palantir
GenericName=Downloader
Comment=Palantir - Download Manager para Séries e Filmes
Exec=$PALANTIR_EXEC
Icon=$ICON_PATH
Path=$SCRIPT_DIR
Terminal=false
Categories=AudioVideo;Video;Utility;
Keywords=download;torrent;aria2;video;series;movies;
StartupNotify=true
StartupWMClass=Palantir
EOF
    
    print_success "Arquivo .desktop criado em: $DESKTOP_FILE"
    
    # Tenta copiar para pixmaps se tiver permissão
    if [ -w "/usr/share/pixmaps" ] || [ $(id -u) -eq 0 ]; then
        if [ -f "$PALANTIR_ICON" ]; then
            cp "$PALANTIR_ICON" "/usr/share/pixmaps/palantir.png" 2>/dev/null || true
            print_success "Ícone também instalado em: /usr/share/pixmaps/palantir.png"
        fi
    fi
    
    # Atualiza o banco de dados de aplicativos
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$LOCAL_APPS" 2>/dev/null || true
        print_success "Banco de dados de aplicativos atualizado"
    fi
    
    # Tenta atualizar o cache de ícones
    if command -v gtk-update-icon-cache &> /dev/null; then
        gtk-update-icon-cache -f "$LOCAL_ICONS" 2>/dev/null || true
        print_success "Cache de ícones atualizado"
    fi
    
    echo ""
    print_success "Ícone do Palantir criado no menu de aplicativos!"
    echo ""
    echo "  Se não aparecer imediatamente, tente:"
    echo "    1. Fazer logout e login novamente"
    echo "    2. Ou executar: killall gnome-shell (GNOME)"
    echo "    3. Ou executar: kbuildsycoca5 (KDE)"
    echo ""
else
    print_error "Executável não encontrado em: $PALANTIR_EXEC"
    print_info "O ícone será criado quando o Palantir for compilado"
fi

# 4. Verificar instalação
echo ""
echo "[6/6] Verificando instalação..."

echo ""
echo "============================================================"
echo "  RESUMO:"
echo "============================================================"
echo ""
echo "  ✓ Dependências do sistema: Instaladas (ou pendentes se não-root)"
echo "  ✓ Ambiente virtual: Criado em ./venv"
echo "  ✓ Dependências Python: Instaladas"
echo "  ✓ PyInstaller: Instalado"
echo "  ✓ Ícone no menu: Criado (se executável existir)"
echo ""
echo "============================================================"
echo "  PRÓXIMOS PASSOS:"
echo "============================================================"
echo ""
echo "  1. Ative o ambiente virtual:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Coloque os players na pasta Players/:"
echo "     - mpv.AppImage ou mpv/mpv"
echo "     - VLC.AppImage ou VLCPortable/VLCPortable"
echo ""
echo "  3. Para executar:"
echo "     ./Palantir  (aparecerá no menu de aplicativos)"
echo "     ou"
echo "     python3 Palantir-Linux.py"
echo ""
echo "  4. Para compilar:"
echo "     python3 build_linux.py"
echo ""
echo "============================================================"
echo ""
