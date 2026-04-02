import os
import time
import requests
import tkinter as tk
from tkinter import messagebox
import threading
from threading import Thread
import shutil

class AdvancedDownloader:
    def __init__(self, root, download_path, user_agent, dns_server):
        self.root = root
        self.download_path = download_path
        self.user_agent = user_agent
        self.dns_server = dns_server
        self.download_queue = []
        self.is_downloading = False
        self.cancel_download = False        
        self._db_jobs_conn = None # Conexão para o DB de trabalhos

        # Variáveis para progresso
        self.download_progress = tk.DoubleVar()
        self.download_progress.set(0.0)
        self.progress_label = None
        self.speed_label = None
        self.download_info_label = None
        self.current_download_name = None  # Novo: armazena o nome do download atual

    def _db_execute_jobs(self, query, params=()):
        """Executa uma query no banco de dados de downloads (jobs) de forma thread-safe."""
        # Conexão específica para o banco de dados de trabalhos de download
        # Usando uma conexão por thread para segurança
        local_conn = sqlite3.connect('downloads.db')
        local_cursor = local_conn.cursor()
        local_cursor.execute(query, params)
        local_conn.commit()
        local_conn.close()

    def set_progress_widgets(self, progress_label, speed_label, download_info_label):
        """Define os widgets de progresso"""
        self.progress_label = progress_label
        self.speed_label = speed_label
        self.download_info_label = download_info_label

    def download_selected(self, items):
        """Inicia o download avançado dos itens selecionados"""
        if not items:
            messagebox.showwarning("Aviso", "Por favor, selecione um vídeo para download.")
            return

        if not os.path.exists(self.download_path):
            messagebox.showerror("Erro", "Pasta de download inválida.")
            return

        # Adiciona os vídeos selecionados à fila
        for item in items:
            values = item['values']
            nome_video = values[1]
            url = values[5]  # URL está na coluna 5
            
            if url:
                self.download_queue.append((nome_video, url, self.download_path))
            else:
                messagebox.showwarning("Aviso", f"URL não encontrada para o vídeo: {nome_video}")

        # Inicia o processamento da fila
        if not self.is_downloading:
            self.process_download_queue()

    def process_download_queue(self):
        """Processa a fila de downloads"""
        if not self.download_queue:
            self.is_downloading = False
            return

        self.is_downloading = True
        name, url, path = self.download_queue.pop(0)
        Thread(target=self.download_video, args=(name, url, path)).start()

    def get_file_extension(self, url):
        """Detecta a extensão do arquivo a partir da URL"""
        # Tenta extrair a extensão da URL
        extension = os.path.splitext(url)[1].lower()
        
        # Se não encontrou extensão na URL, tenta detectar pelo Content-Type
        if not extension:
            try:
                response = requests.head(url, headers={'User-Agent': self.user_agent}, timeout=30)
                content_type = response.headers.get('Content-Type', '').lower()
                
                if 'video/x-matroska' in content_type or 'video/mkv' in content_type:
                    extension = '.mkv'
                else:
                    # Para todos os outros tipos de vídeo, usa .mp4
                    extension = '.mp4'
            except:
                # Em caso de erro, usa .mp4 como padrão
                extension = '.mp4'
        
        # Garante que a extensão seja .mp4 ou .mkv
        if extension not in ['.mp4', '.mkv']:
            extension = '.mp4'
        
        return extension

    def sanitize_filename(self, filename):
        """Limpa o nome do arquivo removendo caracteres inválidos"""
        # Remove caracteres inválidos para nomes de arquivo
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')
        
        # Remove espaços extras
        filename = ' '.join(filename.split())
        
        # Remove pontos no final do nome
        filename = filename.rstrip('.')
        
        return filename

    def download_video(self, nome_video, url, download_path):
        """Tenta baixar o vídeo usando os protocolos disponíveis"""
        # Este método agora usa exclusivamente o downloader baseado em requests.
        try:
            self.cancel_download = False
            
            # Extrai o nome do conteúdo e a temporada
            content_name, season = self.extract_content_info(nome_video)

            # Cria a pasta do conteúdo
            content_folder = os.path.join(download_path, content_name)
            if not os.path.exists(content_folder):
                os.makedirs(content_folder)

            # Obtém a extensão correta do arquivo
            extension = self.get_file_extension(url)

            # Se for uma série, cria a pasta da temporada
            if season:
                season_folder = os.path.join(content_folder, season)
                if not os.path.exists(season_folder):
                    os.makedirs(season_folder)
                file_path = os.path.join(season_folder, f"{nome_video}{extension}")
            else:
                file_path = os.path.join(content_folder, f"{nome_video}{extension}")

            # Chama o downloader com requests (antigo webclient/reserva)
            success = self.download_with_webclient(nome_video, url, file_path)

            if not success and not self.cancel_download:
                messagebox.showerror("Erro", f"Falha ao baixar {nome_video}")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao baixar {nome_video}: {e}")
        finally:
            # Processa o próximo download na fila
            self.root.after(1000, self.process_download_queue)

    def calculate_eta(self, downloaded, total, speed):
        """Calcula o tempo estimado restante de forma mais precisa e amigável"""
        try:
            if not total or not speed or speed <= 0:
                return "Calculando..."
            
            remaining_bytes = total - downloaded
            if remaining_bytes <= 0:
                return "Completo"
            
            seconds = remaining_bytes / speed
            
            # Formata o tempo de forma mais amigável
            if seconds < 1:
                return "Menos de 1s"
            elif seconds < 60:
                return f"{int(seconds)}s"
            elif seconds < 3600:
                minutes = int(seconds / 60)
                remaining_seconds = int(seconds % 60)
                if remaining_seconds > 0:
                    return f"{minutes}m {remaining_seconds}s"
                return f"{minutes}m"
            elif seconds < 86400:  # Menos de 24 horas
                hours = int(seconds / 3600)
                minutes = int((seconds % 3600) / 60)
                if minutes > 0:
                    return f"{hours}h {minutes}m"
                return f"{hours}h"
            else:  # Mais de 24 horas
                days = int(seconds / 86400)
                hours = int((seconds % 86400) / 3600)
                if hours > 0:
                    return f"{days}d {hours}h"
                return f"{days}d"
                
        except Exception as e:
            return "Erro no cálculo"

    def download_with_requests(self, url, file_path, name):
        """Download usando requests com suporte a retomada e chunks"""
        try:
            # Configura a sessão do requests
            session = requests.Session()
            session.headers.update({
                'User-Agent': self.user_agent,
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            })

            # Verifica se o arquivo já existe
            file_exists = os.path.exists(file_path)
            file_size = os.path.getsize(file_path) if file_exists else 0
            
            # Faz uma requisição HEAD primeiro para obter o tamanho total
            response = session.head(url, timeout=30, allow_redirects=True)
            total_size = int(response.headers.get('content-length', 0))
            
            # Se o arquivo já existe com o tamanho correto, pula o download
            if file_exists and file_size == total_size:
                if self.download_info_label:
                    self.download_info_label.configure(text=f"Arquivo já existe: {name}")
                return True
            
            # Configura o range se o arquivo existir
            headers = {}
            if file_exists and file_size < total_size:
                headers['Range'] = f'bytes={file_size}-'
            
            # Faz o download
            response = session.get(url, headers=headers, stream=True, timeout=30)
            
            # Verifica se o servidor suporta download parcial
            if file_exists and response.status_code == 206:  # Partial Content
                mode = 'ab'  # Append em modo binário
            else:
                mode = 'wb'  # Write em modo binário
                file_size = 0
            
            # Tamanho do chunk (8MB)
            chunk_size = 8 * 1024 * 1024
            
            # Variáveis para controle de progresso
            start_time = time.time()
            last_update_time = start_time
            downloaded = file_size
            
            with open(file_path, mode) as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if self.cancel_download:
                        return False
                        
                    if chunk:  # Filtrar keep-alive chunks vazios
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Atualiza o progresso a cada 0.5 segundos
                        current_time = time.time()
                        if current_time - last_update_time >= 0.5:
                            self.update_progress(downloaded, total_size, start_time)
                            last_update_time = current_time
                            
                            # Força o flush para o disco
                            f.flush()
                            os.fsync(f.fileno())
            
            # Verifica se o download foi concluído corretamente
            success, error = self.verify_download(file_path, total_size)
            if not success:
                if self.download_info_label:
                    self.download_info_label.configure(text=f"Erro na verificação: {error}")
                return False
            
            if self.download_info_label:
                self.download_info_label.configure(text=f"Download concluído: {name}")
            return True
            
        except requests.exceptions.RequestException as e:
            if self.download_info_label:
                self.download_info_label.configure(text=f"Erro na requisição: {str(e)}")
            return False
        except Exception as e:
            if self.download_info_label:
                self.download_info_label.configure(text=f"Erro: {str(e)}")
            return False

    def log_reserva(self, message, error=False):
        """Registra logs do modo reserva"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] [RESERVA] {message}"
        print(log_msg)  # Exibe no console
        
        # Salva em arquivo de log
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        log_file = os.path.join(log_dir, "reserva_downloads.log")
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_msg + "\n")
        except Exception as e:
            print(f"Erro ao salvar log: {str(e)}")

    def download_with_webclient(self, nome_video, url, file_path):
        """Tenta baixar o vídeo usando requests com múltiplas tentativas."""
        try:
            max_retries = 5
            retry_count = 0
            chunk_size = 8 * 1024 * 1024  # 8MB chunks
            total_size = None
            self.current_download_name = nome_video  # Armazena o nome atual do download
            
            # Limpa e sanitiza o nome do arquivo
            nome_video = self.sanitize_filename(nome_video)
            
            self.log_reserva(f"Iniciando download (requests): {nome_video}")
            self.log_reserva(f"URL: {url}")
            self.log_reserva(f"Arquivo destino: {file_path}")
            
            # Limpa as informações de progresso antes de começar
            self.clear_progress_info()
            
            while retry_count < max_retries and not self.cancel_download:
                try:
                    # Obtém a extensão do arquivo
                    extension = self.get_file_extension(url)
                    self.log_reserva(f"Extensão detectada: {extension}")
                    
                    # Verifica arquivo existente
                    file_exists = os.path.exists(file_path)
                    file_size = os.path.getsize(file_path) if file_exists else 0
                    
                    # Configura a sessão
                    session = requests.Session()
                    headers = {
                        'User-Agent': self.user_agent,
                        'Accept': '*/*',
                        'Accept-Encoding': 'identity'
                    }
                    
                    if file_exists and file_size > 0:
                        headers['Range'] = f'bytes={file_size}-'
                        self.log_reserva(f"Retomando download de: {self.format_size(file_size)}")
                    
                    # Tenta obter o tamanho total de várias formas
                    try:
                        # Primeiro tenta com HEAD
                        response = session.head(url, headers=headers, timeout=30, allow_redirects=True)
                        content_length = response.headers.get('content-length')
                        
                        # Se não encontrou com HEAD, tenta com GET
                        if not content_length or not content_length.isdigit():
                            response = session.get(url, headers=headers, stream=True, timeout=30)
                            content_length = response.headers.get('content-length')
                            response.close()  # Fecha a conexão para não consumir dados
                        
                        if content_length and content_length.isdigit():
                            total_size = int(content_length)
                            if total_size > 0:  # Verifica se o tamanho é válido
                                self.log_reserva(f"Tamanho total detectado: {self.format_size(total_size)}")
                            else:
                                self.log_reserva("Tamanho total inválido detectado")
                                total_size = None
                        else:
                            self.log_reserva("Não foi possível determinar tamanho total com content-length")
                            
                            # Tenta obter o tamanho do arquivo se já existir
                            if file_exists and file_size > 0:
                                total_size = file_size
                                self.log_reserva(f"Usando tamanho do arquivo existente: {self.format_size(total_size)}")
                            
                    except Exception as e:
                        self.log_reserva(f"Erro ao detectar tamanho total: {str(e)}")
                        total_size = None
                    
                    # Inicia o download
                    response = session.get(url, stream=True, headers=headers, timeout=60)
                    response.raise_for_status()
                    
                    # Modo de escrita
                    mode = 'ab' if file_exists and response.status_code == 206 else 'wb'
                    if mode == 'wb':
                        file_size = 0
                    
                    # Download
                    start_time = time.time()
                    downloaded = file_size
                    last_update = start_time
                    last_progress = -1  # Para controlar atualizações da barra
                    
                    with open(file_path, mode) as f:
                        for chunk in response.iter_content(chunk_size=chunk_size):
                            if self.cancel_download:
                                f.close()
                                if mode == 'wb':
                                    try:
                                        os.remove(file_path)
                                        self.log_reserva("Arquivo parcial removido")
                                    except:
                                        pass
                                return False
                            
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                
                                # Atualiza progresso a cada 0.5 segundos
                                current_time = time.time()
                                if current_time - last_update >= 0.5:
                                    self.update_progress_reserva(downloaded, total_size, start_time)
                                    last_update = current_time
                    
                    # Verifica conclusão
                    final_size = os.path.getsize(file_path)
                    # Verificação de integridade
                    success, error = self.verify_download(file_path, total_size)
                    if success:
                        self.log_reserva("Download concluído com sucesso!")
                        if self.download_info_label:
                            self.download_info_label.configure(text=f"Download concluído: {nome_video}")
                        if hasattr(self, 'download_progress'):
                            self.download_progress.set(1.0)  # 100%
                            self.root.update_idletasks()
                        return True
                    else:
                        self.log_reserva(f"Erro na verificação de integridade: {error}")
                        if self.download_info_label:
                            self.download_info_label.configure(text=f"Erro de integridade: {error}")
                        # Remove arquivo corrompido
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            self.log_reserva(f"Erro ao remover arquivo corrompido: {str(e)}")
                        raise Exception(f"Download incompleto ou corrompido: {error}")
                except Exception as e:
                    retry_count += 1
                    self.log_reserva(f"Erro na tentativa {retry_count}: {str(e)}")
                    if retry_count < max_retries:
                        time.sleep(5)
                        continue
            
            self.log_reserva("Todas as tentativas falharam")
            if self.download_info_label:
                self.download_info_label.configure(text="Erro no download")
            return False
            
        finally:
            self.clear_progress_info()
            self.current_download_name = None  # Limpa o nome do download atual

    def clear_progress_info(self):
        """Limpa todas as informações de progresso da interface"""
        if hasattr(self, 'download_progress'):
            if self.download_progress: self.download_progress.set(0)
        if self.progress_label:
            self.progress_label.configure(text="0%")
        if self.speed_label:
            self.speed_label.configure(text="0 MB/s")
        if self.download_info_label:
            self.download_info_label.configure(text="")

    def update_progress(self, downloaded, total_size, start_time, error=None):
        """Atualiza o progresso do download na interface"""
        try:
            if error:
                if self.download_info_label:
                    self.download_info_label.configure(text=f"Erro: {error}")
                return

            # Calcula velocidade e progresso
            elapsed_time = time.time() - start_time
            speed = downloaded / elapsed_time if elapsed_time > 0 else 0
            
            # Calcula progresso
            if total_size and total_size > 0:
                progress = min(100, (downloaded / total_size) * 100)
            else:
                # Se não temos o tamanho total, estima baseado no que já foi baixado
                if downloaded > 0:
                    progress = min(99, (downloaded / (downloaded * 1.5)) * 100)
                else:
                    progress = 0
            
            # Calcula ETA
            eta = self.calculate_eta(downloaded, total_size, speed)
            
            # Atualiza a barra de progresso
            if hasattr(self, 'download_progress'):
                if self.download_progress: self.download_progress.set(progress / 100)
                if hasattr(self.root, 'update_idletasks'): self.root.update_idletasks()
            
            # Atualiza os labels
            if self.progress_label:
                self.progress_label.configure(text=f"{progress:.1f}%")
            
            if self.speed_label:
                speed_str = self.format_speed(speed)
                downloaded_str = self.format_size(downloaded)
                total_str = self.format_size(total_size) if total_size else "?"
                self.speed_label.configure(text=f"{speed_str} | {downloaded_str}/{total_str} | ETA: {eta}")
            
            if self.download_info_label:
                self.download_info_label.configure(text=f"Baixando: {self.current_download_name}")
            
            # Log de progresso
            self.log_reserva(
                f"Progresso: {progress:.1f}% | "
                f"Velocidade: {speed_str} | "
                f"Baixado: {downloaded_str}/{total_str} | "
                f"ETA: {eta}"
            )
            
        except Exception as e:
            print(f"Erro ao atualizar progresso: {str(e)}")

    def format_speed(self, speed):
        """Formata a velocidade de download em uma string legível"""
        try:
            if speed <= 0:
                return "0 B/s"
                
            # Converte para bytes por segundo
            speed_bytes = speed
            
            # Formata com precisão adequada
            if speed_bytes < 1024:  # Bytes
                return f"{speed_bytes:.0f} B/s"
            elif speed_bytes < 1024 * 1024:  # KB
                return f"{speed_bytes/1024:.1f} KB/s"
            elif speed_bytes < 1024 * 1024 * 1024:  # MB
                return f"{speed_bytes/(1024*1024):.1f} MB/s"
            else:  # GB
                return f"{speed_bytes/(1024*1024*1024):.2f} GB/s"
        except Exception as e:
            return "0 B/s"

    def format_size(self, size):
        """Formata o tamanho em bytes em uma string legível"""
        try:
            if size is None or size <= 0:
                return "0 B"
                
            # Formata com precisão adequada
            if size < 1024:  # Bytes
                return f"{size:.0f} B"
            elif size < 1024 * 1024:  # KB
                return f"{size/1024:.1f} KB"
            elif size < 1024 * 1024 * 1024:  # MB
                return f"{size/(1024*1024):.1f} MB"
            else:  # GB
                return f"{size/(1024*1024*1024):.2f} GB"
        except Exception as e:
            return "0 B"

    def extract_content_info(self, name):
        """Extrai informações do conteúdo (nome e temporada)"""
        import re
        match = re.search(r"(.*?)\s*(S\d{2})\s*E\d{2}", name)
        if match:
            content_name = match.group(1).strip()
            season = match.group(2).strip()
            return content_name, season
        else:
            return name, None

    def cancel_current_download(self):
        """Cancela o download atual"""
        self.cancel_download = True
        self.log_reserva("Cancelamento de download solicitado pelo usuário.")

        # A flag self.cancel_download será verificada no loop de download,
        # que então interromperá o processo. A UI é limpa no bloco finally.
        if self.download_info_label:
            self.download_info_label.configure(text="Cancelando...")
        
        # Força a limpeza da fila de downloads
        self.download_queue.clear()
        self.is_downloading = False

    def verify_download(self, file_path, expected_size=None):
        """Verifica se o download foi concluído corretamente"""
        try:
            if not os.path.exists(file_path):
                return False, "Arquivo não encontrado"
                
            file_size = os.path.getsize(file_path)
            if expected_size and file_size != expected_size:
                return False, f"Tamanho incorreto: {self.format_size(file_size)} vs {self.format_size(expected_size)}"
                
            # Verifica se o arquivo pode ser aberto
            with open(file_path, 'rb') as f:
                # Lê os primeiros bytes para verificar se o arquivo não está corrompido
                f.read(1024)
                
            return True, None
        except Exception as e:
            return False, f"Erro ao verificar arquivo: {str(e)}"

    def update_progress_reserva(self, downloaded, total_size, start_time, error=None):
        """Atualiza o progresso do download na interface (modo reserva)"""
        try:
            if error:
                if self.download_info_label:
                    self.download_info_label.configure(text=f"Erro: {error}")
                return

            # Calcula velocidade e progresso
            elapsed_time = time.time() - start_time
            speed = downloaded / elapsed_time if elapsed_time > 0 else 0
            
            # Calcula progresso
            if total_size and total_size > 0:
                progress = min(100, (downloaded / total_size) * 100)
            else:
                # Se não temos o tamanho total, estima baseado no que já foi baixado
                if downloaded > 0:
                    progress = min(99, (downloaded / (downloaded * 1.5)) * 100)
                else:
                    progress = 0
            
            # Calcula ETA
            eta = self.calculate_eta(downloaded, total_size, speed)
            
            # Atualiza a barra de progresso
            if hasattr(self, 'download_progress'):
                if self.download_progress: self.download_progress.set(progress / 100)
                if hasattr(self.root, 'update_idletasks'): self.root.update_idletasks()
            
            # Atualiza os labels
            if self.progress_label:
                self.progress_label.configure(text=f"{progress:.1f}%")
            
            if self.speed_label:
                speed_str = self.format_speed_reserva(speed)
                downloaded_str = self.format_size_reserva(downloaded)
                total_str = self.format_size_reserva(total_size) if total_size else "?"
                self.speed_label.configure(text=f"{speed_str} | {downloaded_str}/{total_str} | ETA: {eta}")
            
            if self.download_info_label:
                self.download_info_label.configure(text=f"Baixando: {self.current_download_name}")
            
            # Log de progresso
            self.log_reserva(
                f"Progresso: {progress:.1f}% | "
                f"Velocidade: {speed_str} | "
                f"Baixado: {downloaded_str}/{total_str} | "
                f"ETA: {eta}"
            )
            
        except Exception as e:
            print(f"Erro ao atualizar progresso: {str(e)}")

    def format_speed_reserva(self, speed):
        """Formata a velocidade de download em uma string legível (modo reserva)"""
        try:
            if speed <= 0:
                return "0 B/s"
                
            # Converte para bytes por segundo
            speed_bytes = speed
            
            # Formata com precisão adequada
            if speed_bytes < 1024:  # Bytes
                return f"{speed_bytes:.0f} B/s"
            elif speed_bytes < 1024 * 1024:  # KB
                return f"{speed_bytes/1024:.1f} KB/s"
            elif speed_bytes < 1024 * 1024 * 1024:  # MB
                return f"{speed_bytes/(1024*1024):.1f} MB/s"
            else:  # GB
                return f"{speed_bytes/(1024*1024*1024):.2f} GB/s"
        except Exception as e:
            return "0 B/s"

    def format_size_reserva(self, size):
        """Formata o tamanho em bytes em uma string legível (modo reserva)"""
        try:
            if size is None or size <= 0:
                return "0 B"
                
            # Formata com precisão adequada
            if size < 1024:  # Bytes
                return f"{size:.0f} B"
            elif size < 1024 * 1024:  # KB
                return f"{size/1024:.1f} KB"
            elif size < 1024 * 1024 * 1024:  # MB
                return f"{size/(1024*1024):.1f} MB"
            else:  # GB
                return f"{size/(1024*1024*1024):.2f} GB"
        except Exception as e:
            return "0 B" 