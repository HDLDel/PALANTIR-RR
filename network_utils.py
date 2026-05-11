import requests
import subprocess
import time
import sys
import os
from typing import Tuple


def get_base_dir():
    """Obtém o diretório base, funcionando tanto para script quanto para executável PyInstaller"""
    if getattr(sys, 'frozen', False):
        # Modo executável compilado
        return os.path.dirname(sys.executable)
    else:
        # Modo script normal
        return os.path.dirname(os.path.abspath(__file__))


class NetworkUtils:
    """Utilitários de rede para o Palantir"""

    @staticmethod
    def test_api_connection(api_key: str = "<PLACEHOLDER>") -> bool:
        """Testa a conexão com a API do TMDB"""
        try:
            url = f"https://api.themoviedb.org/3/movie/550?api_key={api_key}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print("✅ Conexão com API do TMDB OK")
                return True
            else:
                print(f"⚠️ API do TMDB retornou status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro ao conectar com API do TMDB: {e}")
            return False

    @staticmethod
    def start_aria2c() -> bool:
        """Inicia o servidor aria2c"""
        try:
            base_dir = get_base_dir()

            # Busca aria2c dependendo da plataforma
            aria2c_path = None
            if sys.platform == "win32":
                # Windows: procura aria2c.exe
                for candidate in [
                    os.path.join(base_dir, 'aria2c.exe'),
                    os.path.join(base_dir, 'aria2c', 'aria2c.exe'),
                ]:
                    if os.path.exists(candidate):
                        aria2c_path = candidate
                        break
            else:
                # Linux: ignora o executável da pasta, usa sempre o do PATH
                aria2c_path = 'aria2c'

            if not aria2c_path:
                aria2c_path = 'aria2c'  # Fallback para PATH do sistema

            if sys.platform == "win32":
                subprocess.Popen(
                    [aria2c_path, "--enable-rpc", "--rpc-listen-all=true"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                subprocess.Popen(
                    ["nohup", aria2c_path, "--enable-rpc", "--rpc-listen-all=true"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setpgrp
                )
            time.sleep(2)
            return True
        except FileNotFoundError:
            print("aria2c não encontrado. Por favor, instale o aria2 primeiro.")
            return False
        except Exception as e:
            print(f"Erro ao iniciar aria2c: {e}")
            return False

    @staticmethod
    def check_dependency(dependency: str) -> bool:
        """Verifica se uma dependência está instalada"""
        try:
            subprocess.run([dependency, '--version'],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            return False

    @staticmethod
    def check_dependencies() -> Tuple[bool, list]:
        """Verifica se todas as dependências necessárias estão instaladas"""
        missing_deps = []

        # Verifica aria2
        if not NetworkUtils.check_dependency('aria2c'):
            missing_deps.append("aria2")

        # Verifica MPV (tenta diferentes nomes)
        mpv_found = False
        for mpv_name in ['mpv', 'mpv.exe']:
            if NetworkUtils.check_dependency(mpv_name):
                mpv_found = True
                break

        if not mpv_found:
            missing_deps.append("mpv")

        return len(missing_deps) == 0, missing_deps

# Teste básico da classe
if __name__ == "__main__":
    # Teste de conexão com API
    api_success = NetworkUtils.test_api_connection()
    print(f"API Connection: {api_success}")

    # Teste de dependências
    deps_ok, missing = NetworkUtils.check_dependencies()
    print(f"Dependencies OK: {deps_ok}")
    if missing:
        print(f"Missing: {missing}")

    # Teste de inicialização do aria2 (apenas se estiver disponível)
    if deps_ok:
        aria2_success = NetworkUtils.start_aria2c()
        print(f"aria2c started: {aria2_success}")
