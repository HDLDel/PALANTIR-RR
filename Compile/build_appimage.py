#!/usr/bin/env python3
"""
Build automatizado do Palantir Linux - Formato AppImage
Gera AppImage único com todas as dependências, players e configurações
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)

    print("=" * 60)
    print("        PALANTIR LINUX - BUILD APPIMAGE")
    print("=" * 60)
    print()

    # 1. Verificar Python
    print("[1/7] Verificando Python...")
    print(f"      Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    # 2. Instalar dependências
    print("\n[2/7] Instalando dependências...")
    packages = [
        "requests", "aria2p", "Pillow", "customtkinter",
        "unidecode", "ttkthemes", "psutil", "pyinstaller", "urllib3",
        "websocket-client", "loguru", "platformdirs", "colorama"
    ]

    for pkg in packages:
        print(f"      Instalando {pkg}...")
        subprocess.run([sys.executable, "-m", "pip", "install", pkg, "--upgrade", "-q"],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("      Dependências instaladas!")

    # 3. Verificar/Instalar FUSE e ferramentas do AppImage
    print("\n[3/7] Verificando FUSE e ferramentas do AppImage...")
    
    # Verificar/Instalar FUSE
    fuse_installed = False
    try:
        subprocess.run(['ldconfig', '-p'], capture_output=True, text=True)
        result = subprocess.run(['ldconfig', '-p'], capture_output=True, text=True)
        if 'libfuse.so.2' in result.stdout or 'libfuse.so' in result.stdout:
            fuse_installed = True
            print("      [OK] FUSE já está instalado")
    except:
        pass
    
    if not fuse_installed:
        print("      [!] FUSE não encontrado")
        print("          Instalando FUSE...")
        
        # Detectar distribuição e instalar
        try:
            with open('/etc/os-release', 'r') as f:
                os_info = f.read()
            
            if 'fedora' in os_info.lower() or 'dnf' in os_info.lower():
                # Fedora
                print("      Detectado Fedora - Instalando via dnf...")
                subprocess.run(['sudo', 'dnf', 'install', '-y', 'fuse', 'libfuse2'],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif 'ubuntu' in os_info.lower() or 'debian' in os_info.lower() or 'apt' in os_info.lower():
                # Ubuntu/Debian
                print("      Detectado Ubuntu/Debian - Instalando via apt...")
                subprocess.run(['sudo', 'apt', 'update', '-qq'],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(['sudo', 'apt', 'install', '-y', 'libfuse2'],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif 'arch' in os_info.lower() or 'pacman' in os_info.lower():
                # Arch Linux
                print("      Detectado Arch - Instalando via pacman...")
                subprocess.run(['sudo', 'pacman', '-S', '--noconfirm', 'fuse2'],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif 'opensuse' in os_info.lower() or 'zypper' in os_info.lower():
                # openSUSE
                print("      Detectado openSUSE - Instalando via zypper...")
                subprocess.run(['sudo', 'zypper', 'install', '-y', 'fuse'],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                print("      [!] Distribuição não detectada automaticamente")
                print("          Instale manualmente:")
                print("          - Ubuntu/Debian: sudo apt install libfuse2")
                print("          - Fedora: sudo dnf install fuse")
                print("          - Arch: sudo pacman -S fuse2")
        except Exception as e:
            print(f"      [!] Falha ao instalar FUSE: {e}")
            print("          Instale manualmente para criar AppImage")
    
    # Verificar appimagetool
    appimagetool_path = script_dir / "appimagetool"
    if not appimagetool_path.exists():
        print("      [!] appimagetool não encontrado")
        print("          Baixando appimagetool...")
        try:
            import urllib.request
            url = "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
            urllib.request.urlretrieve(url, appimagetool_path)
            os.chmod(appimagetool_path, 0o755)
            print("      [OK] appimagetool baixado")
        except Exception as e:
            print(f"      [ERRO] Falha ao baixar appimagetool: {e}")
            print("          Baixe manualmente de: https://github.com/AppImage/AppImageKit/releases")
    else:
        print("      [OK] appimagetool encontrado")

    # 4. Verificar executáveis
    print("\n[4/7] Verificando executáveis...")

    # Verifica múltiplos caminhos possíveis para cada executável
    aria2c_paths = [
        script_dir / "aria2c",              # Raiz (aria2c binário)
        script_dir / "aria2c" / "aria2c",   # Pasta aria2c/
    ]

    mpv_paths = [
        script_dir / "Players" / "mpv" / "mpv",
        script_dir / "Players" / "mpv.AppImage",
        script_dir / "Players" / "mpv" / "mpv.AppImage",
    ]

    vlc_paths = [
        script_dir / "Players" / "VLCPortable" / "VLCPortable",
        script_dir / "Players" / "VLC.AppImage",
        script_dir / "Players" / "VLCPortable" / "VLC.AppImage",
    ]

    # Verifica aria2c
    aria2c_found = None
    for path in aria2c_paths:
        if path.exists():
            aria2c_found = path
            print(f"      [OK] aria2c: {path.relative_to(script_dir)}")
            break
    if not aria2c_found:
        print(f"      [ ] aria2c - não encontrado")
        print(f"          Instale: sudo apt install aria2")

    # Verifica mpv
    mpv_found = None
    for path in mpv_paths:
        if path.exists():
            mpv_found = path
            print(f"      [OK] mpv: {path.relative_to(script_dir)}")
            break
    if not mpv_found:
        print(f"      [ ] mpv - não encontrado na pasta Players/")
        print(f"          Coloque mpv ou mpv.AppImage em Players/")

    # Verifica vlc
    vlc_found = None
    for path in vlc_paths:
        if path.exists():
            vlc_found = path
            print(f"      [OK] vlc: {path.relative_to(script_dir)}")
            break
    if not vlc_found:
        print(f"      [ ] vlc - não encontrado na pasta Players/")
        print(f"          Coloque VLC.AppImage ou VLCPortable em Players/")

    # 5. Executar PyInstaller (OneFolder)
    print("\n[5/7] Executando PyInstaller (OneFolder)...")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=Palantir",
        "--console",
        "--icon=palantir.png",
        "--add-data=advanced_downloader.py:.",
        "--add-data=organize_folders.py:.",
        "--add-data=organize_folders_wrapper.py:.",
        "--add-data=categorias.py:.",
        "--add-data=downloads.db:.",
        "--add-data=config.json:.",
        "--add-data=palantir.png:.",
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

    # Adicionar mpv se existir (sempre dentro de Players/)
    if mpv_found:
        if "Players/mpv" in str(mpv_found).replace("\\", "/"):
            cmd.append(f"--add-data={mpv_found}:Players/mpv")
        elif "Players" in str(mpv_found):
            cmd.append(f"--add-data={mpv_found}:Players")

    # Adicionar vlc se existir (sempre dentro de Players/)
    if vlc_found:
        if "Players/VLCPortable" in str(vlc_found).replace("\\", "/"):
            cmd.append(f"--add-data={vlc_found}:Players/VLCPortable")
        elif "Players" in str(vlc_found):
            cmd.append(f"--add-data={vlc_found}:Players")

    cmd.append("Palantir-Linux.py")

    print("      Compilando...")
    result = subprocess.run(cmd, cwd=script_dir)

    if result.returncode == 0:
        print("      Build PyInstaller concluído com sucesso!")
    else:
        print("      Erro no build PyInstaller!")
        return 1

    # 6. Criar AppDir
    print("\n[6/7] Criando AppDir...")

    appdir = script_dir / "AppDir"
    dist_folder = script_dir / "dist" / "Palantir"

    # Limpa AppDir se existir
    if appdir.exists():
        shutil.rmtree(appdir)

    # Cria estrutura do AppDir
    appdir.mkdir(exist_ok=True)
    (appdir / "usr").mkdir(exist_ok=True)
    (appdir / "usr" / "bin").mkdir(exist_ok=True)
    (appdir / "usr" / "lib").mkdir(exist_ok=True)
    (appdir / "usr" / "share").mkdir(exist_ok=True)
    (appdir / "usr" / "share" / "applications").mkdir(exist_ok=True)
    (appdir / "usr" / "share" / "icons").mkdir(exist_ok=True)
    (appdir / "usr" / "share" / "icons" / "hicolor").mkdir(exist_ok=True)
    (appdir / "usr" / "share" / "icons" / "hicolor" / "256x256").mkdir(exist_ok=True)
    (appdir / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps").mkdir(exist_ok=True)

    # Copia conteúdo do dist para AppDir/usr/bin
    print("      Copiando arquivos para AppDir...")
    
    # Copia executável principal
    exe_source = dist_folder / "Palantir"
    if exe_source.exists():
        shutil.copy2(exe_source, appdir / "usr" / "bin" / "Palantir")
        print(f"      Copiado: Palantir")

    # Copia _internal (bibliotecas)
    internal_source = dist_folder / "_internal"
    if internal_source.exists():
        shutil.copytree(internal_source, appdir / "usr" / "lib" / "Palantir", dirs_exist_ok=True)
        print(f"      Copiado: _internal (bibliotecas)")

    # Copia Players
    players_source = dist_folder / "Players"
    if players_source.exists():
        shutil.copytree(players_source, appdir / "usr" / "lib" / "Palantir" / "Players", dirs_exist_ok=True)
        print(f"      Copiado: Players/")

    # Copia config.json
    config_source = script_dir / "config.json"
    if config_source.exists():
        shutil.copy2(config_source, appdir / "usr" / "lib" / "Palantir" / "config.json")
        print(f"      Copiado: config.json")

    # Copia aria2c se existir
    if aria2c_found:
        shutil.copy2(aria2c_found, appdir / "usr" / "bin" / "aria2c")
        print(f"      Copiado: aria2c")

    # Cria script de lançamento (AppRun)
    print("      Criando AppRun...")
    apprun_content = '''#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${HERE}/usr/lib/Palantir:${LD_LIBRARY_PATH}"
exec "${HERE}/usr/bin/Palantir" "$@"
'''
    with open(appdir / "AppRun", "w") as f:
        f.write(apprun_content)
    os.chmod(appdir / "AppRun", 0o755)

    # Cria arquivo desktop
    print("      Criando arquivo .desktop...")
    desktop_content = '''[Desktop Entry]
Type=Application
Name=Palantir
Comment=Gerenciador e Baixador de Vídeos
Exec=Palantir
Icon=palantir
Categories=AudioVideo;Video;
'''
    with open(appdir / "usr" / "share" / "applications" / "palantir.desktop", "w") as f:
        f.write(desktop_content)
    
    # Copia ícone
    icon_source = script_dir / "palantir.png"
    if icon_source.exists():
        shutil.copy2(icon_source, appdir / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps" / "palantir.png")
        shutil.copy2(icon_source, appdir / "palantir.png")
        print(f"      Copiado: ícone")

    # Cria arquivo de informações
    print("      Criando arquivos de informação...")
    with open(appdir / "palantir.desktop", "w") as f:
        f.write(desktop_content)

    # 7. Criar AppImage ou Alternativa
    print("\n[7/7] Criando AppImage...")

    appimage_output = script_dir / "Palantir-x86_64.AppImage"
    
    # Remove AppImage antigo se existir
    if appimage_output.exists():
        appimage_output.unlink()
        print(f"      Removido AppImage antigo")

    # Define função para criar tar.gz
    def create_tarball():
        """Cria pacote tar.gz como alternativa ao AppImage"""
        print("      Criando pacote tar.gz...")
        
        tarball_output = script_dir / "Palantir-Linux-x86_64.tar.gz"
        
        import tarfile
        
        with tarfile.open(tarball_output, "w:gz") as tar:
            # Adiciona AppDir ao tarball
            tar.add(appdir, arcname="Palantir")
        
        size_mb = tarball_output.stat().st_size / (1024 * 1024)
        print(f"      Pacote criado: {tarball_output} ({size_mb:.1f} MB)")
        print(f"      Para usar: tar -xzf {tarball_output.name}")
        return tarball_output

    # Define variáveis de ambiente
    env = os.environ.copy()
    env["ARCH"] = "x86_64"

    # Verifica se está no WSL
    is_wsl = False
    try:
        with open('/proc/version', 'r') as f:
            proc_version = f.read().lower()
            if 'microsoft' in proc_version or 'wsl' in proc_version:
                is_wsl = True
                print("      [INFO] WSL detectado")
    except:
        pass

    # Tenta appimagetool apenas se NÃO for WSL
    if not is_wsl:
        # Executa appimagetool
        try:
            result = subprocess.run(
                [str(appimagetool_path), "-v", str(appdir), str(appimage_output)],
                env=env,
                cwd=script_dir
            )

            if result.returncode == 0:
                print("      AppImage criado com sucesso!")
            else:
                print(f"      Erro ao criar AppImage (código {result.returncode})")
                print("      Criando alternativa (tar.gz)...")
                create_tarball()
                
        except Exception as e:
            print(f"      Erro ao executar appimagetool: {e}")
            print("      Criando alternativa (tar.gz)...")
            create_tarball()
    else:
        # WSL: não usa appimagetool, cria tar.gz diretamente
        print("      [INFO] WSL detectado - Criando pacote tar.gz ao invés de AppImage")
        print("      (AppImages não funcionam bem no WSL)")
        create_tarball()

    # Resumo
    print()
    print("=" * 60)

    if appimage_output.exists():
        size_mb = appimage_output.stat().st_size / (1024 * 1024)
        print(f"  BUILD APPIMAGE CONCLUÍDO!")
        print(f"  Arquivo: {appimage_output}")
        print(f"  Tamanho: {size_mb:.1f} MB")
        print()
        print("  Para usar:")
        print(f"  1. Torne executável:")
        print(f"     chmod +x {appimage_output.name}")
        print()
        print(f"  2. Execute:")
        print(f"     ./{appimage_output.name}")
        print()
        print("  Para distribuir:")
        print(f"  1. Copie o arquivo {appimage_output.name}")
        print(f"  2. Distribua (funciona em qualquer distro Linux)")
    else:
        tarball_output = script_dir / "Palantir-Linux-x86_64.tar.gz"
        if tarball_output.exists():
            size_mb = tarball_output.stat().st_size / (1024 * 1024)
            print(f"  BUILD CONCLUÍDO!")
            print(f"  Arquivo: {tarball_output}")
            print(f"  Tamanho: {size_mb:.1f} MB")
            print()
            print("  Para usar:")
            print(f"  1. Extraia:")
            print(f"     tar -xzf {tarball_output.name}")
            print()
            print(f"  2. Execute:")
            print(f"     cd Palantir && ./AppRun")
            print()
            print("  Para distribuir:")
            print(f"  1. Copie o arquivo {tarball_output.name}")
            print(f"  2. Distribua (funciona em qualquer distro Linux)")
        else:
            print(f"  AppDir criado em: {appdir}")
            print()
            print("  Use o AppDir diretamente ou execute:")
            print(f"  cd {appdir} && ./AppRun")

    print()
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
