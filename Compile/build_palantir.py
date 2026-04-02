#!/usr/bin/env python3
"""
Script de compilação para Palantir - Windows/Linux
Gera um executável standalone com todas as dependências, players e configuracoes
"""

import os
import sys
import subprocess
import shutil
import time
from pathlib import Path

# Cores para output no console
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}→ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def check_python():
    """Verifica se Python está instalado e na versão correta"""
    print_header("Verificando Python")

    python_version = sys.version_info
    if python_version.major < 3 or python_version.minor < 8:
        print_error("Python 3.8 ou superior é necessário")
        return False

    print_success(f"Python {python_version.major}.{python_version.minor}.{python_version.micro} detectado")
    return True

def install_dependencies():
    """Instala todas as dependências necessárias"""
    print_header("Instalando Dependências")

    requirements = [
        "requests>=2.25.1",
        "aria2p>=0.12.1",
        "Pillow>=8.0.0",
        "customtkinter>=5.2.0",
        "unidecode",
        "ttkthemes",
        "psutil",
        "pyinstaller>=5.0",
        "urllib3"
    ]

    print_info("Instalando/atualizando pacotes Python...")

    for package in requirements:
        try:
            print_info(f"Instalando {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--upgrade", "--quiet"])
            print_success(f"{package} instalado")
        except subprocess.CalledProcessError as e:
            print_error(f"Falha ao instalar {package}: {e}")
            return False

    print_success("Todas as dependências instaladas")
    return True

def check_executables():
    """Verifica se os executáveis necessários estão presentes"""
    print_header("Verificando Executáveis")

    # Usa a pasta raiz do projeto (pai da pasta Compile)
    script_dir = Path(__file__).parent.absolute()
    project_dir = script_dir.parent

    executables = {
        "aria2c.exe": project_dir / "aria2c.exe",
        "Players/mpv/mpv.exe": project_dir / "Players" / "mpv" / "mpv.exe",
        "Players/VLCPortable/VLCPortable.exe": project_dir / "Players" / "VLCPortable" / "VLCPortable.exe"
    }

    all_present = True

    for name, path in executables.items():
        if path.exists():
            print_success(f"{name} encontrado")
        else:
            print_error(f"{name} não encontrado em: {path}")
            all_present = False

    if not all_present:
        print_warning("\nAlguns executáveis não foram encontrados.")
        print_info("O build continuará, mas você precisará adicionar os executáveis faltantes manualmente.")
        print_info("Dica: Coloque os players na pasta Players/ na raiz do projeto")

    return all_present

