#!/bin/bash

# Muda para o diretório do script
cd "$(dirname "$0")" || exit

# Navega para a pasta raiz do projeto (pai da pasta Compile)
cd .. || exit

# Salva o caminho da raiz do projeto
PROJECT_DIR=$(pwd)

echo "============================================================"
echo "         INSTALADOR DE DEPENDÊNCIAS - PALANTIR"
echo "============================================================"
echo ""

# Permite a instalação global ignorando o erro "externally-managed-environment" (Arch Linux, Ubuntu 23.04+, etc)
export PIP_BREAK_SYSTEM_PACKAGES=1

# Verifica se o Python 3 está instalado
if ! command -v python3 &> /dev/null; then
    echo "[ERRO] Python 3 não encontrado!"
    echo ""
    echo "Por favor, instale o Python 3.8 ou superior:"
    echo "Ubuntu/Debian/Mint: sudo apt update && sudo apt install python3 python3-pip"
    echo "Fedora/RHEL:        sudo dnf install python3 python3-pip"
    echo "Arch Linux/Manjaro: sudo pacman -S python python-pip"
    echo ""
    exit 1
fi

# Mostra versão do Python
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "[OK] Python detectado: $PYTHON_VERSION"
echo ""

# Verifica versão do Python (deve ser 3.8+)
if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" &> /dev/null; then
    echo "[ERRO] Python 3.8 ou superior é necessário!"
    echo "Sua versão é inferior a 3.8."
    echo ""
    exit 1
fi

# Verifica se o pip está instalado
if ! python3 -m pip --version &> /dev/null; then
    echo "[ERRO] Módulo 'pip' não encontrado!"
    echo ""
    echo "Por favor, instale o pip para o Python 3:"
    echo "Ubuntu/Debian/Mint: sudo apt update && sudo apt install python3-pip"
    echo "Fedora/RHEL:        sudo dnf install python3-pip"
    echo "Arch Linux/Manjaro: sudo pacman -S python-pip"
    echo ""
    exit 1
fi

# Atualiza o pip
echo "[INFO] Atualizando o pip..."
if ! python3 -m pip install --upgrade pip --quiet; then
    echo "[AVISO] Não foi possível atualizar o pip, continuando..."
fi
echo ""

# Instala as dependências do requirements.txt
# Tenta procurar na raiz e depois na pasta Compile
REQ_FILE=""
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    REQ_FILE="$PROJECT_DIR/requirements.txt"
elif [ -f "$PROJECT_DIR/Compile/requirements.txt" ]; then
    REQ_FILE="$PROJECT_DIR/Compile/requirements.txt"
fi

if [ -n "$REQ_FILE" ]; then
    echo "[INFO] Instalando dependências de $REQ_FILE..."
    echo ""
    if ! python3 -m pip install -r "$REQ_FILE"; then
        echo ""
        echo "[ERRO] Falha ao instalar algumas dependências!"
        echo ""
        exit 1
    fi
    echo ""
    echo "[OK] Dependências instaladas com sucesso!"
else
    echo "[AVISO] requirements.txt não encontrado, instalando pacotes manualmente..."
    echo ""

    # Instala cada pacote individualmente
    echo "[INFO] Instalando dependências principais..."
    python3 -m pip install requests>=2.31.0 aria2p>=0.12.1 Pillow>=8.0.0 customtkinter>=5.2.0 --quiet
    python3 -m pip install unidecode>=1.3.8 ttkthemes>=3.2.2 psutil>=5.9.0 urllib3>=2.0.0 --quiet
    python3 -m pip install websocket-client>=1.8.0 loguru>=0.7.3 platformdirs>=4.3.7 colorama>=0.4.6 pyinstaller>=6.0.0 --quiet

    echo ""
    echo "[OK] Todas as dependências instaladas!"
fi

echo ""
echo "============================================================"
echo "         INSTALAÇÃO CONCLUÍDA COM SUCESSO!"
echo "============================================================"
echo ""
echo "Dependências instaladas (Python):"
echo "  - requests, aria2p, Pillow, customtkinter, unidecode,"
echo "  - ttkthemes, psutil, urllib3, websocket-client,"
echo "  - loguru, platformdirs, colorama, pyinstaller"
echo ""
echo "Lembrete para usuários LINUX:"
echo "Certifique-se de que os pacotes de sistema estejam instalados, incluindo o Tkinter, Aria2 e o MPV."
echo ""
echo "Debian/Ubuntu/Mint:"
echo "  sudo apt update"
echo "  sudo apt install python3-tk tk aria2 mpv"
echo ""
echo "Fedora/RHEL:"
echo "  sudo dnf install python3-tkinter tk aria2 mpv"
echo ""
echo "Arch Linux/Manjaro:"
echo "  sudo pacman -S tk aria2 mpv"
echo ""
echo "Próximos passos:"
echo "  1. Para compilar o programa, você pode criar um script equivalente"
echo "     ao build_windows.py para Linux, ou testar a aplicação com:"
echo "     python3 Palantir-Linux.py"
echo ""
echo "============================================================"