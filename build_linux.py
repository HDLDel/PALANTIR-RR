#!/usr/bin/env python3
"""
Build automatizado do Palantir Linux
Gera pacote com binário + pasta Players/ integrada
Formato: dist/Palantir/ com todos os arquivos necessários
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# =============================================================================
# CONFIGURAÇÕES DE DIRETÓRIO (Inteligente)
# =============================================================================
SCRIPT_DIR = Path(__file__).parent.absolute()
if (SCRIPT_DIR / "Palantir-windows.py").exists() or (SCRIPT_DIR / "Palantir-Linux.py").exists():
    PROJECT_DIR = SCRIPT_DIR
else:
    PROJECT_DIR = SCRIPT_DIR.parent

def main():
    project_dir = PROJECT_DIR
    os.chdir(project_dir)

    print("=" * 60)
    print("        PALANTIR LINUX - BUILD AUTOMATIZADO")
    print("=" * 60)
    print()

    # 1. Verificar Python
    print("[1/5] Verificando Python...")
    print(f"      Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    # 2. Instalar dependências
    print("\n[2/5] Instalando dependências...")
    packages = [
        "requests", "aria2p", "Pillow", "customtkinter",
        "unidecode", "ttkthemes", "psutil", "pyinstaller", "urllib3"
    ]

    for pkg in packages:
        print(f"      Instalando {pkg}...")
        subprocess.run([sys.executable, "-m", "pip", "install", pkg, "--upgrade", "-q"],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("      Dependências instaladas!")

    # 3. Verificar executáveis
    print("\n[3/5] Verificando executáveis...")

    # Verifica múltiplos caminhos possíveis para cada executável (na raiz do projeto)
    aria2c_paths = [
        project_dir / "aria2c",              # Raiz (aria2c binário)
        project_dir / "aria2c" / "aria2c",   # Pasta aria2c/
    ]

    mpv_paths = [
        project_dir / "Players" / "mpv" / "mpv",
        project_dir / "Players" / "mpv.AppImage",
        project_dir / "Players" / "mpv" / "mpv.AppImage",
    ]

    vlc_paths = [
        project_dir / "Players" / "VLCPortable" / "VLCPortable",
        project_dir / "Players" / "VLC.AppImage",
        project_dir / "Players" / "VLCPortable" / "VLC.AppImage",
    ]

    executables_found = []

    # Verifica aria2c
    aria2c_found = None
    for path in aria2c_paths:
        if path.exists():
            aria2c_found = path
            print(f"      [OK] aria2c: {path.relative_to(project_dir)}")
            break
    if not aria2c_found:
        print(f"      [ ] aria2c - não encontrado")
        print(f"          Instale: sudo apt install aria2")

    # Verifica mpv
    mpv_found = None
    for path in mpv_paths:
        if path.exists():
            mpv_found = path
            print(f"      [OK] mpv: {path.relative_to(project_dir)}")
            break
    if not mpv_found:
        print(f"      [ ] mpv - não encontrado na pasta Players/")
        print(f"          Coloque mpv ou mpv.AppImage em Players/")

    # Verifica vlc
    vlc_found = None
    for path in vlc_paths:
        if path.exists():
            vlc_found = path
            print(f"      [OK] vlc: {path.relative_to(project_dir)}")
            break
    if not vlc_found:
        print(f"      [ ] vlc - não encontrado na pasta Players/")
        print(f"          Coloque VLC.AppImage ou VLCPortable em Players/")

    # 4. Executar PyInstaller (OneFolder)
    print("\n[4/5] Executando PyInstaller (OneFolder)...")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=Palantir",
        "--console",
        f"--icon={project_dir / 'palantir.png'}",
        f"--add-data={project_dir / 'advanced_downloader.py'}:.",
        f"--add-data={project_dir / 'organize_folders.py'}:.",
        f"--add-data={project_dir / 'organize_folders_wrapper.py'}:.",
        f"--add-data={project_dir / 'categorias.py'}:.",
        f"--add-data={project_dir / 'downloads.db'}:.",
        f"--add-data={project_dir / 'config.json'}:.",
        f"--add-data={project_dir / 'palantir.png'}:.",
        "--hidden-import=customtkinter",
        "--hidden-import=ttkthemes",
        "--hidden-import=aria2p",
        "--hidden-import=unidecode",
        "--hidden-import=PIL",
        "--hidden-import=requests",
        "--hidden-import=urllib3",
        "--hidden-import=sqlite3",
        "--hidden-import=logging",
        "--hidden-import=datetime",
        "--hidden-import=concurrent.futures",
        "--collect-all=customtkinter",
        "--collect-all=ttkthemes",
        "--clean",
        "--noconfirm",
    ]

    # Adicionar aria2c se existir
    if aria2c_found:
        cmd.append(f"--add-data={aria2c_found}:.")

    # Adiciona o script principal (Palantir-Linux.py na raiz)
    cmd.append(str(project_dir / "Palantir-Linux.py"))

    print("      Compilando...")
    result = subprocess.run(cmd, cwd=project_dir)

    if result.returncode == 0:
        print("      Build concluído com sucesso!")
    else:
        print("      Erro no build!")
        return 1

    # 5. Copiar pasta Players/ para a raiz da distribuição
    print("\n[5/5] Copiando pasta Players/ para distribuição...")

    dist_folder = project_dir / "dist" / "Palantir"
    players_root = dist_folder / "Players"

    # Remove Players/ se existir em _internal (evita duplicação)
    players_internal = dist_folder / "_internal" / "Players"
    if players_internal.exists():
        shutil.rmtree(players_internal)
        print(f"      Removida Players/ duplicada em _internal/")

    # Copia da pasta original do projeto
    players_source = project_dir / "Players"
    if players_source.exists():
        if players_root.exists():
            shutil.rmtree(players_root)
        shutil.copytree(players_source, players_root)
        print(f"      Players/ copiada para a raiz da distribuição")
    else:
        print("      Players/ não encontrada no projeto")

    # Resumo
    print()
    print("=" * 60)

    if dist_folder.exists():
        print(f"  BUILD CONCLUÍDO!")
        print(f"  Pasta de distribuição: {dist_folder}")
        print()
        print("  Estrutura gerada:")
        print("  Palantir/")
        print("  ├── Palantir              # Executável principal")
        print("  ├── Players/")
        print("  │   ├── mpv.AppImage      # Player MPV")
        print("  │   └── VLC.AppImage      # Player VLC")
        print("  └── (outras bibliotecas)")
        print()
        print("  Para usar o Palantir:")
        print(f"  1. Navegue até: {dist_folder}")
        print("  2. Execute: ./Palantir")
        print()
        print("  Para distribuir:")
        print("  1. Copie toda a pasta 'Palantir'")
        print("  2. Compacte em TAR.GZ se necessário:")
        print(f"     tar -czvf Palantir-Linux.tar.gz -C {dist_folder.parent} Palantir")
        print("  3. Distribua para outros usuários")

        # Aviso sobre players faltantes
        if not mpv_found or not vlc_found:
            print()
            print("  ⚠️  ATENÇÃO: Alguns players não foram encontrados!")
            print("      Adicione os arquivos na pasta Players/ antes de distribuir.")
    else:
        print("  ERRO: Pasta de distribuição não encontrada!")

    print("=" * 60)
    print()

    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nBuild cancelado pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\nErro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