def create_onefolder_build():
    """Cria build no formato onefolder (pasta com todos os arquivos)"""
    print_header("Criando Build OneFolder")

    # Usa a pasta raiz do projeto (pai da pasta Compile)
    script_dir = Path(__file__).parent.absolute()
    project_dir = script_dir.parent
    dist_dir = project_dir / "dist" / "Palantir"

    # Limpeza prévia
    if dist_dir.exists():
        print_info("Limpando pasta dist/Palantir existente...")
        try:
            subprocess.run(['taskkill', '/F', '/IM', 'mpv.exe'],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['taskkill', '/F', '/IM', 'vlc.exe'],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)
            shutil.rmtree(dist_dir, ignore_errors=True)
        except Exception as e:
            print_warning(f"Não foi possível limpar completamente: {e}")
            print_info("O PyInstaller tentará limpar durante o build")

    # Determina o separador de paths baseado no sistema operacional
    sep = ";" if sys.platform == "win32" else ":"

    # Comando PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=Palantir",
        "--console",
        f"--icon={project_dir / 'Palantir.ico'}",
        f"--add-data={project_dir / 'advanced_downloader.py'}{sep}.",
        f"--add-data={project_dir / 'organize_folders.py'}{sep}.",
        f"--add-data={project_dir / 'organize_folders_wrapper.py'}{sep}.",
        f"--add-data={project_dir / 'categorias.py'}{sep}.",
        f"--add-data={project_dir / 'downloads.db'}{sep}.",
        f"--add-data={project_dir / 'config.json'}{sep}.",
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
        "--runtime-tmpdir=.",
    ]

    # Adiciona aria2c.exe se existir
    if (project_dir / "aria2c.exe").exists():
        cmd.append(f"--add-data={project_dir / 'aria2c.exe'}{sep}.")
        print_info("Incluindo aria2c.exe")

    # Adiciona Players/ se existir
    if (project_dir / "Players" / "mpv" / "mpv.exe").exists():
        cmd.append(f"--add-data={project_dir / 'Players' / 'mpv' / 'mpv.exe'}{sep}Players/mpv")
        print_info("Incluindo mpv.exe")

    if (project_dir / "Players" / "VLCPortable" / "VLCPortable.exe").exists():
        cmd.append(f"--add-data={project_dir / 'Players' / 'VLCPortable' / 'VLCPortable.exe'}{sep}Players/VLCPortable")
        print_info("Incluindo VLCPortable.exe")

    # Script principal (Palantir-windows.py na raiz)
    cmd.append(str(project_dir / "Palantir-windows.py"))

    print_info("Executando PyInstaller...")
    print_info(f"Comando: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True, cwd=project_dir)
        print_success("Build OneFolder concluído com sucesso!")

        # Copiar aria2c.exe para a distribuição
        if (project_dir / "aria2c.exe").exists():
            print_info("Copiando aria2c.exe para distribuição...")
            shutil.copy2(project_dir / "aria2c.exe", dist_dir / "aria2c.exe")

        # Copiar Players/ para a distribuição
        if (project_dir / "Players").exists():
            print_info("Copiando Players/ para distribuição...")
            shutil.copytree(project_dir / "Players", dist_dir / "Players", dirs_exist_ok=True)

        print_info(f"Distribua a pasta: {dist_dir}")
        print_info(f"Estrutura: {dist_dir}")
        print_info("  ├── Palantir.exe")
        print_info("  ├── aria2c.exe")
        print_info("  ├── Players/")
        print_info("  │   ├── mpv/mpv.exe")
        print_info("  │   └── VLCPortable/VLCPortable.exe")
        print_info("  └── [bibliotecas em _internal/]")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Erro no build: {e}")
        return False

def create_onefile_build():
    """Cria build no formato onefile (único executável)"""
    print_header("Criando Build OneFile (Executável Único)")

    script_dir = Path(__file__).parent.absolute()
    project_dir = script_dir.parent

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=Palantir",
        "--onefile",
        "--console",
        f"--icon={project_dir / 'Palantir.ico'}",
        "--hidden-import=customtkinter",
        "--hidden-import=ttkthemes",
        "--hidden-import=aria2p",
        "--hidden-import=unidecode",
        "--hidden-import=PIL",
        "--hidden-import=requests",
        "--hidden-import=urllib3",
        "--hidden-import=sqlite3",
        "--collect-all=customtkinter",
        "--collect-all=ttkthemes",
        "--clean",
        "--noconfirm",
        "--runtime-tmpdir=.",
    ]

    if (project_dir / "aria2c.exe").exists():
        cmd.append(f"--add-data={project_dir / 'aria2c.exe'};.")

    if (project_dir / "Players" / "mpv" / "mpv.exe").exists():
        cmd.append(f"--add-data={project_dir / 'Players' / 'mpv' / 'mpv.exe'};Players/mpv")

    if (project_dir / "Players" / "VLCPortable" / "VLCPortable.exe").exists():
        cmd.append(f"--add-data={project_dir / 'Players' / 'VLCPortable' / 'VLCPortable.exe'};Players/VLCPortable")

    cmd.append(str(project_dir / "Palantir-windows.py"))

    print_info("Executando PyInstaller (OneFile)...")

    try:
        subprocess.run(cmd, check=True, cwd=project_dir)
        print_success("Build OneFile concluído com sucesso!")
        print_info(f"Executável único: {project_dir / 'dist' / 'Palantir.exe'}")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Erro no build OneFile: {e}")
        return False

