#!/usr/bin/env python3
"""
Build Unificado do Palantir Linux
Gera pacotes: OneFolder, AppImage e TAR.GZ
Consolida build_linux.py e build_appimage.py em um único script
"""

import os
import sys
import subprocess
import shutil
import tarfile
from pathlib import Path
from typing import Optional, List, Tuple

# =============================================================================
# CONFIGURAÇÕES GERAIS
# =============================================================================

# Usa a pasta raiz do projeto (Inteligente)
SCRIPT_DIR = Path(__file__).parent.absolute()
if (SCRIPT_DIR / "Palantir-windows.py").exists() or (SCRIPT_DIR / "Palantir-Linux.py").exists():
    PROJECT_DIR = SCRIPT_DIR
else:
    PROJECT_DIR = SCRIPT_DIR.parent  # Pasta raiz do projeto
PLAYERS_DIR = PROJECT_DIR / "Players"
DIST_DIR = PROJECT_DIR / "dist"
APPDIR_DIR = PROJECT_DIR / "AppDir"

# Pacotes Python necessários
PACKAGES_BASE = [
    "requests", "aria2p", "Pillow", "customtkinter",
    "unidecode", "ttkthemes", "psutil", "pyinstaller", "urllib3"
]

PACKAGES_EXTRAS = [
    "websocket-client", "loguru", "platformdirs", "colorama"
]

# Arquivos do projeto para incluir no build
PROJECT_FILES = [
    "advanced_downloader.py",
    "organize_folders.py",
    "organize_folders_wrapper.py",
    "categorias.py",
]

# Arquivos de dados
DATA_FILES = [
    "downloads.db",
    "config.json",
    "palantir.png",
]

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def print_header(title: str):
    """Imprime cabeçalho formatado"""
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)
    print()

def print_step(step: int, total: int, message: str):
    """Imprime passo atual"""
    print(f"\n[{step}/{total}] {message}")

def print_success(message: str):
    """Imprime mensagem de sucesso"""
    print(f"      ✓ {message}")

def print_warning(message: str):
    """Imprime aviso"""
    print(f"      ⚠ {message}")

def print_error(message: str):
    """Imprime erro"""
    print(f"      ✗ {message}")

def print_info(message: str):
    """Imprime informação"""
    print(f"      ℹ {message}")

def find_executable(names: List[Path], description: str) -> Optional[Path]:
    """Procura executável em múltiplos caminhos"""
    for path in names:
        if path.exists():
            print_success(f"{description}: {path.relative_to(PROJECT_DIR)}")
            return path

    print_warning(f"{description} - não encontrado")
    return None

def install_packages(packages: List[str], quiet: bool = True):
    """Instala pacotes Python via pip"""
    for pkg in packages:
        print(f"      Instalando {pkg}...")
        cmd = [sys.executable, "-m", "pip", "install", pkg, "--upgrade"]
        if quiet:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(cmd)

def detect_distro() -> Tuple[str, str]:
    """Detecta distribuição Linux"""
    distro_id = ""
    distro_id_like = ""

    try:
        with open('/etc/os-release', 'r') as f:
            for line in f:
                if line.startswith('ID='):
                    distro_id = line.strip().split('=')[1].strip('"')
                elif line.startswith('ID_LIKE='):
                    distro_id_like = line.strip().split('=')[1].strip('"')
    except:
        pass

    return distro_id, distro_id_like

def is_wsl() -> bool:
    """Detecta se está rodando no WSL"""
    try:
        with open('/proc/version', 'r') as f:
            content = f.read().lower()
            return 'microsoft' in content or 'wsl' in content
    except:
        return False

# =============================================================================
# ETAPAS DO BUILD
# =============================================================================

