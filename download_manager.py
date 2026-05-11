"""
Módulo DownloadManager - Responsável por gerenciar downloads de vídeos
Depende do M3UHandler para obter URLs e do DatabaseManager para operações no banco
"""
import os
import sys
import re
import time
import threading
import subprocess
import sqlite3
from typing import List, Tuple, Optional, Callable
import logging
import aria2p
import requests
from tkinter import messagebox
import tkinter as tk
import unicodedata
from urllib.parse import quote
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_base_dir():
    """Obtém o diretório base, funcionando tanto para script quanto para executável PyInstaller"""
    if getattr(sys, 'frozen', False):
        # Modo executável compilado
        return os.path.dirname(sys.executable)
    else:
        # Modo script normal
        return os.path.dirname(os.path.abspath(__file__))

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DownloadManager:
    def __init__(self, database_manager=None, m3u_handler=None):
        """
        Inicializa o DownloadManager
        
        Args:
            database_manager: Instância do DatabaseManager para operações no banco
            m3u_handler: Instância do M3UHandler para obter URLs
        """
        self.database_manager = database_manager
        self.m3u_handler = m3u_handler
        self.download_queue = []
        self.is_downloading = False
        self.current_download = None
        self.cancel_download = False
        self.download_progress = tk.DoubleVar()
        self.download_progress.set(0.0)
        
        # Inicializa aria2
        self.start_aria2c()
        self.aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800))
    
    def set_database_manager(self, database_manager):
        """Define o DatabaseManager para operações no banco"""
        self.database_manager = database_manager
    
    def set_m3u_handler(self, m3u_handler):
        """Define o M3UHandler para obter URLs"""
        self.m3u_handler = m3u_handler
    
    def start_aria2c(self):
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
        except FileNotFoundError:
            logger.error("aria2c não encontrado. Por favor, instale o aria2 primeiro.")
            raise
    
    def add_to_queue(self, name: str, url: str, path: str):
        """Adiciona um item à fila de downloads"""
        self.download_queue.append((name, url, path))
        logger.info(f"Adicionado à fila: {name} - {url}")
    
    def clear_queue(self):
        """Limpa a fila de downloads"""
        self.download_queue = []
        logger.info("Fila de downloads limpa")
    
    def get_queue_size(self):
        """Retorna o tamanho da fila de downloads"""
        return len(self.download_queue)
    
    def process_download_queue(self):
        """Processa a fila de downloads"""
        if not self.download_queue:
            self.is_downloading = False
            return

        self.is_downloading = True
        name, url, path = self.download_queue.pop(0)
        threading.Thread(target=self.download_video_with_callback, args=(name, url, path)).start()

    def download_video_with_callback(self, name: str, url: str, path: str):
        """Download com callback para processar a fila"""
        try:
            self.download_video(name, url, path)
        finally:
            # Agenda o processamento da próxima fila na thread principal
            if hasattr(tk, '_default_root') and tk._default_root:
                tk._default_root.after(1000, self.process_download_queue)
            else:
                # Fallback para caso não haja interface gráfica
                time.sleep(1)
                self.process_download_queue()
    
    def sanitize_directory_name(self, name: str) -> str:
        """Remove caracteres inválidos de nomes de diretórios mantendo a estrutura do nome"""
        # Lista de caracteres inválidos no Windows
        invalid_chars = '<>:"/\\|?*'
        
        # Preserva os dois pontos se for parte de um título (ex: "Missão: Impossível")
        if ':' in name:
            parts = name.split(':')
            if len(parts) == 2 and parts[1].strip():
                name = parts[0] + ' - ' + parts[1]
        
        # Substitui cada caractere inválido por um espaço
        for char in invalid_chars:
            name = name.replace(char, ' ')
            
        # Remove espaços extras e normaliza
        name = ' '.join(name.split())
        
        # Garante que o nome não termine com ponto ou espaço
        name = name.strip('. ')
        
        return name
    
    def extract_content_info(self, name: str) -> Tuple[str, Optional[str]]:
        """Extrai informações do conteúdo (nome e temporada)"""
        match = re.search(r"(.*?)\s*(S\d{2})\s*E\d{2}", name)
        if match:
            content_name = match.group(1).strip()
            season = match.group(2).strip()
            return content_name, season
        else:
            return name, None
    
    def download_video(self, name: str, url: str, path: str, user_agent: str = None, dns_server: str = None):
        """Realiza o download do vídeo usando aria2"""
        try:
            self.cancel_download = False
            
            # Extrai o nome do conteúdo e a temporada
            content_name, season = self.extract_content_info(name)

            # Sanitiza os nomes dos diretórios
            content_name = self.sanitize_directory_name(content_name)
            if season:
                season = self.sanitize_directory_name(season)

            # Cria a pasta do conteúdo
            content_folder = os.path.join(path, content_name)
            if not os.path.exists(content_folder):
                os.makedirs(content_folder)

            # Se for uma série, cria a pasta da temporada
            if season:
                season_folder = os.path.join(content_folder, season)
                if not os.path.exists(season_folder):
                    os.makedirs(season_folder)
                file_path = os.path.join(season_folder, f"{self.sanitize_directory_name(name)}.mp4")
            else:
                file_path = os.path.join(content_folder, f"{self.sanitize_directory_name(name)}.mp4")

            # Cria diretório de logs se não existir
            log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            # Cria ou abre o arquivo de log
            log_file = os.path.join(log_dir, "aria2_downloads.log")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"Download iniciado: {name}\n")
                f.write(f"Data/Hora: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"URL: {url}\n")
                f.write(f"Destino: {file_path}\n")
                f.write(f"User-Agent: {user_agent or 'Mozilla/5.0'}\n")
                if dns_server and dns_server.strip():
                    f.write(f"DNS Server: {dns_server}\n")

            # Configuração do download com aria2
            options = {
                "dir": os.path.dirname(file_path),
                "out": os.path.basename(file_path),
                "max-connection-per-server": "16",
                "split": "16",
                "user-agent": user_agent or "Mozilla/5.0",
                "continue": "true",
                "max-concurrent-downloads": "1"
            }

            # Adiciona DNS se configurado
            if dns_server and dns_server.strip():
                options["dns-server"] = dns_server.strip()

            try:
                # Inicia o download
                download = self.aria2.add_uris([url], options=options)
                
                # Log do início do download
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"Download ID: {download.gid}\n")
                    f.write("Status: Iniciado\n")
                
                while not self.cancel_download and download.is_active:
                    try:
                        download.update()
                        downloaded = download.completed_length
                        total = download.total_length
                        
                        if total > 0:
                            progress = (downloaded / total) * 100
                            speed = download.download_speed / (1024 * 1024)  # Converte para MB/s
                            
                            # Atualiza progresso se houver callback
                            if hasattr(self, 'progress_callback'):
                                self.progress_callback(progress, speed, name)
                            
                        time.sleep(0.1)
                    except Exception as e:
                        with open(log_file, "a", encoding="utf-8") as f:
                            f.write(f"Erro durante o download: {str(e)}\n")
                        break

                if self.cancel_download:
                    download.remove(force=True)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write("Status: Cancelado pelo usuário\n")
                    return
                else:
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write("Status: Concluído com sucesso\n")
                        f.write(f"Tamanho final: {total/(1024*1024):.2f} MB\n")

            except Exception as e:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"Erro fatal no download: {str(e)}\n")
                raise

        except Exception as e:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"Erro geral: {str(e)}\n")
            logger.error(f"Erro ao baixar {name}: {e}")
            raise
        finally:
            # Reseta progresso
            self.download_progress.set(0.0)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{'='*50}\n")
    
    def cancel_current_download(self):
        """Cancela o download atual"""
        self.cancel_download = True
        logger.info("Download cancelado pelo usuário")
    
    def set_progress_callback(self, callback: Callable):
        """Define uma função de callback para atualizar o progresso"""
        self.progress_callback = callback
    
    def download_selected(self, items: List[Tuple[str, str]], download_path: str, user_agent: str = None, dns_server: str = None):
        """Inicia o download dos itens selecionados"""
        if not items:
            logger.warning("Nenhum item selecionado para download")
            return
            
        if not os.path.exists(download_path):
            logger.error("Pasta de download inválida")
            raise ValueError("Pasta de download inválida")

        # Adiciona os vídeos selecionados à fila
        for name, url in items:
            if not url:
                logger.warning(f"URL não encontrada para o vídeo: {name}")
                continue
                
            if not url.startswith(('http://', 'https://')):
                logger.warning(f"URL inválida para o vídeo: {name}\nURL: {url}")
                continue
            
            self.add_to_queue(name, url, download_path)

        # Inicia o processamento da fila se não houver download em andamento
        if not self.is_downloading and self.download_queue:
            self.process_download_queue()
    
    def retomar_downloads(self, download_path: str):
        """Retoma todos os downloads incompletos"""
        try:
            if not os.path.exists(download_path):
                logger.error("Pasta de download não encontrada")
                return

            # Lista todos os arquivos .aria2 no diretório e subdiretórios
            arquivos_aria2 = []
            
            for root, dirs, files in os.walk(download_path):
                for file in files:
                    if file.endswith('.aria2'):
                        caminho_completo = os.path.join(root, file)
                        # Verifica se o arquivo original (sem .aria2) existe
                        arquivo_original = caminho_completo[:-6]  # Remove .aria2
                        if os.path.exists(arquivo_original):
                            arquivos_aria2.append(caminho_completo)

            if not arquivos_aria2:
                logger.info("Não há downloads incompletos para retomar")
                return

            # Processa cada arquivo .aria2
            for aria2_file in arquivos_aria2:
                try:
                    # Tenta ler a URL do arquivo .aria2
                    with open(aria2_file, 'rb') as f:
                        # Pula os primeiros 16 bytes (cabeçalho)
                        f.seek(16)
                        # Lê o restante do arquivo
                        data = f.read()
                        # Procura por uma URL válida
                        text_data = data.decode('utf-8', errors='ignore')
                        
                        # Tenta diferentes padrões de URL
                        urls = []
                        # Padrão para URLs HTTP/HTTPS
                        http_urls = re.findall(r'https?://[^\s<>"\']+', text_data)
                        if http_urls:
                            urls.extend(http_urls)
                        
                        if urls:
                            url = urls[0]  # Usa a primeira URL encontrada
                            nome_video = os.path.splitext(os.path.basename(aria2_file[:-6]))[0]
                            
                            # Adiciona à fila para retomada
                            self.add_to_queue(nome_video, url, download_path)
                            
                except Exception as e:
                    logger.error(f"Erro ao processar {aria2_file}: {str(e)}")
                    continue

            # Inicia o processamento da fila
            if not self.is_downloading and self.download_queue:
                self.process_download_queue()

        except Exception as e:
            logger.error(f"Erro ao verificar downloads: {str(e)}")
            raise
    
    def get_queue_info(self) -> dict:
        """Retorna informações sobre a fila de downloads"""
        return {
            'total_items': len(self.download_queue),
            'is_downloading': self.is_downloading,
            'current_download': self.current_download,
            'queue': self.download_queue
        }
    
    def __del__(self):
        """Limpa os processos ao fechar o programa"""
        try:
            # Mata o processo do aria2c
            if sys.platform == "win32":
                # Windows: usa taskkill
                subprocess.run(['taskkill', '/F', '/IM', 'aria2c.exe'],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            else:
                # Linux: usa pkill
                subprocess.run(['pkill', 'aria2c'],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)

        except Exception as e:
            logger.error(f"Erro ao limpar recursos: {e}")

# Função de conveniência para uso rápido
def criar_download_manager_com_db(caminho_db: str = 'videos.db') -> DownloadManager:
    """
    Cria um DownloadManager com DatabaseManager configurado
    
    Args:
        caminho_db: Caminho para o arquivo do banco de dados
        
    Returns:
        Instância do DownloadManager configurada
    """
    from database_manager import DatabaseManager
    from m3u_handler import M3UHandler
    
    db_manager = DatabaseManager(caminho_db)
    m3u_handler = M3UHandler(db_manager)
    download_manager = DownloadManager(db_manager, m3u_handler)
    
    return download_manager