def create_distribution_folder():
    """Cria uma pasta de distribuição completa com Players/ e aria2c.exe"""
    print_header("Criando Pasta de Distribuição")

    script_dir = Path(__file__).parent.absolute()
    project_dir = script_dir.parent
    dist_dir = project_dir / "dist" / "Palantir"
    publish_dir = project_dir / "publish"

    if not dist_dir.exists():
        print_error("Pasta dist/Palantir não encontrada. Execute o build primeiro!")
        return False

    # Copiar aria2c.exe se existir
    if (project_dir / "aria2c.exe").exists():
        print_info("Copiando aria2c.exe para distribuição...")
        shutil.copy2(project_dir / "aria2c.exe", dist_dir / "aria2c.exe")
        print_success("aria2c.exe copiado com sucesso!")

    # Copiar pasta Players/ se existir
    if (project_dir / "Players").exists():
        print_info("Copiando pasta Players/ para distribuição...")
        shutil.copytree(project_dir / "Players", dist_dir / "Players", dirs_exist_ok=True)
        print_success("Players/ copiada com sucesso!")

    # Cria pasta publish
    if publish_dir.exists():
        shutil.rmtree(publish_dir)

    shutil.copytree(dist_dir, publish_dir, dirs_exist_ok=True)

    print_success(f"Pasta de distribuição criada: {publish_dir}")
    print_info("Esta pasta contém tudo necessário para rodar o Palantir")
    return True

def cleanup():
    """Limpa arquivos temporários de build"""
    print_header("Limpando Arquivos Temporários")

    script_dir = Path(__file__).parent.absolute()
    project_dir = script_dir.parent

    folders_to_remove = ["build", "__pycache__"]

    for folder in folders_to_remove:
        path = project_dir / folder
        if path.exists():
            try:
                shutil.rmtree(path)
                print_success(f"Removido: {folder}")
            except Exception as e:
                print_warning(f"Não foi possível remover {folder}: {e}")

    # Remove arquivo .spec se existir
    spec_file = project_dir / "Palantir.spec"
    if spec_file.exists():
        try:
            spec_file.unlink()
            print_success("Removido: Palantir.spec")
        except Exception as e:
            print_warning(f"Não foi possível remover Palantir.spec: {e}")

def main():
    """Função principal"""
    print_header("Palantir Build Tool")
    print_info("Este script irá compilar o Palantir com TODAS as dependências")
    print_info("Incluindo: aria2c.exe, Players/, ícone, e todos os módulos")

    script_dir = Path(__file__).parent.absolute()
    project_dir = script_dir.parent
    os.chdir(project_dir)

    print("\n" + "="*60)
    print("Opções de Build:")
    print("="*60)
    print("1. Build OneFolder (Recomendado - mais rápido para iniciar)")
    print("2. Build OneFile (Executável único - menor tamanho)")
    print("3. Build Completo (OneFolder + Pasta de Distribuição)")
    print("4. Apenas instalar dependências")
    print("5. Limpar arquivos de build")
    print("6. Sair")
    print("="*60)

    while True:
        choice = input("\nEscolha uma opção (1-6): ").strip()

        if choice == "1":
            if not check_python():
                continue
            if not install_dependencies():
                continue
            check_executables()
            create_onefolder_build()

        elif choice == "2":
            if not check_python():
                continue
            if not install_dependencies():
                continue
            check_executables()
            create_onefile_build()

        elif choice == "3":
            if not check_python():
                continue
            if not install_dependencies():
                continue
            check_executables()
            if create_onefolder_build():
                create_distribution_folder()

        elif choice == "4":
            if not check_python():
                continue
            install_dependencies()

        elif choice == "5":
            cleanup()

        elif choice == "6":
            print_info("Saindo...")
            break

        else:
            print_warning("Opção inválida. Escolha 1-6.")

        print("\n" + "="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_warning("\nBuild cancelado pelo usuário")
        sys.exit(1)
    except Exception as e:
        print_error(f"Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