def check_python() -> bool:
    """Verifica versão do Python"""
    print_info(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    if sys.version_info < (3, 8):
        print_error("Python 3.8+ é necessário!")
        return False

    return True

def install_dependencies(packages: List[str]) -> bool:
    """Instala dependências Python"""
    print_info("Instalando dependências...")

    try:
        install_packages(packages)
        print_success("Dependências instaladas!")
        return True
    except Exception as e:
        print_error(f"Falha ao instalar dependências: {e}")
        return False

def check_executables() -> Tuple[Optional[Path], Optional[Path], Optional[Path]]:
    """Verifica executáveis necessários (aria2c, mpv, vlc)"""
    print_info("Verificando executáveis...")

    # aria2c
    aria2c_paths = [
        PROJECT_DIR / "aria2c",
        PROJECT_DIR / "aria2c" / "aria2c",
    ]
    aria2c = find_executable(aria2c_paths, "aria2c")
    if not aria2c:
        print_info("Instale: sudo apt install aria2")

    # mpv
    mpv_paths = [
        PLAYERS_DIR / "mpv" / "mpv",
        PLAYERS_DIR / "mpv.AppImage",
        PLAYERS_DIR / "mpv" / "mpv.AppImage",
    ]
    mpv = find_executable(mpv_paths, "mpv")
    if not mpv:
        print_info("Coloque mpv ou mpv.AppImage em Players/")

    # vlc
    vlc_paths = [
        PLAYERS_DIR / "VLCPortable" / "VLCPortable",
        PLAYERS_DIR / "VLC.AppImage",
        PLAYERS_DIR / "VLCPortable" / "VLC.AppImage",
    ]
    vlc = find_executable(vlc_paths, "vlc")
    if not vlc:
        print_info("Coloque VLC.AppImage ou VLCPortable em Players/")

    return aria2c, mpv, vlc

def run_pyinstaller(output_name: str = "Palantir") -> bool:
    """Executa PyInstaller para compilar o projeto"""
    print_info("Executando PyInstaller (OneFolder)...")

    aria2c, mpv, vlc = check_executables()

    # Comando base do PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        f"--name={output_name}",
        "--console",
        f"--icon={PROJECT_DIR / 'palantir.png'}",
        "--clean",
        "--noconfirm",
    ]

    # Adicionar arquivos de dados
    for file in PROJECT_FILES:
        if (PROJECT_DIR / file).exists():
            cmd.append(f"--add-data={PROJECT_DIR / file}:.")

    for file in DATA_FILES:
        if (PROJECT_DIR / file).exists():
            cmd.append(f"--add-data={PROJECT_DIR / file}:.")

    # Adicionar aria2c se existir
    if aria2c:
        cmd.append(f"--add-data={aria2c}:.")

    # Hidden imports
    hidden_imports = [
        "customtkinter", "ttkthemes", "aria2p", "unidecode",
        "PIL", "requests", "urllib3", "sqlite3", "logging",
        "datetime", "concurrent.futures"
    ]

    for imp in hidden_imports:
        cmd.append(f"--hidden-import={imp}")

    # Coletar pacotes completos
    cmd.extend([
        "--collect-all=customtkinter",
        "--collect-all=ttkthemes",
    ])

    # Script principal (Palantir-Linux.py na raiz)
    cmd.append(str(PROJECT_DIR / "Palantir-Linux.py"))

    print_info("Compilando...")
    result = subprocess.run(cmd, cwd=PROJECT_DIR)

    if result.returncode == 0:
        print_success("Build PyInstaller concluído!")
        return True
    else:
        print_error("Erro no build PyInstaller!")
        return False

def copy_players_to_dist(dist_folder: Path):
    """Copia pasta Players para o diretório de distribuição"""
    players_dest = dist_folder / "Players"

    # Remove Players duplicado em _internal se existir
    players_internal = dist_folder / "_internal" / "Players"
    if players_internal.exists():
        shutil.rmtree(players_internal)
        print_info("Removida Players/ duplicada em _internal/")

    # Copia da pasta original
    if PLAYERS_DIR.exists():
        if players_dest.exists():
            shutil.rmtree(players_dest)
        shutil.copytree(PLAYERS_DIR, players_dest)
        print_success("Players/ copiada para distribuição")
    else:
        print_warning("Players/ não encontrada no projeto")

def create_appdir(dist_folder: Path, aria2c: Optional[Path]) -> bool:
    """Cria estrutura AppDir para AppImage"""
    print_info("Criando AppDir...")

    # Limpa AppDir se existir
    if APPDIR_DIR.exists():
        shutil.rmtree(APPDIR_DIR)

    # Cria estrutura de diretórios
    dirs = [
        APPDIR_DIR,
        APPDIR_DIR / "usr" / "bin",
        APPDIR_DIR / "usr" / "lib" / "Palantir",
        APPDIR_DIR / "usr" / "share" / "applications",
        APPDIR_DIR / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    # Copia executável principal
    exe_source = dist_folder / "Palantir"
    if exe_source.exists():
        shutil.copy2(exe_source, APPDIR_DIR / "usr" / "bin" / "Palantir")
        print_success("Copiado: Palantir")

    # Copia _internal (bibliotecas)
    internal_source = dist_folder / "_internal"
    if internal_source.exists():
        shutil.copytree(internal_source, APPDIR_DIR / "usr" / "lib" / "Palantir", dirs_exist_ok=True)
        print_success("Copiado: _internal (bibliotecas)")

    # Copia Players
    players_source = dist_folder / "Players"
    if players_source.exists():
        shutil.copytree(players_source, APPDIR_DIR / "usr" / "lib" / "Palantir" / "Players", dirs_exist_ok=True)
        print_success("Copiado: Players/")

    # Copia config.json
    config_source = PROJECT_DIR / "config.json"
    if config_source.exists():
        shutil.copy2(config_source, APPDIR_DIR / "usr" / "lib" / "Palantir" / "config.json")
        print_success("Copiado: config.json")

    # Copia aria2c se existir
    if aria2c:
        shutil.copy2(aria2c, APPDIR_DIR / "usr" / "bin" / "aria2c")
        print_success("Copiado: aria2c")

    # Cria AppRun
    apprun_content = '''#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${HERE}/usr/lib/Palantir:${LD_LIBRARY_PATH}"
exec "${HERE}/usr/bin/Palantir" "$@"
'''
    with open(APPDIR_DIR / "AppRun", "w") as f:
        f.write(apprun_content)
    os.chmod(APPDIR_DIR / "AppRun", 0o755)
    print_success("Criado: AppRun")

    # Cria arquivo .desktop
    desktop_content = '''[Desktop Entry]
Type=Application
Name=Palantir
Comment=Gerenciador e Baixador de Vídeos
Exec=Palantir
Icon=palantir
Categories=AudioVideo;Video;
'''
    desktop_path = APPDIR_DIR / "usr" / "share" / "applications" / "palantir.desktop"
    with open(desktop_path, "w") as f:
        f.write(desktop_content)

    # Copia ícone
    icon_source = PROJECT_DIR / "palantir.png"
    if icon_source.exists():
        icon_dest = APPDIR_DIR / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps" / "palantir.png"
        shutil.copy2(icon_source, icon_dest)
        shutil.copy2(icon_source, APPDIR_DIR / "palantir.png")

        # Também cria arquivo .desktop na raiz do AppDir
        with open(APPDIR_DIR / "palantir.desktop", "w") as f:
            f.write(desktop_content)

        print_success("Copiado: ícone")

    return True

def create_appimage() -> Optional[Path]:
    """Cria AppImage usando appimagetool"""
    print_info("Criando AppImage...")

    appimage_output = PROJECT_DIR / "Palantir-x86_64.AppImage"
    appimagetool_path = SCRIPT_DIR / "appimagetool"

    # Remove AppImage antigo
    if appimage_output.exists():
        appimage_output.unlink()
        print_info("Removido AppImage antigo")

    # Verifica se está no WSL
    if is_wsl():
        print_info("WSL detectado - AppImage não funciona bem no WSL")
        return None

    # Baixa appimagetool se não existir
    if not appimagetool_path.exists():
        print_info("Baixando appimagetool...")
        try:
            import urllib.request
            url = "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
            urllib.request.urlretrieve(url, appimagetool_path)
            os.chmod(appimagetool_path, 0o755)
            print_success("appimagetool baixado")
        except Exception as e:
            print_error(f"Falha ao baixar appimagetool: {e}")
            print_info("Baixe manualmente de: https://github.com/AppImage/AppImageKit/releases")
            return None

    # Executa appimagetool
    env = os.environ.copy()
    env["ARCH"] = "x86_64"

    try:
        result = subprocess.run(
            [str(appimagetool_path), "-v", str(APPDIR_DIR), str(appimage_output)],
            env=env,
            cwd=PROJECT_DIR
        )

        if result.returncode == 0:
            print_success("AppImage criado com sucesso!")
            return appimage_output
        else:
            print_error(f"Erro ao criar AppImage (código {result.returncode})")
            return None
    except Exception as e:
        print_error(f"Erro ao executar appimagetool: {e}")
        return None

def create_tarball(name: str = "Palantir-Linux-x86_64.tar.gz", source_dir: Optional[Path] = None) -> Path:
    """Cria pacote TAR.GZ como alternativa ao AppImage"""
    print_info("Criando pacote tar.gz...")

    tarball_output = PROJECT_DIR / name

    # Se source_dir não for especificado, usa AppDir
    if source_dir is None:
        source_dir = APPDIR_DIR

    with tarfile.open(tarball_output, "w:gz") as tar:
        tar.add(source_dir, arcname="Palantir")

    size_mb = tarball_output.stat().st_size / (1024 * 1024)
    print_success(f"Pacote criado: {tarball_output.name} ({size_mb:.1f} MB)")

    return tarball_output

def create_dist_folder(dist_folder: Path) -> bool:
    """Cria pasta de distribuição final"""
    print_info("Preparando pasta de distribuição...")

    if not dist_folder.exists():
        print_error("Pasta de distribuição não encontrada!")
        return False

    print_success(f"Distribuição pronta em: {dist_folder}")
    return True

# =============================================================================
# MODOS DE BUILD
# =============================================================================

def build_onefolder() -> bool:
    """Build modo OneFolder (padrão)"""
    print_header("PALANTIR LINUX - BUILD ONEFOLDER")

    total_steps = 5
    step = 1

    # 1. Verificar Python
    print_step(step, total_steps, "Verificando Python...")
    if not check_python():
        return False
    step += 1

    # 2. Instalar dependências
    print_step(step, total_steps, "Instalando dependências...")
    if not install_dependencies(PACKAGES_BASE + PACKAGES_EXTRAS):
        return False
    step += 1

    # 3. Verificar executáveis
    print_step(step, total_steps, "Verificando executáveis...")
    aria2c, mpv, vlc = check_executables()
    step += 1

    # 4. Executar PyInstaller
    print_step(step, total_steps, "Executando PyInstaller...")
    if not run_pyinstaller():
        return False
    step += 1

    # 5. Copiar Players
    print_step(step, total_steps, "Copiando Players...")
    dist_folder = DIST_DIR / "Palantir"
    copy_players_to_dist(dist_folder)

    if not create_dist_folder(dist_folder):
        return False

    # Resumo
    print_header("BUILD CONCLUÍDO!")
    print_info(f"Pasta de distribuição: {dist_folder}")
    print()
    print("  Estrutura:")
    print("  Palantir/")
    print("  ├── Palantir              # Executável principal")
    print("  ├── Players/")
    print("  │   ├── mpv.AppImage      # Player MPV")
    print("  │   └── VLC.AppImage      # Player VLC")
    print("  └── (bibliotecas em _internal/)")
    print()
    print("  Para usar:")
    print(f"  1. cd {dist_folder}")
    print("  2. ./Palantir")
    print()
    print("  Para distribuir:")
    print("  1. Copie toda a pasta 'Palantir'")
    print("  2. Ou compacte: tar -czvf Palantir-Linux.tar.gz -C dist Palantir")

    if not mpv or not vlc:
        print()
        print_warning("ATENÇÃO: Alguns players não foram encontrados!")
        print_info("Adicione os arquivos na pasta Players/ antes de distribuir.")

    return True

def build_appimage() -> bool:
    """Build modo AppImage + TAR.GZ"""
    print_header("PALANTIR LINUX - BUILD APPIMAGE")

    total_steps = 7
    step = 1

    # 1. Verificar Python
    print_step(step, total_steps, "Verificando Python...")
    if not check_python():
        return False
    step += 1

    # 2. Instalar dependências
    print_step(step, total_steps, "Instalando dependências...")
    if not install_dependencies(PACKAGES_BASE + PACKAGES_EXTRAS):
        return False
    step += 1

    # 3. Verificar FUSE
    print_step(step, total_steps, "Verificando FUSE...")
    fuse_installed = False
    try:
        result = subprocess.run(['ldconfig', '-p'], capture_output=True, text=True)
        if 'libfuse.so.2' in result.stdout or 'libfuse.so' in result.stdout:
            fuse_installed = True
            print_success("FUSE instalado")
    except:
        pass

    if not fuse_installed and not is_wsl():
        print_warning("FUSE não encontrado")
        print_info("Para criar AppImage, instale:")
        print_info("  - Ubuntu/Debian: sudo apt install libfuse2")
        print_info("  - Fedora: sudo dnf install fuse")
        print_info("  - Arch: sudo pacman -S fuse2")
    step += 1

    # 4. Verificar executáveis
    print_step(step, total_steps, "Verificando executáveis...")
    aria2c, mpv, vlc = check_executables()
    step += 1

    # 5. Executar PyInstaller
    print_step(step, total_steps, "Executando PyInstaller...")
    if not run_pyinstaller():
        return False
    step += 1

    # 6. Copiar Players
    print_step(step, total_steps, "Copiando Players...")
    dist_folder = DIST_DIR / "Palantir"
    copy_players_to_dist(dist_folder)
    step += 1

    # 7. Criar AppDir e AppImage
    print_step(step, total_steps, "Criando AppDir/AppImage...")

    if not create_appdir(dist_folder, aria2c):
        return False

    # Tenta criar AppImage (se não for WSL)
    appimage_output = None
    if not is_wsl() and fuse_installed:
        appimage_output = create_appimage()

    # Cria TAR.GZ como fallback ou alternativa
    tarball_output = create_tarball()

    # Resumo
    print_header("BUILD CONCLUÍDO!")

    if appimage_output and appimage_output.exists():
        size_mb = appimage_output.stat().st_size / (1024 * 1024)
        print_success(f"AppImage criado: {appimage_output.name} ({size_mb:.1f} MB)")
        print()
        print("  Para usar:")
        print(f"  1. chmod +x {appimage_output.name}")
        print(f"  2. ./{appimage_output.name}")
        print()
        print("  Para distribuir:")
        print(f"  Copie {appimage_output.name} (funciona em qualquer distro)")

    if tarball_output.exists():
        size_mb = tarball_output.stat().st_size / (1024 * 1024)
        print_success(f"TAR.GZ criado: {tarball_output.name} ({size_mb:.1f} MB)")
        print()
        print("  Para usar:")
        print(f"  1. tar -xzf {tarball_output.name}")
        print("  2. cd Palantir && ./AppRun")

    if not mpv or not vlc:
        print()
        print_warning("ATENÇÃO: Alguns players não foram encontrados!")
        print_info("Adicione os arquivos na pasta Players/ antes de distribuir.")

    return True

def build_all() -> bool:
    """Executa todos os modos de build"""
    print_header("PALANTIR LINUX - BUILD COMPLETO")
    print_info("Este script irá gerar:")
    print("  1. OneFolder (dist/Palantir/)")
    print("  2. AppImage (Palantir-x86_64.AppImage)")
    print("  3. TAR.GZ (Palantir-Linux-x86_64.tar.gz)")
    print()

    response = input("Continuar? [s/N]: ").strip().lower()
    if response not in ['s', 'sim', 'y', 'yes']:
        print_info("Build cancelado")
        return False

    # Build OneFolder
    print_header("ETAPA 1: BUILD ONEFOLDER")
    if not build_onefolder():
        print_error("Build OneFolder falhou!")
        return False

    # Build AppImage
    print_header("ETAPA 2: BUILD APPIMAGE")
    if not build_appimage():
        print_error("Build AppImage falhou!")
        return False

    print_header("BUILD COMPLETO CONCLUÍDO!")
    print_success("Todos os pacotes foram gerados com sucesso!")
    print()
    print("  Arquivos gerados:")
    print(f"  1. {DIST_DIR / 'Palantir'} (OneFolder)")
    print(f"  2. {PROJECT_DIR / 'Palantir-x86_64.AppImage'} (AppImage)")
    print(f"  3. {PROJECT_DIR / 'Palantir-Linux-x86_64.tar.gz'} (TAR.GZ)")

    return True

# =============================================================================
# MAIN
# =============================================================================

def main():
    """Função principal"""
    os.chdir(PROJECT_DIR)

    # Parse de argumentos
    mode = "all"  # padrão: build all

    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["onefolder", "1", "one"]:
            mode = "onefolder"
        elif arg in ["appimage", "2", "app"]:
            mode = "appimage"
        elif arg in ["all", "a", "complete"]:
            mode = "all"
        elif arg in ["help", "h", "-h", "--help"]:
            print("Build Unificado do Palantir Linux")
            print()
            print("Uso: python build_linux_unified.py [modo]")
            print()
            print("Modos disponíveis:")
            print("  onefolder, 1  - Gera apenas pasta dist/Palantir/")
            print("  appimage, 2   - Gera AppImage + TAR.GZ")
            print("  all, a        - Gera todos os formatos (padrão)")
            print("  help, h       - Mostra esta ajuda")
            print()
            return 0
        else:
            print_error(f"Argumento desconhecido: {arg}")
            print_info("Use 'python build_linux_unified.py help' para ajuda")
            return 1

    # Executa build no modo selecionado
    try:
        if mode == "onefolder":
            success = build_onefolder()
        elif mode == "appimage":
            success = build_appimage()
        else:  # all
            success = build_all()

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n\nBuild cancelado pelo usuário")
        return 1
    except Exception as e:
        print_error(f"Erro: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
