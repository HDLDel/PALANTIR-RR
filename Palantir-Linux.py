import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import re
import requests
import threading
from threading import Thread
import concurrent.futures
import customtkinter as ctk
import os
import webbrowser
import unicodedata
import aria2p
import subprocess
import time
import json
import sys
import signal
import traceback
from unidecode import unidecode
from advanced_downloader import AdvancedDownloader
from organize_folders import organize_folders
from categorias import PASTAS, FOLDER_MAPPING, CATEGORIAS_VALIDAS, normalizar
import logging
import datetime
import shutil
from urllib.parse import quote

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('palantir.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import platform
import traceback
from ttkthemes import ThemedTk

# Constantes de estilo
CORES_BOTOES = {
    'DOWNLOAD': '#2ecc71',      # Verde
    'DOWNLOAD_HOVER': '#27ae60', # Verde escuro
    'VER_FILA': '#9b59b6',      # Roxo
    'VER_FILA_HOVER': '#8e44ad', # Roxo escuro
    'RESERVA': '#f39c12',       # Laranja escuro
    'RESERVA_HOVER': '#e67e22', # Laranja mais escuro
    'ORGANIZAR': '#3498db',     # Azul claro
    'ORGANIZAR_HOVER': '#2980b9', # Azul escuro
    'LIMPAR': '#e74c3c',        # Vermelho
    'LIMPAR_HOVER': '#c0392b',  # Vermelho escuro
    'PLAYER': '#2ecc71',        # Verde
    'PLAYER_HOVER': '#27ae60',  # Verde escuro
    'API_KEY': '#f1c40f',       # Amarelo
    'API_KEY_HOVER': '#f39c12', # Laranja
    'LINKS': '#e74c3c',         # Vermelho
    'LINKS_HOVER': '#c0392b',   # Vermelho escuro
    'EDITOR_URLS': '#e67e22',   # Laranja
    'EDITOR_URLS_HOVER': '#d35400', # Laranja escuro
    'ATUALIZAR': '#3498db',     # Azul
    'ATUALIZAR_HOVER': '#2980b9', # Azul escuro
    'LIMPAR_RETOMADA': '#e74c3c', # Vermelho
    'LIMPAR_RETOMADA_HOVER': '#c0392b', # Vermelho escuro
    'PENDENTES': '#9b59b6',     # Roxo
    'PENDENTES_HOVER': '#8e44ad', # Roxo escuro
    'FECHAR': '#95a5a6',        # Cinza
    'FECHAR_HOVER': '#7f8c8d',  # Cinza escuro
    'REMOVER_SEL': '#f39c12',   # Laranja
    'REMOVER_SEL_HOVER': '#e67e22', # Laranja escuro
    'ABRIR': '#3498db',         # Azul
    'ABRIR_HOVER': '#2980b9',   # Azul escuro
    'COPIAR': '#f1c40f',        # Amarelo
    'COPIAR_HOVER': '#f39c12',  # Laranja
    'D1_ARIA': '#2ecc71',       # Verde
    'D1_ARIA_HOVER': '#27ae60', # Verde escuro
    'D2_REQUEST': '#e67e22',    # Laranja
    'D2_REQUEST_HOVER': '#d35400', # Laranja escuro
    'D3_URLLIB': '#1abc9c',     # Verde água
    'D3_URLLIB_HOVER': '#16a085', # Verde água escuro
    'SAVE_CONFIG': '#2ecc71',   # Verde
    'SAVE_CONFIG_HOVER': '#27ae60', # Verde escuro
    'USER_AGENT': '#3498db',    # Azul
    'USER_AGENT_HOVER': '#2980b9', # Azul escuro
    'THEME': '#9b59b6',         # Roxo
    'THEME_HOVER': '#8e44ad',   # Roxo escuro
    'ESTATISTICAS': '#9b59b6',  # Roxo
    'ESTATISTICAS_HOVER': '#8e44ad', # Roxo escuro
}

def validar_url(url):
    """
    Valida se uma URL é válida
    
    Args:
        url (str): URL para validação
        
    Returns:
        bool: True se a URL for válida, False caso contrário
    """
    import re
    regex = re.compile(
        r'^https?://'  # http:// ou https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domínio...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...ou ip
        r'(?::\d+)?'  # porta opcional
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url is not None and regex.search(url)


def get_base_dir():
    """Obtém o diretório base, funcionando tanto para script quanto para executável PyInstaller"""
    if getattr(sys, 'frozen', False):
        # Modo executável V3.5.40
        return os.path.dirname(sys.executable)
    else:
        # Modo script normal
        return os.path.dirname(os.path.abspath(__file__))


class Palantir:
    def __init__(self):
        """Inicializa a aplicação"""
        # 1. Definir valores padrão para todos os atributos de configuração
        self.download_path_str = os.getcwd()
        self.user_agent_str = "Mozilla/5.0"
        self.dns_server_str = ""
        self.active_theme = "black"
        self.tmdb_api_key_str = ""  # Chave padrão
        self.m3u_base_url_str = "DIGITE AQUI SUA URL"
        self.config_file = os.path.join(get_base_dir(), "config.json")

        # 2. Carregar configurações do arquivo, sobrescrevendo os padrões
        self.load_config()

        # 3. Inicializar variáveis de controle
        self.is_downloading = False
        self.download_queue = []
        self.current_download = None
        self.dados_db = []
        self.dados_m3u = []
        self.is_generating_m3u = False

        # Controle de tentativas de retomada
        self.download_retry_count = {}  # Dicionário para contar tentativas por download
        self.max_retries = 5  # Limite padrão de tentativas (ciclos de estagnação)
        self.unlimited_retries = False  # Flag para tentativas ilimitadas

        # Controle de ciclos de estagnação da fila
        self.last_queue_size = 0  # Tamanho da fila no ciclo anterior
        self.stagnation_counter = 5  # Contador de ciclos de estagnação (inicia em 5)

        # 4. Criar a janela principal
        self.root = ThemedTk(theme=self.active_theme)
        try:
            self.root.set_theme(self.active_theme)
        except Exception as e:
            print(f"Erro ao aplicar o tema {self.active_theme}: {e}")
        self.root.title("Palantir Versão V3.5.40")
        # Maximiza de forma cross-platform
        if platform.system() == "Windows":
            self.root.state('zoomed')
        else:
            try:
                self.root.attributes('-zoomed', True)
            except:
                self.root.attributes('-fullscreen', True)
        self.root.geometry("1400x900")  # Tamanho inicial maior
        self.root.minsize(1200, 800)     # Tamanho mínimo

        # 5. Inicializar variáveis Tkinter agora que a root existe
        self.download_path = tk.StringVar(self.root, value=self.download_path_str)
        self.user_agent = tk.StringVar(self.root, value=self.user_agent_str)
        self.dns_server = tk.StringVar(self.root, value=self.dns_server_str)
        self.tmdb_api_key = tk.StringVar(self.root, value=self.tmdb_api_key_str)
        self.m3u_base_url = tk.StringVar(self.root, value=self.m3u_base_url_str)
        self.download_progress = tk.DoubleVar(self.root)
        self.download_progress.set(0.0)

        # 6. Outras variáveis de instância
        self.conn = None # Inicializa conn como None
        self.cursor = None # Inicializa cursor como None
        self.current_url = None
        self.cancel_download = False
        self.reserva_mode = False
        self.player_type = "MPV (Sistema)" # MPV (Sistema) é o player padrão agora
        # Caminhos dos players (Linux - sem .exe)
        # Usa get_base_dir() para funcionar tanto no script quanto no executável V3.5.40
        base = get_base_dir()

        # Linux: MPV do PATH do sistema, AppImages da pasta Players
        self.mpv_path = "mpv"  # PATH do sistema
        self.vlc_path = os.path.join(base, 'Players', 'VLC.AppImage')
        self.mpv_appimage_path = os.path.join(base, 'Players', 'mpv.AppImage')
        self.mpv_process = None
        self.available_themes = [
            "arc", "equilux", "breeze", "clearlooks", "elegance", "radiance",
            "plastik", "alt", "classic", "default", "clam", "vista", "winnative",
            "xpnative", "keramik", "keramik_alt", "aquativo", "black", "blue",
            "winxpblue", "ubuntu", "ubuntu-mono-dark", "ubuntu-mono-light",
            "ubuntu-mono", "ubuntu-dark", "ubuntu-light", "ubuntu"
        ]
        
        # Define o ícone do programa
        def definir_icone(root):
            try:
                # Linux usa PNG
                icon_filename = "palantir.png"

                # Caminhos possíveis onde o ícone pode estar
                possible_paths = [
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), icon_filename),
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", icon_filename),
                    os.path.join(os.path.dirname(sys.executable), icon_filename),
                    os.path.join(os.path.dirname(sys.executable), "assets", icon_filename),
                    icon_filename  # Diretório atual
                ]

                for icon_path in possible_paths:
                    if os.path.exists(icon_path):
                        # Define o ícone da janela principal no Linux
                        from PIL import ImageTk
                        icon = ImageTk.PhotoImage(file=icon_path)
                        root.wm_iconphoto(True, icon)

                        print(f"Ícone definido com sucesso: {icon_path}")
                        return True

                print("Aviso: Ícone não encontrado em nenhum dos caminhos possíveis")
                return False

            except Exception as e:
                print(f"Erro ao definir ícone: {e}")
                return False

        # 7. Configuração do tema e inicialização de serviços
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        self.start_aria2c()
        self.aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800))
        
        self.db_cache = {}
        self.db_cache_loaded = False
        
        # 8. Sequência final de inicialização
        self.check_dependencies()
        self.test_api_connection()
        self.init_database()
        self.criar_interface()

        self.advanced_downloader = AdvancedDownloader(
            self.root,
            self.download_path.get(),
            self.user_agent.get(),
            self.dns_server.get()
        )

        # Novas estruturas de dados para indexação
        self.index_nome = {}      # índice por nome
        self.index_categoria = {} # índice por categoria
        self.index_tipo = {}      # índice por tipo
        self.index_temporada = {} # índice por temporada

        # Inicializa o player externo (agora será sempre MPV via subprocess)
        self.external_player_process = None

        # Estatísticas de uso
        self.estatisticas = {
            'downloads_realizados': 0,
            'buscas_realizadas': 0,
            'erros_encontrados': 0
        }

    def check_dependencies(self):
        """Verifica se todas as dependências necessárias estão instaladas"""
        missing_deps = []
            
        # Verifica aria2
        try:
            subprocess.run(['aria2c', '--version'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            missing_deps.append("aria2")
            
        # Verifica MPV
        try:
            # Tenta executar o mpv para ver se está no PATH
            subprocess.run([self.mpv_path, '--version'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL,
                         check=True) # check=True levanta CalledProcessError se o comando falhar
        except (FileNotFoundError, subprocess.CalledProcessError):
            missing_deps.append("mpv")
            
        if missing_deps:
            error_msg = "Dependências faltando:\n"
            for dep in missing_deps:
                error_msg += f"- {dep}\n"
            error_msg += "\nPor favor, instale as dependências necessárias:\n"
            if os.name == 'nt':
                error_msg += "Baixe e instale o aria2 de: https://aria2.github.io/\n"
                error_msg += "Baixe e instale o MPV de: https://mpv.io/"
            else:
                error_msg += "sudo dnf install aria2 mpv" # Exemplo para Fedora
            messagebox.showerror("Erro", error_msg)
            sys.exit(1)
            
    def test_api_connection(self):
        """Testa a conexão com a Servidor de TMDB"""
        try:
            API_KEY = self.tmdb_api_key.get()
            if not API_KEY:
                print("⚠️ Chave da Servidor de TMDB não configurada.")
                messagebox.showwarning("API Key Faltando", "A chave da Servidor de TMDB não foi configurada. Por favor, insira uma chave.")
                return False
            url = f"https://api.themoviedb.org/3/movie/550?api_key={API_KEY}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print("✅ Conexão com Servidor de TMDB OK")
                return True
            else:
                print(f"⚠️ Servidor de TMDB retornou status {response.status_code}")
                # Pergunta ao usuário se deseja inserir uma nova chave
                if messagebox.askyesno("Erro de TMDB", f"A chave de TMDB pode ser inválida ou expirada (Status: {response.status_code}).\n\nDeseja inserir uma nova chave agora?"):
                    return self.change_tmdb_api_key()
                else:
                    messagebox.showerror("Licença Inválida", "O programa será fechado por falta de uma licença válida.")
                    self.root.destroy()
                    return False
        except Exception as e:
            print(f"❌ Erro ao conectar com Servidor de TMDB: {e}")
            messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao servidor de TMDB. Verifique sua conexão.\nErro: {e}")
            return False

    def change_tmdb_api_key(self):
        """Abre um diálogo para o usuário inserir uma nova chave de TMDB."""
        dialog = ctk.CTkInputDialog(text="Digite sua chave de TMDB:", title="chave de TMDB")
        new_key = dialog.get_input()
        if new_key and new_key.strip():
            self.tmdb_api_key.set(new_key.strip())
            self.save_config()
            messagebox.showinfo("Sucesso", "chave de TMDB atualizada. Testando a nova chave...")
            return self.test_api_connection()
        else:
            messagebox.showwarning("Aviso", "Nenhuma chave inserida.")
            return False

    def change_m3u_base_url(self):
        """Abre um diálogo para o usuário inserir uma nova URL base do M3U."""
        dialog = ctk.CTkInputDialog(text="Digite a URL base do M3U:", title="URL Base")
        new_url = dialog.get_input()
        if new_url is not None and new_url.strip():
            self.m3u_base_url.set(new_url.strip())
            self.save_config()
            messagebox.showinfo("Sucesso", "URL base atualizada com sucesso.")
        elif new_url is not None:
            messagebox.showwarning("Aviso", "Nenhuma URL inserida.")

    def start_aria2c(self):
        """Inicia o servidor aria2c"""
        try:
            # Tenta encerrar instâncias anteriores do aria2c que possam estar travando a porta
            subprocess.run(['pkill', '-x', 'aria2c'],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
            time.sleep(0.5)

            aria2c_path = 'aria2c'
            print(f"Tentando aria2c do PATH: {aria2c_path}")
            self.aria2c_process = subprocess.Popen(
                [aria2c_path, "--enable-rpc", "--rpc-listen-all=true", "--rpc-allow-origin-all", "--daemon=false"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            time.sleep(2)
            if self.aria2c_process.poll() is None:
                print(f"aria2c do PATH iniciado com PID: {self.aria2c_process.pid}")
            else:
                print(f"Aviso: aria2c falhou ao iniciar (código {self.aria2c_process.poll()}). Assumindo que já existe uma instância rodando.")

            print(f"Usando aria2c: {aria2c_path}")

        except FileNotFoundError as e:
            print(f"ERRO: aria2c não encontrado: {e}")
            messagebox.showerror("Erro", "aria2c não encontrado. Por favor, instale o aria2 primeiro.\n\nNo Fedora: sudo dnf install aria2\nNo Ubuntu: sudo apt install aria2\nNo Arch Linux: sudo pacman -S aria2")
            sys.exit(1)
        except Exception as e:
            print(f"ERRO ao iniciar aria2c: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erro", f"Erro ao iniciar aria2c: {e}")
            sys.exit(1)

    def load_config(self):
        """Carrega as configurações do arquivo para atributos Python simples."""
        try:
            config = {}
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f, strict=False)
                except json.JSONDecodeError:
                    # Fallback caso o usuário tenha inserido caminhos do Windows com barras simples
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    content = content.replace('\\', '\\\\').replace('\\\\"', '\\"')
                    config = json.loads(content, strict=False)
            # Atualiza os atributos _str e active_theme
            self.download_path_str = config.get('default_download_path', self.download_path_str)
            self.user_agent_str = config.get('user_agent', self.user_agent_str)
            self.dns_server_str = config.get('dns_server', self.dns_server_str)
            self.active_theme = config.get('theme', self.active_theme)
            self.tmdb_api_key_str = config.get('tmdb_api_key', self.tmdb_api_key_str)
            self.m3u_base_url_str = config.get('m3u_base_url', self.m3u_base_url_str)
        except Exception as e:
            print(f"Erro ao carregar configurações: {e}")
            # Mantém os padrões definidos no __init__ em caso de erro

    def save_config(self):
        """Salva as configurações no arquivo"""
        try:
            config = {}
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f, strict=False)
                except:
                    pass

            config['default_download_path'] = self.download_path.get()
            config['user_agent'] = self.user_agent.get()
            config['dns_server'] = self.dns_server.get()
            config['theme'] = self.active_theme
            config['tmdb_api_key'] = self.tmdb_api_key.get()
            if hasattr(self, 'm3u_base_url'):
                config['m3u_base_url'] = self.m3u_base_url.get()

            # Garante que o diretório existe
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
                
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")

    def browse_directory(self):
        """Abre diálogo para selecionar pasta de download"""
        directory = filedialog.askdirectory(initialdir=self.download_path.get())
        if directory:
            self.download_path.set(directory)
            # Salva automaticamente a nova configuração
            self.save_config()

    def get_url_from_selection(self, item=None):
        """Obtém a URL do item selecionado de forma segura"""
        try:
            if item is None:
                selected_items = self.tree.selection()
                if not selected_items:
                    return None
                item = selected_items[0]

            values = self.tree.item(item)['values']
            if not values or len(values) < 7:  # Verifica se tem valores suficientes
                return None

            nome_video = values[1]
            link_origem = values[6]  # Pega o link de origem diretamente da treeview

            # Se temos o link de origem na treeview e ele é válido, usamos ele
            if link_origem and isinstance(link_origem, str) and link_origem.strip():
                url = link_origem.strip()
                if validar_url(url):
                    return url
                else:
                    logger.warning(f"URL inválida encontrada na treeview: {url}")
                    return None

            # Se não temos o link na treeview, buscamos nas fontes de dados
            # Busca primeiro no banco de dados
            for item_db in self.dados_db:
                if item_db[1] == nome_video:  # item_db[1] é o nome
                    if item_db[2] and isinstance(item_db[2], str) and item_db[2].strip():  # item_db[2] é a URL
                        url = item_db[2].strip()
                        if validar_url(url):
                            return url
                        else:
                            logger.warning(f"URL inválida encontrada no banco de dados: {url}")

            # Se não encontrou no banco, busca nos dados M3U
            for item_m3u in self.dados_m3u:
                if item_m3u[0] == nome_video:
                    if item_m3u[5] and isinstance(item_m3u[5], str) and item_m3u[5].strip():  # item_m3u[5] é a URL
                        url = item_m3u[5].strip()
                        if validar_url(url):
                            return url
                        else:
                            logger.warning(f"URL inválida encontrada nos dados M3U: {url}")

            return None

        except Exception as e:
            logger.error(f"Erro ao obter URL: {str(e)}")
            return None

    def download_selected(self):
        """Inicia o download dos itens selecionados"""
        try:
            # Reseta o controle de estagnação para começar como se fosse a primeira vez
            self.reset_stagnation_control()

            selected_items = self.tree.selection()
            if not selected_items:
                messagebox.showwarning("Aviso", "Por favor, selecione um vídeo para download.")
                return

            base_download_path = self.download_path.get()
            download_path = self.download_path.get()
            if not os.path.exists(download_path):
                messagebox.showerror("Erro", "Pasta de download inválida.")
                return

            # Adiciona os vídeos selecionados à fila
            for item in selected_items:
                time.sleep(0.1) # Adiciona um pequeno delay para não sobrecarregar o servidor com HEAD requests
                values = self.tree.item(item)['values']
                if not values or len(values) < 7:
                    continue
                nome_video = values[1]
                url = self.get_url_from_selection(item)

                if not url:
                    messagebox.showwarning("Aviso", f"URL não encontrada para o vídeo: {nome_video}")
                    continue

                # --- Início: Lógica de Registro em downloads.db ---
                try:
                    # 1. Inserir imediatamente no banco de dados com tamanho 0.
                    # O tamanho será atualizado posteriormente pelo worker de download.
                    self._db_execute_jobs(
                        "INSERT OR IGNORE INTO download_jobs (name, url, remote_size) VALUES (?, ?, ?)",
                        (nome_video, url, 0)
                    )
                    print(f"Trabalho registrado em downloads.db para Download 1: {nome_video}")
                    self.download_queue.append((nome_video, url, download_path))
                except Exception as e:
                    messagebox.showerror("Erro de Registro", f"Erro ao registrar trabalho de download para '{nome_video}': {e}")
                    continue # Pula este item se não conseguir registrar

            # Inicia o processamento da fila se não houver download em andamento
            if not self.is_downloading and self.download_queue:
                self.process_download_queue()
            elif not self.download_queue:
                messagebox.showinfo("Informação", "Nenhum vídeo válido para download.")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao iniciar download: {str(e)}")
            print(f"Erro detalhado: {str(e)}")

    def process_download_queue(self):
        """Processa a fila de downloads"""
        if not self.download_queue:
            self.is_downloading = False
            # Quando a fila em memória termina, verifica o DB por trabalhos pendentes.
            print("Fila de downloads em memória concluída. Verificando trabalhos pendentes...")
            self.verificar_e_retomar_pendentes()
            return # A verificação irá popular a fila novamente se necessário.

        self.is_downloading = True
        name, url, path = self.download_queue.pop(0)
        # Reseta o contador de retry para este download (nova tentativa bem-sucedida)
        self.reset_retry_count(name)
        Thread(target=self.download_video_with_callback, args=(name, url, path)).start()

    def download_video_with_callback(self, name, url, path):
        """Download com callback para processar a fila"""
        try:
            self.download_video(name, url, path)
        finally:
            self.root.after(1000, self.process_download_queue)

    def sanitize_directory_name(self, name):
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

    def _db_execute(self, query, params=()):
        """Executa uma query no banco de dados de forma thread-safe."""
        # Cria uma conexão local para a thread para evitar problemas de concorrência
        local_conn = sqlite3.connect('videos.db')
        local_cursor = local_conn.cursor()
        local_cursor.execute(query, params)
        local_conn.commit()
        local_conn.close()

    def _db_execute_jobs(self, query, params=()):
        """Executa uma query no banco de dados de downloads (jobs) de forma thread-safe."""
        # Conexão específica para o banco de dados de trabalhos de download
        local_conn = sqlite3.connect('downloads.db')
        local_cursor = local_conn.cursor()
        local_cursor.execute(query, params)
        local_conn.commit()
        local_conn.close()

    def download_video(self, name, url, path):
        """Realiza o download do vídeo"""
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file = os.path.join(log_dir, "aria2_downloads.log")

        try:
            self.cancel_download = False
            self.root.after(0, lambda: self.download_info_label.configure(text=f"Baixando: {name}"))

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

            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"Download iniciado: {name}\n")
                f.write(f"Data/Hora: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"URL: {url}\n")
                f.write(f"Destino: {file_path}\n")
                f.write(f"User-Agent: {self.user_agent.get()}\n")
                if self.dns_server.get().strip():
                    f.write(f"DNS Server: {self.dns_server.get()}\n")

            # Configuração do download com aria2
            options = {
                "dir": os.path.dirname(file_path),
                "out": os.path.basename(file_path),
                "max-connection-per-server": "16",
                "split": "16",
                "user-agent": self.user_agent.get(),
                "continue": "true",
                "max-concurrent-downloads": "1"
            }

            # Adiciona DNS se configurado
            dns_server = self.dns_server.get().strip()
            if dns_server:
                options["dns-server"] = dns_server

            try:
                # Inicia o download
                download = self.aria2.add_uris([url], options=options)

                # Log do início do download
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"Download ID: {download.gid}\n")
                    f.write("Status: Iniciado\n")
                
                size_updated = False # Flag para garantir que o tamanho seja atualizado apenas uma vez

                while not self.cancel_download and download.is_active:
                    try:
                        download.update()
                        downloaded = download.completed_length
                        total = download.total_length
                        
                        if total > 0:
                            # Atualiza o tamanho no DB assim que estiver disponível
                            if not size_updated:
                                self._db_execute_jobs("UPDATE download_jobs SET remote_size = ? WHERE name = ?", (total, name))
                                print(f"Tamanho atualizado em downloads.db para '{name}': {total} bytes")
                                size_updated = True

                            progress = (downloaded / total) * 100
                            speed = download.download_speed / (1024 * 1024)  # Converte para MB/s
                            
                            def update_progress_ui():
                                self.download_progress.set(progress)
                                self.progress_label.configure(text=f"{progress:.1f}%")
                                self.speed_label.configure(text=f"{speed:.1f} MB/s")
                            self.root.after(0, update_progress_ui)

                            # Log do progresso a cada 5%
                            if int(progress) % 5 == 0:
                                with open(log_file, "a", encoding="utf-8") as f:
                                    f.write(f"Progresso: {progress:.1f}% - Velocidade: {speed:.1f} MB/s\n")
                        
                        time.sleep(0.1)
                    except Exception as e:
                        with open(log_file, "a", encoding="utf-8") as f:
                            f.write(f"Erro durante o download: {str(e)}\n")
                        break

                if self.cancel_download:
                    download.remove(force=True)
                    self.root.after(0, lambda: self.download_info_label.configure(text="Download cancelado"))
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write("Status: Cancelado pelo usuário\n")
                    return
                else:
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write("Status: Concluído com sucesso\n")
                        f.write(f"Tamanho final: {total/(1024*1024):.2f} MB\n")

                    # Se o tamanho remoto nunca foi atualizado (total==0 ou size_updated False), tenta ajustar
                    try:
                        if not size_updated:
                            if os.path.exists(file_path):
                                final_size = os.path.getsize(file_path)
                                self._db_execute_jobs("UPDATE download_jobs SET remote_size = ? WHERE name = ?", (final_size, name))
                                print(f"Tamanho final detectado localmente para '{name}': {final_size} bytes")
                    except Exception:
                        pass

                    # Verifica de fato se o arquivo final existe e tem tamanho esperado antes de remover do DB
                    remove_job = False
                    try:
                        if os.path.exists(file_path):
                            final_size = os.path.getsize(file_path)
                            if total and final_size >= total:
                                remove_job = True
                            elif not total:
                                # Se total não informado, consideramos como concluído se arquivo existir e maior que zero
                                remove_job = final_size > 0
                        else:
                            remove_job = False
                    except Exception:
                        remove_job = False

                    if remove_job:
                        # OBS: não removemos o job imediatamente aqui para evitar perda de registro
                        # se a fila for interrompida no meio de vários downloads. A limpeza e
                        # verificação final serão feitas por `verificar_e_retomar_pendentes()`
                        # quando toda a fila de downloads em memória terminar.
                        # Se quiser comportamento antigo, descomente a linha abaixo.
                        # self._db_execute_jobs("DELETE FROM download_jobs WHERE name = ?", (name,))
                        pass
                        
                        # Incrementa contador de downloads realizados com sucesso
                        self.estatisticas['downloads_realizados'] += 1

                    # Tenta limpar o registro do aria2 e arquivos de controle (.aria2 / .aria)
                    try:
                        try:
                            download.remove(force=True)
                        except Exception:
                            pass
                        # Remove arquivos de controle residuais na mesma pasta
                        try:
                            dirpath = os.path.dirname(file_path)
                            base = os.path.basename(file_path)
                            for fname in os.listdir(dirpath):
                                if fname.startswith(base) and (fname.endswith('.aria2') or fname.endswith('.aria')):
                                    try:
                                        os.remove(os.path.join(dirpath, fname))
                                    except Exception:
                                        pass
                        except Exception:
                            pass
                    except Exception:
                        # Falha na limpeza dos arquivos temporários não deve impedir o fluxo
                        pass

            except Exception as e:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"Erro fatal no download: {str(e)}\n")
                raise

        except Exception as e:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"Erro geral: {str(e)}\n")
            # Incrementa contador de erros
            self.estatisticas['erros_encontrados'] += 1
            messagebox.showerror("Erro", f"Erro ao baixar {name}: {e}")
        finally:
            def reset_progress_ui():
                self.download_progress.set(0.0)
                self.progress_label.configure(text="0%")
                self.speed_label.configure(text="0 MB/s")
                self.download_info_label.configure(text="")
            self.root.after(0, reset_progress_ui)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{'='*50}\n")

    def extract_content_info(self, name):
        """Extrai informações do conteúdo (nome e temporada)"""
        match = re.search(r"(.*?)\s*(S\d{2})\s*E\d{2}", name)
        if match:
            content_name = match.group(1).strip()
            season = match.group(2).strip()
            return content_name, season
        else:
            return name, None

    def cancel_current_download(self):
        """Cancela o download atual"""
        if hasattr(self, 'advanced_downloader') and self.advanced_downloader and self.advanced_downloader.is_downloading:
            # Cancela download avançado
            self.advanced_downloader.cancel_current_download()
            self.download_info_label.configure(text="Cancelando download...")
        elif self.is_downloading:
            # Cancela download normal
            self.cancel_download = True
            self.download_info_label.configure(text="Cancelando download...")

    def remover_item_fila(self, posicao):
        """Remove um item específico da fila de downloads"""
        try:
            # A posição na UI começa em 1, mas o índice da lista começa em 0
            index = posicao - 1
            if 0 <= index < len(self.download_queue):
                item_removido = self.download_queue.pop(index)
                print(f"Item removido da fila: {item_removido[0]}")
                return True
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao remover item da fila: {str(e)}")
        return False

    def toggle_unlimited_retries(self):
        """Alterna entre modo de tentativas limitadas e ilimitadas"""
        self.unlimited_retries = not self.unlimited_retries
        if self.unlimited_retries:
            self.btn_unlimited_retries.configure(
                text="✓ Tentativas Ilimitadas",
                fg_color=CORES_BOTOES['LIMPAR_RETOMADA']  # Vermelho para indicar ativo
            )
            messagebox.showinfo("Modo Ilimitado", "Downloads agora terão tentativas ilimitadas de retomada.\n\nClique novamente no botão para voltar ao modo padrão (5 ciclos de estagnação).")
        else:
            self.btn_unlimited_retries.configure(
                text="♾️ Tentativas Ilimitadas",
                fg_color=CORES_BOTOES['VER_FILA']  # Roxo padrão
            )
            messagebox.showinfo("Modo Padrão", "Downloads limitados a 5 ciclos de estagnação da fila.")

    def reset_retry_count(self, name):
        """Reseta o contador de tentativas para um download"""
        if name in self.download_retry_count:
            del self.download_retry_count[name]

    def update_stagnation_counter(self, current_queue_size):
        """
        Atualiza o contador de estagnação baseado no progresso da fila.

        Regras:
        - Se a quantidade de itens for DIFERENTE do ciclo anterior: reinicia contador para 5
        - Se a quantidade de itens for IGUAL à do ciclo anterior: decrementa contador
        - Ao chegar em 0: zera o contador para permitir novo ciclo futuro
        """
        if self.unlimited_retries:
            # Modo ilimitado: não controla estagnação
            self.last_queue_size = current_queue_size
            return

        if current_queue_size != self.last_queue_size and current_queue_size > 0:
            # Houve mudança na fila (aumento ou diminuição): reinicia o contador
            print(f"Mudança na fila ({self.last_queue_size} -> {current_queue_size}). Reiniciando contador de estagnação.")
            self.stagnation_counter = 5
        elif current_queue_size == self.last_queue_size and current_queue_size > 0:
            # Estagnação: decrementa o contador
            self.stagnation_counter -= 1
            print(f"Estagnação detectada ({current_queue_size} itens). Contador: {self.stagnation_counter}/5")

            # Ao chegar em 0, zera tudo para permitir novo ciclo futuro
            if self.stagnation_counter == 0:
                print("Contador atingiu 0. Zera contador para permitir novo ciclo futuro.")
                self.last_queue_size = 0

        self.last_queue_size = current_queue_size

    def can_retry_download(self, name):
        """
        Verifica se um download pode ser reenfileirado baseado no contador de estagnação.

        Returns:
            bool: True se pode reenfileirar, False se atingiu o limite
        """
        if self.unlimited_retries:
            return True

        # Verifica se o contador de estagnação ainda permite tentativas
        if self.stagnation_counter <= 0:
            print(f"Download '{name}' atingiu o limite de estagnação da fila ({self.max_retries} ciclos).")
            return False

        return True

    def reset_stagnation_control(self):
        """
        Reseta completamente o controle de estagnação.
        Deve ser chamado quando o usuário inicia downloads manualmente.
        """
        self.last_queue_size = 0
        self.stagnation_counter = 5
        self.download_retry_count.clear()
        print("Controle de estagnação resetado. Contador: 5/5")

    def increment_retry_count(self, name):
        """
        Incrementa o contador de tentativas e retorna True se ainda pode tentar.
        NOTA: Esta função agora apenas registra o download no contador,
        a verificação de limite é feita por can_retry_download().
        """
        if self.unlimited_retries:
            return True

        if name not in self.download_retry_count:
            self.download_retry_count[name] = 0

        self.download_retry_count[name] += 1
        print(f"Download '{name}': tentativa {self.download_retry_count[name]}")
        return True

    def visualizar_fila_downloads(self):
        """Mostra a fila de downloads atual com interface simplificada"""
        try:
            # Cria janela de visualização
            queue_window = ctk.CTkToplevel(self.root)
            queue_window.title("Fila de Downloads - Palantir")
            queue_window.geometry("800x500")
            queue_window.resizable(True, True)

            # Configura a janela como modal de forma mais segura
            queue_window.transient(self.root)
            try:
                queue_window.grab_set()
            except tk.TclError:
                pass

            # Frame principal
            main_frame = ctk.CTkFrame(queue_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Título
            title_label = ctk.CTkLabel(main_frame, text="Fila de Downloads",
                                     font=ctk.CTkFont(size=16, weight="bold"))
            title_label.pack(pady=(0, 10))

            # Frame para informações gerais
            info_frame = ctk.CTkFrame(main_frame)
            info_frame.pack(fill=tk.X, padx=5, pady=5)

            # Informações da fila
            total_items = len(self.download_queue)
            status = "Processando" if self.is_downloading else "Aguardando"

            info_text = f"Total de itens na fila: {total_items} | Status: {status}"
            info_label = ctk.CTkLabel(info_frame, text=info_text, font=ctk.CTkFont(size=12))
            info_label.pack(pady=5)

            # Frame para a lista de downloads
            list_frame = ctk.CTkFrame(main_frame)
            list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            # Treeview para mostrar a fila
            queue_tree = ttk.Treeview(list_frame, columns=("posicao", "nome", "url", "pasta"), show="headings", height=15)
            queue_tree.heading("posicao", text="Posição")
            queue_tree.heading("nome", text="Nome do Vídeo")
            queue_tree.heading("url", text="URL")
            queue_tree.heading("pasta", text="Pasta de Destino")

            queue_tree.column("posicao", width=60, anchor="center")
            queue_tree.column("nome", width=250, anchor="w")
            queue_tree.column("url", width=200, anchor="w")
            queue_tree.column("pasta", width=150, anchor="w")

            # Scrollbar para o treeview
            queue_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=queue_tree.yview)
            queue_tree.configure(yscrollcommand=queue_scrollbar.set)

            queue_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            queue_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

            # Adiciona os itens da fila ao treeview
            for i, (nome, url, pasta) in enumerate(self.download_queue, 1):
                # Trunca o nome se for muito longo
                nome_display = nome[:35] + "..." if len(nome) > 35 else nome
                # Trunca a URL se for muito longa
                url_display = url[:30] + "..." if len(url) > 30 else url
                # Trunca o caminho se for muito longo
                pasta_display = os.path.basename(pasta)[:20] + "..." if len(os.path.basename(pasta)) > 20 else os.path.basename(pasta)

                queue_tree.insert("", tk.END, values=(i, nome_display, url_display, pasta_display))

            # Frame para botões simplificado
            button_frame = ctk.CTkFrame(main_frame)
            button_frame.pack(fill=tk.X, padx=5, pady=5)

            # Botão para atualizar
            def atualizar_fila():
                """Atualiza a visualização da fila"""
                # Limpa o treeview
                for item in queue_tree.get_children():
                    queue_tree.delete(item)

                # Atualiza informações
                total_items = len(self.download_queue)
                status = "Processando" if self.is_downloading else "Aguardando"
                info_text = f"Total de itens na fila: {total_items} | Status: {status}"
                info_label.configure(text=info_text)

                # Adiciona os itens atualizados
                for i, (nome, url, pasta) in enumerate(self.download_queue, 1):
                    nome_display = nome[:35] + "..." if len(nome) > 35 else nome
                    url_display = url[:30] + "..." if len(url) > 30 else url
                    pasta_display = os.path.basename(pasta)[:20] + "..." if len(os.path.basename(pasta)) > 20 else os.path.basename(pasta)

                    queue_tree.insert("", tk.END, values=(i, nome_display, url_display, pasta_display))

            atualizar_button = ctk.CTkButton(
                button_frame,
                text="🔄 Atualizar",
                command=atualizar_fila,
                fg_color=CORES_BOTOES['ATUALIZAR'],
                hover_color=CORES_BOTOES['ATUALIZAR_HOVER']
            )
            atualizar_button.pack(side=tk.LEFT, padx=5)

            # Botão para remover item selecionado
            def remover_selecionado():
                selected = queue_tree.selection()
                if not selected:
                    messagebox.showwarning("Aviso", "Selecione um item para remover.")
                    return

                # Coleta as posições de todos os itens selecionados e ordena de forma decrescente
                # para evitar que a remoção de um item altere os índices dos próximos
                posicoes = sorted([int(queue_tree.item(item, 'values')[0]) for item in selected], reverse=True)

                removidos = 0
                for posicao in posicoes:
                    if self.remover_item_fila(posicao):
                        removidos += 1

                if removidos > 0:
                    atualizar_fila()
                    messagebox.showinfo("Sucesso", f"{removidos} item(ns) removido(s) da fila.")

            remover_button = ctk.CTkButton(
                button_frame,
                text="🗑️ Remover Sel.",
                command=remover_selecionado,
                fg_color=CORES_BOTOES['REMOVER_SEL'],
                hover_color=CORES_BOTOES['REMOVER_SEL_HOVER']
            )
            remover_button.pack(side=tk.LEFT, padx=5)

            # Botão para fechar
            fechar_button = ctk.CTkButton(
                button_frame,
                text="❌ Fechar",
                command=queue_window.destroy,
                fg_color=CORES_BOTOES['FECHAR'],
                hover_color=CORES_BOTOES['FECHAR_HOVER']
            )
            fechar_button.pack(side=tk.RIGHT, padx=5)

            # Atualização automática a cada 3 segundos
            def auto_atualizar():
                if queue_window.winfo_exists():
                    # Só atualiza automaticamente se o usuário não estiver selecionando nada
                    if not queue_tree.selection():
                        atualizar_fila()
                    queue_window.after(3000, auto_atualizar)

            queue_window.after(3000, auto_atualizar)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir visualizador de fila: {str(e)}")

    def clean_folders(self):
        """Limpa as pastas de download"""
        try:
            # Primeira confirmação
            if not messagebox.askyesno("Confirmar Limpeza", 
                "Tem certeza que deseja limpar todas as pastas de download?\n\n"
                "Esta ação irá remover todos os arquivos de vídeo (.mp4, .mkv, .avi, .mov) "
                "e pastas vazias do diretório de download."):
                return

            # Segunda confirmação com aviso mais forte
            if not messagebox.askyesno("ATENÇÃO - Confirmação Final", 
                "⚠️ ATENÇÃO: Esta ação NÃO pode ser desfeita!\n\n"
                "Você está prestes a remover permanentemente:\n"
                "• Todos os arquivos de vídeo\n"
                "• Todas as pastas vazias\n"
                "• Todo o conteúdo do diretório: " + self.download_path.get() + "\n\n"
                "Deseja realmente continuar?"):
                return

            base_dir = self.download_path.get()
            items_to_remove = []
            
            # Contador para mostrar progresso
            total_items = 0
            removed_items = 0
            
            for root, dirs, files in os.walk(base_dir):
                for file in files:
                    if file.endswith(('.mp4', '.mkv', '.avi', '.mov')):
                        items_to_remove.append(os.path.join(root, file))
                        total_items += 1
                
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    if not os.listdir(dir_path):
                        items_to_remove.append(dir_path)
                        total_items += 1
            
            # Terceira confirmação mostrando quantidade de itens
            if total_items > 0:
                if not messagebox.askyesno("Confirmação Final", 
                    f"Serão removidos {total_items} itens:\n"
                    f"• {len([x for x in items_to_remove if os.path.isfile(x)])} arquivos\n"
                    f"• {len([x for x in items_to_remove if os.path.isdir(x)])} pastas vazias\n\n"
                    "Deseja prosseguir com a limpeza?"):
                    return
            
            # Barra de progresso
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Limpando Pastas")
            progress_window.transient(self.root)
            
            def setup_progress_window():
                progress_window.geometry("400x150")
                def wait_and_grab():
                    if progress_window.winfo_viewable():
                        progress_window.grab_set()
                    else:
                        progress_window.after(50, wait_and_grab)
                progress_window.after(0, wait_and_grab)
            # Centraliza a janela
            progress_window.update_idletasks()
            width = progress_window.winfo_width()
            height = progress_window.winfo_height()
            x = (progress_window.winfo_screenwidth() // 2) - (width // 2)
            y = (progress_window.winfo_screenheight() // 2) - (height // 2)
            progress_window.geometry(f'+{x}+{y}')
            
            self.root.after_idle(setup_progress_window) # Agendado para próxima iteração do mainloop
            
            # Frame para progresso
            progress_frame = ctk.CTkFrame(progress_window)
            progress_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Label de status
            status_label = ctk.CTkLabel(progress_frame, text="Iniciando limpeza...")
            status_label.pack(pady=10)
            
            # Barra de progresso
            progress_bar = ctk.CTkProgressBar(progress_frame)
            progress_bar.pack(fill=tk.X, padx=10, pady=5)
            progress_bar.set(0)
            
            # Label de contagem
            count_label = ctk.CTkLabel(progress_frame, text="0/0 itens processados")
            count_label.pack(pady=5)
            
            # Processa os itens
            for i, item in enumerate(items_to_remove):
                try:
                    if os.path.isfile(item):
                        os.remove(item)
                    elif os.path.isdir(item):
                        os.rmdir(item)
                    removed_items += 1
                    
                    # Atualiza a interface
                    progress = (i + 1) / total_items
                    progress_bar.set(progress)
                    count_label.configure(text=f"{i + 1}/{total_items} itens processados")
                    status_label.configure(text=f"Removendo: {os.path.basename(item)}")
                    progress_window.update()
                    
                except Exception as e:
                    print(f"Erro ao remover {item}: {e}")
            
            # Fecha a janela de progresso
            self.root.after(0, progress_window.destroy)
            
            # Mensagem final
            if removed_items > 0:
                messagebox.showinfo("Sucesso", 
                    f"Limpeza concluída com sucesso!\n\n"
                    f"Total de itens removidos: {removed_items}\n"
                    f"• {len([x for x in items_to_remove if os.path.isfile(x)])} arquivos\n"
                    f"• {len([x for x in items_to_remove if os.path.isdir(x)])} pastas vazias")
            else:
                messagebox.showinfo("Informação", "Nenhum item foi encontrado para remover.")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao limpar pastas: {e}")

    def criar_interface(self):
        """Cria a interface gráfica do programa"""
        # Frame principal
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # --- 1. BARRA SUPERIOR ---
        self.top_frame = ctk.CTkFrame(self.main_frame)
        self.top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Grupo 1: Carregamento
        loading_group = ctk.CTkFrame(self.top_frame)
        loading_group.pack(side=tk.LEFT, padx=5, pady=5)




        # Grupo de carregamento
        self.btn_adicionar_links = ctk.CTkButton(
            loading_group,
            text="Links",
            command=self.load_multiple_links,
            fg_color="#e74c3c",  # Vermelho
            hover_color="#c0392b"  # Vermelho escuro para hover
        )
        self.btn_adicionar_links.pack(side=tk.LEFT, padx=5)

        self.btn_editar_urls = ctk.CTkButton(
            loading_group,
            text="Editor URLs",
            command=self.editar_urls_banco,
            fg_color="#e67e22",  # Laranja
            hover_color="#d35400"  # Laranja escuro para hover
        )
        self.btn_editar_urls.pack(side=tk.LEFT, padx=5)

        # Separador para agrupar funcionalidades de carregamento
        ttk.Separator(loading_group, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)

        # Grupo 2: Pasta de Download
        download_folder_group = ctk.CTkFrame(self.top_frame)
        download_folder_group.pack(side=tk.LEFT, padx=5, pady=5)

        self.download_path_label = ctk.CTkLabel(download_folder_group, text="Pasta de Download:  ")
        self.download_path_label.pack(side=tk.LEFT, padx=(5, 2))

        self.download_path_entry = ctk.CTkEntry(
            download_folder_group,
            textvariable=self.download_path
        )
        self.download_path_entry.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)

        self.btn_browse = ctk.CTkButton(
            download_folder_group,
            text="Selecionar",
            command=self.browse_directory,
            fg_color="#9b59b6",  # Roxo
            hover_color="#8e44ad",  # Roxo escuro para hover
            width=40
        )
        self.btn_browse.pack(side=tk.LEFT, padx=5)

        # Grupo 3: Rede
        network_group = ctk.CTkFrame(self.top_frame)
        network_group.pack(side=tk.LEFT, padx=5, pady=5)

        self.ua_label = ctk.CTkLabel(network_group, text="User-Agent:  ")
        self.ua_label.pack(side=tk.LEFT, padx=(5, 2))

        self.ua_combo = ctk.CTkOptionMenu(
            network_group,
            values=[
                "Mozilla/5.0",
                "MPV/1.0",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Lavf/58.76.100",
                "Mozilla/5.0 (SMART-TV; Linux; Tizen 2.4.0) AppleWebkit/538.1",
                "XCIPTV-v5.0.1",
                "XCIPTV-v7.0",
                "samsung-agent/1.1",
                "Dalvik/2.1.0 (Linux; U; Android 11.1; TV BOX Build/QP1A.191105.004)",
                "Custom..."
            ],
            command=self.change_user_agent,
            fg_color="#3498db",
            button_color="#2980b9",
            button_hover_color="#1f6aa5",
            dropdown_fg_color="#2b2b2b",
            dropdown_hover_color="#3d3d3d",
            dropdown_text_color="white"
        )
        self.ua_combo.pack(side=tk.LEFT, padx=(0, 5))
        self.ua_combo.set(self.user_agent.get())

        self.dns_label = ctk.CTkLabel(network_group, text="DNS:")
        self.dns_label.pack(side=tk.LEFT, padx=(5, 2))

        self.dns_entry = ctk.CTkEntry(
            network_group,
            textvariable=self.dns_server,
            placeholder_text="Ex: 8.8.8.8"
        )
        self.dns_entry.pack(side=tk.LEFT, padx=5)

        # Separador para agrupar configurações de rede
        ttk.Separator(network_group, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)

        # Grupo 4: Configuração Final
        final_config_group = ctk.CTkFrame(self.top_frame)
        final_config_group.pack(side=tk.LEFT, padx=5, pady=5)

        self.theme_label = ctk.CTkLabel(final_config_group, text="Tema: ")
        self.theme_label.pack(side=tk.LEFT, padx=(5, 2))

        # Garante que a lista de temas está ordenada
        sorted_themes = sorted(self.available_themes)
        self.theme_menu = ctk.CTkOptionMenu(
            final_config_group,
            values=sorted_themes,
            command=self.change_theme,
            fg_color="#9b59b6",  # Roxo
            button_color="#8e44ad",  # Roxo escuro para o botão
            button_hover_color="#7d3c98",  # Roxo mais escuro para hover do botão
            dropdown_fg_color="#2b2b2b",  # Cor de fundo do dropdown
            dropdown_hover_color="#3d3d3d",  # Cor de hover dos itens do dropdown
            dropdown_text_color="white"  # Cor do texto do dropdown
        )
        self.theme_menu.pack(side=tk.LEFT, padx=(0, 5))
        # Define explicitamente o tema atual do config.json
        self.theme_menu.set(self.active_theme)
        
        self.btn_save_config = ctk.CTkButton(
            final_config_group,
            text=" Salvar",
            command=self.save_config,
            fg_color="#2ecc71",  # Verde
            hover_color="#27ae60",  # Verde escuro para hover
            width=40
        )
        self.btn_save_config.pack(side=tk.LEFT, padx=5)

        # Botão para limpar o banco de dados
        self.btn_limpar_banco = ctk.CTkButton(
            final_config_group,
            text="Limpar banco",
            command=self.limpar_banco,
            fg_color="#e74c3c",  # Vermelho
            hover_color="#c0392b",  # Vermelho escuro para hover
            width=80
        )
        self.btn_limpar_banco.pack(side=tk.LEFT, padx=5)

        # Separador para agrupar configurações finais
        ttk.Separator(final_config_group, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)

        self.ua_entry = ctk.CTkEntry(
            network_group,
            placeholder_text="Digite o User-Agent personalizado"
        )
        
        # --- FIM DA BARRA SUPERIOR ---
        self.progress_frame = ctk.CTkFrame(self.main_frame)
        self.progress_frame.pack(fill=tk.X, padx=5, pady=5)

        # Frame para pesquisa e barra de progresso
        self.search_progress_frame = ctk.CTkFrame(self.progress_frame)
        self.search_progress_frame.pack(fill=tk.X, padx=5, pady=5)

        # Frame para pesquisa (agora dentro do frame de progresso)
        self.search_frame = ctk.CTkFrame(self.search_progress_frame)
        self.search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Campo de pesquisa
        self.search_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="Digite o termo de pesquisa"
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Campo de pesquisa por categoria
        self.category_search_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="Busca por Categoria"
        )
        self.category_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Campo de pesquisa adicional para cruzamento de informações
        self.extra_search_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="Busca adicional (ano, qualidade, etc.)"
        )
        self.extra_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Menu suspenso para seleção de tipo (Todos/Filme/Série)
        self.type_search_option = ctk.CTkOptionMenu(
            self.search_frame,
            values=["Todos", "Filme", "Série"],
            command=self.atualizar_busca_tipo,
            fg_color="#3498db",
            button_color="#2980b9",
            button_hover_color="#1f6aa5",
            dropdown_fg_color="#2b2b2b",
            dropdown_hover_color="#3d3d3d",
            dropdown_text_color="white"
        )
        self.type_search_option.set("Todos")  # Valor padrão
        self.type_search_option.pack(side=tk.LEFT, padx=5)

        # Botão Pesquisar
        self.btn_pesquisar = ctk.CTkButton(
            self.search_frame,
            text="Pesquisar",
            command=self.filtrar_resultados,
            fg_color="#3498db",
            hover_color="#2980b9"
        )
        self.btn_pesquisar.pack(side=tk.LEFT, padx=5)

        # Botão para limpar todos os campos de pesquisa
        self.btn_limpar_campos = ctk.CTkButton(
            self.search_frame,
            text="X",
            command=self.limpar_campos_pesquisa,
            fg_color="#e74c3c",  # Vermelho
            hover_color="#c0392b",  # Vermelho escuro para hover
            width=40
        )
        self.btn_limpar_campos.pack(side=tk.LEFT, padx=5)

        # Frame para barra de progresso e informações
        self.progress_bar_frame = ctk.CTkFrame(self.search_progress_frame)
        self.progress_bar_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Barra de progresso
        self.progress_bar = ctk.CTkProgressBar(self.progress_bar_frame, variable=self.download_progress)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        # Label de porcentagem (agora ao lado da barra)
        self.progress_label = ctk.CTkLabel(self.progress_bar_frame, text="0%", width=50)
        self.progress_label.pack(side=tk.LEFT, padx=(0, 5))

        # Labels de velocidade e informações
        self.speed_label = ctk.CTkLabel(self.progress_bar_frame, text="0 MB/s")
        self.speed_label.pack(side=tk.LEFT, padx=5)
        
        self.download_info_label = ctk.CTkLabel(self.progress_bar_frame, text="")
        self.download_info_label.pack(side=tk.LEFT, padx=5)

        # Botão Cancelar (agora após as informações)
        self.btn_cancel = ctk.CTkButton(
            self.progress_bar_frame,
            text="Cancelar",
            command=self.cancel_current_download,
            fg_color=CORES_BOTOES['LIMPAR'],  # Vermelho
            hover_color=CORES_BOTOES['LIMPAR_HOVER'],  # Vermelho escuro para hover
            width=80
        )
        self.btn_cancel.pack(side=tk.LEFT, padx=(0, 5))

        # Frame para conteúdo (lista e player)
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Frame esquerdo para lista
        self.left_frame = ctk.CTkFrame(self.content_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # --- 2. BARRA DE AÇÕES ---
        self.list_buttons_frame = ctk.CTkFrame(self.left_frame)
        self.list_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Ordem: Abrir, Copiar, Downloads, Fila, Checkboxes, Organizar/Limpar, Player, Suporte
        self.btn_abrir = ctk.CTkButton(
            self.list_buttons_frame,
            text=" Abrir",
            command=self.open_selected_in_browser,
            fg_color=CORES_BOTOES['ABRIR'],  # Azul claro
            hover_color=CORES_BOTOES['ABRIR_HOVER'],  # Azul escuro para hover
            width=40
        )
        self.btn_abrir.pack(side=tk.LEFT, padx=5)
        
        self.btn_copiar = ctk.CTkButton(
            self.list_buttons_frame,
            text="Copiar",
            command=self.copy_selected_link,
            fg_color=CORES_BOTOES['COPIAR'],  # Amarelo
            hover_color=CORES_BOTOES['COPIAR_HOVER'],  # Laranja para hover
            width=40
        )
        self.btn_copiar.pack(side=tk.LEFT, padx=5)
        
        # Grupo de downloads
        self.btn_download = ctk.CTkButton(
            self.list_buttons_frame,
            text="Download Aria",
            command=self.download_selected,
            fg_color=CORES_BOTOES['D1_ARIA'],  # Verde
            hover_color=CORES_BOTOES['D1_ARIA_HOVER']  # Verde escuro para hover
        )
        self.btn_download.pack(side=tk.LEFT, padx=5)

        # Botão para abrir submenu "Reserva"
        self.btn_reserva_menu = ctk.CTkButton(
            self.list_buttons_frame,
            text="Reserva ▼",
            command=self.abrir_submenu_reserva,
            fg_color=CORES_BOTOES['RESERVA'],  # Laranja escuro
            hover_color=CORES_BOTOES['RESERVA_HOVER']  # Laranja mais escuro para hover
        )
        self.btn_reserva_menu.pack(side=tk.LEFT, padx=5)

        # Separador para agrupar downloads
        ttk.Separator(self.list_buttons_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)

        # Grupo de organização
        self.btn_organizar = ctk.CTkButton(
            self.list_buttons_frame,
            text="Organizar",
            command=self.organize_folders,
            fg_color=CORES_BOTOES['ORGANIZAR'],  # Azul claro
            hover_color=CORES_BOTOES['ORGANIZAR_HOVER']  # Azul escuro para hover
        )
        self.btn_limpar = ctk.CTkButton(
            self.list_buttons_frame,
            text="Limpar",
            command=self.limpar_pastas,
            fg_color=CORES_BOTOES['LIMPAR'],  # Vermelho
            hover_color=CORES_BOTOES['LIMPAR_HOVER']  # Vermelho escuro para hover
        )
        self.btn_limpar.pack(side=tk.LEFT, padx=5)

        self.btn_organizar.pack(side=tk.LEFT, padx=5)

        # Botão para gerar M3U
        self.btn_gerar_m3u = ctk.CTkButton(
            self.list_buttons_frame,
            text="M3U",
            command=self.gerar_m3u_automatico,
            fg_color="#9b59b6",  # Roxo
            hover_color="#8e44ad",  # Roxo escuro para hover
            width=40
        )
        self.btn_gerar_m3u.pack(side=tk.LEFT, padx=5)

        # Botão para exibir estatísticas
        self.btn_estatisticas = ctk.CTkButton(
            self.list_buttons_frame,
            text="Estatísticas",
            command=self.mostrar_estatisticas,
            fg_color=CORES_BOTOES['ESTATISTICAS'],  # Roxo
            hover_color=CORES_BOTOES['ESTATISTICAS_HOVER'],  # Roxo escuro para hover
            width=80
        )
        self.btn_estatisticas.pack(side=tk.LEFT, padx=5)

        # Separador para agrupar organização
        ttk.Separator(self.list_buttons_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)

        # Grupo de player
        self.player_label = ctk.CTkLabel(self.list_buttons_frame, text="Player:")
        self.player_label.pack(side=tk.LEFT, padx=(5, 2))

        self.player_menu = ctk.CTkOptionMenu(
            self.list_buttons_frame,
            values=["MPV (Sistema)", "MPV AppImage", "VLC AppImage"], # Novas opções
            command=self.change_player,
            fg_color=CORES_BOTOES['PLAYER'],  # Verde
            button_color=CORES_BOTOES['PLAYER_HOVER'],  # Verde escuro para o botão
            button_hover_color="#219a52",  # Verde mais escuro para hover do botão
            dropdown_fg_color="#2b2b2b",  # Cor de fundo do dropdown
            dropdown_hover_color="#3d3d3d",  # Cor de hover dos itens do dropdown
            dropdown_text_color="white"  # Cor do texto do dropdown
        )
        self.player_menu.pack(side=tk.LEFT, padx=5)
        self.player_menu.set("MPV (Sistema)")  # MPV (Sistema) como padrão

        # Botão para visualizar fila de downloads
        self.btn_ver_fila = ctk.CTkButton(
            self.list_buttons_frame,
            text="🔄 Ver Fila",
            command=self.visualizar_fila_downloads,
            fg_color=CORES_BOTOES['VER_FILA'],  # Roxo
            hover_color=CORES_BOTOES['VER_FILA_HOVER'],  # Roxo escuro
            width=80
        )
        self.btn_ver_fila.pack(side=tk.LEFT, padx=5)

        # Botão para limpar fila de retomada
        def limpar_fila_retomada():
            """Limpa a tabela de trabalhos de download."""
            if messagebox.askyesno("Confirmar", "Tem certeza que deseja limpar todos os trabalhos de download pendentes?\n\nIsso removerá a capacidade de retomar downloads que falharam ou foram interrompidos."):
                try:
                    self._db_execute_jobs("DELETE FROM download_jobs")
                    messagebox.showinfo("Sucesso", "A fila de retomada de downloads foi limpa.")
                    # Reseta contadores de retry
                    self.download_retry_count.clear()
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao limpar a fila de retomada: {e}")

        self.btn_limpar_retomada = ctk.CTkButton(
            self.list_buttons_frame,
            text="🗑️ Limpar Retomada",
            command=limpar_fila_retomada,
            fg_color=CORES_BOTOES['LIMPAR_RETOMADA'],  # Vermelho
            hover_color=CORES_BOTOES['LIMPAR_RETOMADA_HOVER'],
            width=110
        )
        self.btn_limpar_retomada.pack(side=tk.LEFT, padx=5)

        # Botão para visualizar pendentes
        def visualizar_db_retomada():
            """Abre uma janela simplificada para visualizar o conteúdo de downloads.db"""
            try:
                db_window = ctk.CTkToplevel(self.root)
                db_window.title("Downloads Pendentes")
                db_window.geometry("700x400")
                db_window.transient(self.root)
                try:
                    db_window.grab_set()
                except tk.TclError:
                    pass

                db_frame = ctk.CTkFrame(db_window)
                db_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

                tree = ttk.Treeview(db_frame, columns=("Nome", "Tamanho"), show="headings", height=12)
                tree.heading("Nome", text="Nome do Vídeo"); tree.column("Nome", width=400, anchor="w")
                tree.heading("Tamanho", text="Tamanho (MB)"); tree.column("Tamanho", width=150, anchor="e")

                scrollbar = ttk.Scrollbar(db_frame, orient="vertical", command=tree.yview)
                tree.configure(yscrollcommand=scrollbar.set)
                tree.pack(side=tk.LEFT, fill="both", expand=True, pady=5)
                scrollbar.pack(side="right", fill="y", pady=5)

                # Carrega os dados
                conn = sqlite3.connect('downloads.db')
                cursor = conn.cursor()
                cursor.execute("SELECT name, remote_size FROM download_jobs ORDER BY name")
                records = cursor.fetchall()
                conn.close()

                for name, remote_size in records:
                    size_mb = f"{(remote_size / (1024*1024)):.2f}" if remote_size and remote_size > 0 else "0.00"
                    tree.insert("", "end", values=(name, size_mb))

                if not records:
                    tree.insert("", "end", values=("Nenhum download pendente", ""))

            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível ler 'downloads.db': {e}")

        self.btn_pendentes = ctk.CTkButton(
            self.list_buttons_frame,
            text="📋 Pendentes",
            command=visualizar_db_retomada,
            fg_color=CORES_BOTOES['PENDENTES'],
            hover_color=CORES_BOTOES['PENDENTES_HOVER'],
            width=80
        )
        self.btn_pendentes.pack(side=tk.LEFT, padx=5)

        self.btn_unlimited_retries = ctk.CTkButton(
            self.list_buttons_frame,
            text="♾️ Tentativas Ilimitadas",
            command=self.toggle_unlimited_retries,
            fg_color=CORES_BOTOES['VER_FILA'],  # Roxo
            hover_color=CORES_BOTOES['VER_FILA_HOVER'],  # Roxo escuro para hover
            width=120
        )
        self.btn_unlimited_retries.pack(side=tk.LEFT, padx=5)

        self.btn_change_api_key = ctk.CTkButton(
            self.list_buttons_frame,
            text="Chave de api",
            command=self.change_tmdb_api_key,
            fg_color=CORES_BOTOES['API_KEY'],  # Amarelo
            hover_color=CORES_BOTOES['API_KEY_HOVER'],  # Laranja para hover
            width=40
        )
        self.btn_change_api_key.pack(side=tk.LEFT, padx=5)

        self.btn_change_url = ctk.CTkButton(
            self.list_buttons_frame,
            text="URL",
            command=self.change_m3u_base_url,
            fg_color=CORES_BOTOES['ABRIR'],  # Azul
            hover_color=CORES_BOTOES['ABRIR_HOVER'],  # Azul escuro para hover
            width=40
        )
        self.btn_change_url.pack(side=tk.LEFT, padx=5)

        # Separador final
        ttk.Separator(self.list_buttons_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)

        # Treeview para resultados
        self.tree = ttk.Treeview(
            self.left_frame,
            columns=("Nº", "Nome", "Tipo", "Temporada", "Servidor", "Categoria", "Link de Origem"),
            show="headings",
            style="Custom.Treeview"
        )
        
        # Configurar estilo personalizado para a Treeview
        style = ttk.Style()
        style.configure("Custom.Treeview",
            background="#2b2b2b",
            foreground="white",
            fieldbackground="#2b2b2b",
            rowheight=25,  # Reduzido de 30 para 25
            font=('Segoe UI', 9)  # Reduzido de 10 para 9
        )
        
        style.configure("Custom.Treeview.Heading",
            background="#1f538d",
            foreground="white",
            relief="flat",
            font=('Segoe UI', 9, 'bold')  # Reduzido de 10 para 9
        )
        
        # Simplificado o mapeamento de estilos
        style.map("Custom.Treeview",
            background=[('selected', '#3c9bf7')],
            foreground=[('selected', 'white')]
        )
        
        # Configurar colunas
        self.tree.heading("Nº", text="Nº")
        self.tree.heading("Nome", text="Nome", command=lambda: self.sort_treeview("Nome"))
        self.tree.heading("Tipo", text="Tipo", command=lambda: self.sort_treeview("Tipo"))
        self.tree.heading("Temporada", text="Temporada", command=lambda: self.sort_treeview("Temporada"))
        self.tree.heading("Servidor", text="Servidor", command=lambda: self.sort_treeview("Servidor"))
        self.tree.heading("Categoria", text="Categoria", command=lambda: self.sort_treeview("Categoria"))
        self.tree.heading("Link de Origem", text="Link de Origem", command=lambda: self.sort_treeview("Link de Origem"))
        
        # Configurar larguras das colunas
        self.tree.column("Nº", width=40, anchor="center", minwidth=40)  # Reduzido de 50 para 40
        self.tree.column("Nome", width=250, anchor="w", minwidth=200)  # Reduzido de 300 para 250
        self.tree.column("Tipo", width=80, anchor="center", minwidth=80)  # Reduzido de 100 para 80
        self.tree.column("Temporada", width=80, anchor="center", minwidth=80)  # Reduzido de 100 para 80
        self.tree.column("Servidor", width=120, anchor="center", minwidth=120)  # Reduzido de 150 para 120
        self.tree.column("Categoria", width=120, anchor="center", minwidth=120)  # Reduzido de 150 para 120
        self.tree.column("Link de Origem", width=250, anchor="w", minwidth=200)  # Reduzido de 300 para 250
        
        # Scrollbar para a lista
        scrollbar = ttk.Scrollbar(self.left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Posicionar Treeview e Scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind eventos
        self.search_entry.bind("<Return>", lambda e: self.filtrar_resultados())
        self.category_search_entry.bind("<Return>", lambda e: self.filtrar_resultados())
        self.extra_search_entry.bind("<Return>", lambda e: self.filtrar_resultados())
        self.tree.bind("<Double-Button-1>", self.on_tree_double_click)
        
        # Variável para controlar a ordenação
        self.sort_reverse = False
        self.last_sort_column = None

    def atualizar_busca_tipo(self, choice):
        """Atualiza a busca quando o tipo é alterado"""
        # Dispara a busca automaticamente quando o tipo é alterado
        self.filtrar_resultados()

    def limpar_campos_pesquisa(self):
        """Limpa todos os campos de pesquisa"""
        self.search_entry.delete(0, tk.END)
        self.category_search_entry.delete(0, tk.END)
        self.extra_search_entry.delete(0, tk.END)
        self.type_search_option.set("Todos")  # Volta para o valor padrão
        # Atualiza a lista para mostrar todos os itens novamente
        self.filtrar_resultados()

    def on_tree_double_click(self, event):
        """Manipula duplo clique na treeview"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
            
        url = self.get_url_from_selection(selected_items[0])
        if url:
            self.play_video(url)
        else:
            messagebox.showinfo("Aviso", "URL não encontrada para este vídeo.")
        
    def play_video(self, url):
        """Reproduz um vídeo usando o player selecionado em um subprocesso"""
        try:
            # Encerra o processo do player anterior se estiver rodando
            if self.mpv_process and self.mpv_process.poll() is None:
                self.mpv_process.terminate()
                self.mpv_process.wait() # Aguarda a terminação
            
            player_executable = ""
            player_args = []

            if self.player_type == "MPV AppImage":
                player_executable = self.mpv_appimage_path
                player_args = [player_executable, url, '--no-config']
            elif self.player_type == "VLC AppImage":
                player_executable = self.vlc_path
                player_args = [player_executable, url, '--fullscreen', '--no-qt-privacy-ask'] # Adiciona opções para VLC
            elif self.player_type == "MPV (Sistema)":
                player_executable = self.mpv_path
                player_args = [player_executable, url, '--no-config']
            else:
                messagebox.showerror("Erro", "Nenhum player selecionado ou player inválido.")
                return

            # Verifica se o executável do player existe e tem permissão de execução
            if not os.path.exists(player_executable):
                messagebox.showerror("Erro", f"Player não encontrado: {player_executable}")
                return
            if not os.access(player_executable, os.X_OK):
                # Tenta adicionar permissão de execução se for um AppImage
                if player_executable.endswith(".AppImage"):
                    try:
                        os.chmod(player_executable, 0o755) # Adiciona permissão de execução
                        print(f"DEBUG: Permissão de execução adicionada a {player_executable}")
                    except Exception as e:
                        messagebox.showerror("Erro", f"Sem permissão de execução para o player: {player_executable}\nErro: {e}")
                        return
                else:
                    messagebox.showerror("Erro", f"Sem permissão de execução para o player: {player_executable}")
                    return

            print(f"DEBUG: URL original recebida em play_video: '{url}'")
            # Sanitiza a URL para remover aspas simples e duplas que podem causar problemas
            sanitized_url = url.replace("'", "").replace('"', '')
            print(f"DEBUG: URL sanitizada em play_video: '{sanitized_url}'")
            
            # Substitui a URL original pela sanitizada nos argumentos
            # Assumindo que a URL é sempre o segundo argumento para MPV e VLC
            player_args[1] = sanitized_url

            print(f"DEBUG: Tentando iniciar {self.player_type} com argumentos: {player_args}")
            
            # Inicia o processo do player
            self.mpv_process = subprocess.Popen(player_args) # Reutiliza self.mpv_process para qualquer player
            print(f"DEBUG: {self.player_type} iniciado. PID: {self.mpv_process.pid}")
            
        except FileNotFoundError:
            messagebox.showerror("Erro", f"{self.player_type} não encontrado. Por favor, certifique-se de que o player está instalado e no seu PATH ou na pasta 'Players'.")
            print(f"DEBUG: Erro FileNotFoundError ao iniciar {self.player_type}.")
            traceback.print_exc()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao reproduzir vídeo com {self.player_type}: {str(e)}")
            print(f"DEBUG: Erro geral ao iniciar {self.player_type}: {str(e)}")
            traceback.print_exc()
    
    def conectar_banco(self):
        """Conecta ao banco de dados"""
        try:
            # Se já existe uma conexão ativa, retorna True
            if self.conn is not None:
                return True

            print("Tentando conectar ao banco de dados...")
            db_path = os.path.abspath('videos.db')
            print(f"Caminho do banco: {db_path}")
            
            # Verifica se o diretório tem permissão de escrita
            db_dir = os.path.dirname(db_path)
            if not os.access(db_dir, os.W_OK):
                print(f"Sem permissão de escrita no diretório: {db_dir}")
                messagebox.showerror("Erro", "Sem permissão de escrita no diretório do banco de dados")
                return False

            self.conn = sqlite3.connect('videos.db')
            self.cursor = self.conn.cursor()
            
            # Verifica se a tabela existe
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    type TEXT NOT NULL,
                    season TEXT NOT NULL,
                    username TEXT,
                    category TEXT,
                    downloaded INTEGER DEFAULT 0
                )
            """)
            self.conn.commit()
            
            print("Conexão com o banco estabelecida com sucesso")
            return True
            
        except Exception as e:
            print(f"Erro ao conectar ao banco: {str(e)}")
            messagebox.showerror("Erro", f"Erro ao conectar ao banco de dados: {str(e)}")
            return False




    def extrair_servidor_e_username(self, url):
        """Extrai o nome do servidor e username da URL"""
        try:
            # Remove o protocolo (http:// ou https://)
            url_sem_protocolo = re.sub(r'^https?://', '', url)
            
            # Divide a URL em partes
            partes = url_sem_protocolo.split('/')
            
            # Pega o servidor (primeira parte)
            servidor = partes[0].split(':')[0]
            
            # Tenta extrair o username da URL
            username = "N/A"
            if "username=" in url:
                # Procura por username= seguido de números
                match = re.search(r'username=(\d+)', url)
                if match:
                    username = match.group(1)
                else:
                    # Se não encontrou números, tenta pegar qualquer valor após username=
                    match = re.search(r'username=([^&]+)', url)
                    if match:
                        username = match.group(1)
            
            return servidor, username
        except:
            return "Desconhecido", "N/A"
            
    def normalize_text(self, text):
        """Remove acentos, caracteres especiais e normaliza pontuação do texto"""
        # Converte para string se não for
        text = str(text)
        
        # Remove espaços extras e normaliza pontuação
        text = ' '.join(text.split())  # Remove espaços extras
        text = text.replace("'", "")   # Remove aspas simples
        text = text.replace('"', '')   # Remove aspas duplas
        text = text.replace(',', ' ')  # Substitui vírgulas por espaços
        text = text.replace(';', ' ')  # Substitui ponto e vírgula por espaços
        text = text.replace(':', ' ')  # Substitui dois pontos por espaços
        text = text.replace('.', ' ')  # Substitui pontos por espaços
        text = text.replace('!', ' ')  # Substitui exclamação por espaços
        text = text.replace('?', ' ')  # Substitui interrogação por espaços
        text = text.replace('-', ' ')  # Substitui hífens por espaços
        text = text.replace('_', ' ')  # Substitui underscores por espaços
        text = text.replace('|', ' ')  # Substitui pipe por espaços
        
        # Normaliza o texto (NFD) e remove os diacríticos
        text = unicodedata.normalize('NFD', text)
        # Remove caracteres não ASCII e converte para minúsculas
        text = ''.join(c for c in text if not unicodedata.category(c) == 'Mn')
        text = text.lower()
        
        # Substitui caracteres especiais comuns
        replacements = {
            'ç': 'c',
            'ñ': 'n',
            'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a',
            'é': 'e', 'è': 'e', 'ê': 'e',
            'í': 'i', 'ì': 'i', 'î': 'i',
            'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o',
            'ú': 'u', 'ù': 'u', 'û': 'u',
            'ý': 'y', 'ÿ': 'y',
            'ä': 'a', 'ë': 'e', 'ï': 'i', 'ö': 'o', 'ü': 'u',
            'ß': 'ss',
            'æ': 'ae', 'œ': 'oe',
            'ð': 'd', 'þ': 'th',
            'ł': 'l', 'ø': 'o', 'å': 'a'
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        # Remove espaços extras novamente após todas as substituições
        text = ' '.join(text.split())
        
        return text

    def indexar_item(self, item, fonte="m3u"):
        """Indexa um item nos dicionários de busca"""
        try:
            # Extrai os dados do item baseado na fonte
            if fonte == "m3u":
                nome = item[0]
                tipo = item[1]
                temporada = item[2]
                categoria = item[4]
            else:  # banco de dados
                nome = item[1]
                tipo = item[3]
                temporada = item[4]
                categoria = item[6]
            
            # Normaliza os textos para busca
            nome_norm = self.normalize_text(str(nome))
            categoria_norm = self.normalize_text(str(categoria)) if categoria else ""
            tipo_norm = self.normalize_text(str(tipo))
            temporada_norm = self.normalize_text(str(temporada))
            
            # Indexa por nome
            if nome_norm not in self.index_nome:
                self.index_nome[nome_norm] = []
            self.index_nome[nome_norm].append((item, fonte))
            
            # Indexa por categoria
            if categoria_norm:
                if categoria_norm not in self.index_categoria:
                    self.index_categoria[categoria_norm] = []
                self.index_categoria[categoria_norm].append((item, fonte))
            
            # Indexa por tipo
            if tipo_norm not in self.index_tipo:
                self.index_tipo[tipo_norm] = []
            self.index_tipo[tipo_norm].append((item, fonte))
            
            # Indexa por temporada
            if temporada_norm not in self.index_temporada:
                self.index_temporada[temporada_norm] = []
            self.index_temporada[temporada_norm].append((item, fonte))
            
        except Exception as e:
            print(f"Erro ao indexar item: {str(e)}")
    
    def limpar_indices(self):
        """Limpa todos os índices"""
        self.index_nome.clear()
        self.index_categoria.clear()
        self.index_tipo.clear()
        self.index_temporada.clear()
    
    def reindexar_dados(self):
        """Reindexar todos os dados"""
        self.limpar_indices()
        
        # Indexa dados M3U
        for item in self.dados_m3u:
            self.indexar_item(item, "m3u")
            
        # Indexa dados do banco
        for item in self.dados_db:
            self.indexar_item(item, "db")
    
    def filtrar_resultados(self):
        """Filtra os resultados pesquisando diretamente no banco de dados com índices."""
        def perform_search():
            try:
                termo_busca = self.search_entry.get().strip()
                categoria_busca = self.category_search_entry.get().strip()
                
                # Obter o valor do OptionMenu (Todos, Filme, Série)
                tipo_selecionado = self.type_search_option.get()
                # Converter para o valor real do banco de dados
                if tipo_selecionado == "Todos":
                    tipo_busca = None  # Não aplicar filtro de tipo
                else:
                    tipo_busca = tipo_selecionado  # Filme ou Série
                    
                extra_busca = self.extra_search_entry.get().strip()

                # Incrementa contador de buscas
                self.estatisticas['buscas_realizadas'] += 1

                # Se todos os campos estiverem vazios (exceto tipo que pode ser "Todos"), limpa a lista e retorna
                if not termo_busca and not categoria_busca and not extra_busca and tipo_busca is None:
                    self.root.after_idle(self.limpar_treeview)
                    return

                # Cria uma conexão de banco de dados local para esta thread
                local_conn = sqlite3.connect('videos.db')
                local_cursor = local_conn.cursor()

                query = "SELECT id, name, type, season, username, category, url FROM videos WHERE 1=1"
                params = []

                if termo_busca:
                    query += " AND name LIKE ?"
                    params.append(f"%{termo_busca}%")

                if categoria_busca:
                    query += " AND category LIKE ?"
                    params.append(f"%{categoria_busca}%")

                if tipo_busca:  # Só aplica o filtro se não for "Todos" (quando tipo_busca não é None)
                    query += " AND type LIKE ?"
                    params.append(f"%{tipo_busca}%")

                if extra_busca:
                    # Adiciona condição para busca adicional em nome, categoria e tipo
                    query += " AND (name LIKE ? OR category LIKE ? OR type LIKE ?)"
                    params.extend([f"%{extra_busca}%", f"%{extra_busca}%", f"%{extra_busca}%"])

                query += " ORDER BY name LIMIT 5000"  # Limita para evitar sobrecarga na UI

                # Executa a busca no banco de dados
                local_cursor.execute(query, tuple(params))
                resultados_db = local_cursor.fetchall()
                local_conn.close() # Fecha a conexão local da thread

                def update_ui():
                    try:
                        self.limpar_treeview()
                        if not resultados_db:
                            self.tree.insert('', 'end', values=('', 'Nenhum resultado encontrado', '', '', '', '', ''))
                        else:
                            for i, row in enumerate(resultados_db, 1):
                                # row = (id, name, type, season, username, category, url)
                                _, name, tipo, temporada, username, categoria, url = row
                                servidor, _ = self.extrair_servidor_e_username(url)
                                self.tree.insert('', 'end', values=(i, name, tipo, temporada, servidor, categoria, url))
                    except Exception as e:
                        print(f"Erro ao atualizar a UI da pesquisa: {e}")

                self.root.after_idle(update_ui)

            except Exception as e:
                def show_error(err=e):
                    self.limpar_treeview()
                    self.tree.insert('', 'end', values=('', f'Erro na pesquisa: {err}', '', '', '', '', ''))
                    # Incrementa contador de erros
                    self.estatisticas['erros_encontrados'] += 1
                self.root.after_idle(show_error)

        # Limpa a Treeview e mostra "Pesquisando..." antes de iniciar a thread
        self.limpar_treeview()
        self.tree.insert('', 'end', values=('', 'Pesquisando...', '', '', '', '', ''))
        self.tree.update_idletasks()
        Thread(target=perform_search).start()

    def limpar_treeview(self):
        """Limpa todos os itens da Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def load_multiple_links(self):
        """Carrega múltiplos links M3U ao mesmo tempo"""
        try:
            # Cria uma nova janela
            multi_url_window = tk.Toplevel(self.root)
            multi_url_window.title("Adicionar Múltiplos Links")
            # Maximiza de forma cross-platform
            if platform.system() == "Windows":
                multi_url_window.state('zoomed')
            else:
                try:
                    multi_url_window.attributes('-zoomed', True)
                except:
                    multi_url_window.attributes('-fullscreen', True)
            # Corrigir o grab_set para evitar erro de window not viewable
            def setup_multi_url_window():
                if platform.system() == "Windows":
                    multi_url_window.state('zoomed')
                else:
                    try:
                        multi_url_window.attributes('-zoomed', True)
                    except:
                        multi_url_window.attributes('-fullscreen', True)
                multi_url_window.update_idletasks()
                width = multi_url_window.winfo_width()
                height = multi_url_window.winfo_height()
                x = (multi_url_window.winfo_screenwidth() // 2) - (width // 2)
                y = (multi_url_window.winfo_screenheight() // 2) - (height // 2)
                multi_url_window.geometry(f'+{x}+{y}')
                # Só faz grab_set quando a janela está realmente visível
                def wait_and_grab():
                    if multi_url_window.winfo_viewable():
                        multi_url_window.grab_set()
                    else:
                        multi_url_window.after(50, wait_and_grab)
                multi_url_window.after(0, wait_and_grab)
            self.root.after_idle(setup_multi_url_window)
            
            # Frame principal com split
            main_frame = ttk.Frame(multi_url_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # Frame esquerdo para links
            left_frame = ttk.Frame(main_frame)
            left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
            
            # Frame direito para terminal
            right_frame = ttk.Frame(main_frame)
            right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
            
            # Adiciona um texto explicativo
            ttk.Label(left_frame, 
                     text="Cole aqui seus links M3U (um por linha):",
                     wraplength=550,
                     padding=10).pack(fill=tk.X)
            
            # Cria um campo de texto com barra de rolagem para links
            text_frame = ttk.Frame(left_frame)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            text_scroll = ttk.Scrollbar(text_frame)
            text_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            
            text_area = tk.Text(text_frame, 
                               wrap=tk.WORD, 
                               yscrollcommand=text_scroll.set,
                               height=15)
            text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            text_scroll.config(command=text_area.yview)

            # Frame para progresso
            progress_frame = ttk.LabelFrame(left_frame, text="Progresso", padding="5")
            progress_frame.pack(fill=tk.X, padx=5, pady=5)

            # Barra de progresso
            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100)
            progress_bar.pack(fill=tk.X, pady=5)

            # Labels para informações
            info_frame = ttk.Frame(progress_frame)
            info_frame.pack(fill=tk.X)

            progress_label = ttk.Label(info_frame, text="0%")
            progress_label.pack(side=tk.LEFT, padx=5)

            status_label = ttk.Label(info_frame, text="", wraplength=500)
            status_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            
            # Frame para os botões
            button_frame = ttk.Frame(left_frame)
            button_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Frame para o terminal
            terminal_frame = ttk.LabelFrame(right_frame, text="Terminal", padding="5")
            terminal_frame.pack(fill=tk.BOTH, expand=True)
            
            # Terminal
            terminal_scroll = ttk.Scrollbar(terminal_frame)
            terminal_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            
            terminal = tk.Text(terminal_frame,
                             wrap=tk.WORD,
                             yscrollcommand=terminal_scroll.set,
                             bg='black',
                             fg='white',
                             font=('Consolas', 10),
                             height=20)
            terminal.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            terminal_scroll.config(command=terminal.yview)
            
            # Configura o terminal como somente leitura
            terminal.config(state='disabled')
            
            # Função para adicionar texto ao terminal
            def append_to_terminal(text, color='white'):
                try:
                    if multi_url_window.winfo_exists() and terminal.winfo_exists():
                        terminal.config(state='normal')
                        terminal.tag_configure(color, foreground=color)
                        terminal.insert(tk.END, f"{text}\n", color)
                        terminal.see(tk.END)
                        terminal.config(state='disabled')
                        terminal.update_idletasks()
                except Exception as e:
                    print(f"Erro ao atualizar terminal: {str(e)}")

            # Variável para controlar o cancelamento
            cancel_process = False
            
            # Função para atualizar a interface de forma segura
            def safe_update_interface(text, progress=None):
                try:
                    if multi_url_window.winfo_exists():
                        if text:
                            status_label.config(text=text)
                            append_to_terminal(text)
                        if progress is not None:
                            # Garante que progress é float para formatação
                            try:
                                progress_float = float(progress)
                            except Exception:
                                progress_float = 0.0
                            progress_var.set(progress_float)
                            progress_label.config(text=f"{progress_float:.1f}%")
                        multi_url_window.update_idletasks()
                except Exception as e:
                    print(f"Erro ao atualizar interface: {str(e)}")
            
            # Função para processar os links
            def process_links():
                nonlocal cancel_process
                cancel_process = False
                # Usa conexão/cursor locais para esta thread
                thread_conn = sqlite3.connect('videos.db')
                thread_cursor = thread_conn.cursor()
                try:
                    # Testa a conexão com o banco
                    try:
                        thread_cursor.execute("SELECT 1")
                        thread_cursor.fetchone()
                    except sqlite3.Error as e:
                        if multi_url_window.winfo_exists():
                            append_to_terminal(f"Erro ao conectar ao banco de dados: {str(e)}", 'red')
                            safe_update_interface("Erro no banco de dados!", 'red')
                        return

                    # Verifica se a tabela existe, se não, cria
                    thread_cursor.execute('''
                        CREATE TABLE IF NOT EXISTS videos (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            url TEXT NOT NULL UNIQUE,
                            type TEXT NOT NULL,
                            season TEXT NOT NULL,
                            username TEXT,
                            category TEXT,
                            downloaded INTEGER DEFAULT 0
                        )
                    ''')
                    thread_conn.commit()

                    # Verifica o tamanho inicial do banco
                    thread_cursor.execute("SELECT COUNT(*) FROM videos")
                    initial_count = thread_cursor.fetchone()[0]
                    if multi_url_window.winfo_exists():
                        append_to_terminal(f"Total de vídeos no banco antes: {initial_count}", 'cyan')
                    
                    # Obtém os links
                    links = text_area.get("1.0", tk.END).strip().split("\n")
                    links = [link.strip() for link in links if link.strip()]
                    
                    if not links:
                        if multi_url_window.winfo_exists():
                            safe_update_interface("Nenhum link encontrado!", 'yellow')
                        return
                    
                    # Desabilita os botões durante o processamento
                    if multi_url_window.winfo_exists():
                        if process_button.winfo_exists():
                            process_button.configure(state="disabled")
                        if cancel_button.winfo_exists():
                            cancel_button.configure(state="normal")
                    
                    total_links = len(links)
                    if multi_url_window.winfo_exists():
                        append_to_terminal(f"Iniciando download de {total_links} links M3U...", 'cyan')
                    
                    # Contador para links ignorados por causa da extensão
                    ignored_links = 0
                    
                    # Configuração otimizada do requests
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Accept": "*/*",
                        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                        "Connection": "keep-alive",
                        "Cache-Control": "no-cache",
                        "Pragma": "no-cache"
                    }
                    
                    # Baixa todas as M3U em paralelo com timeout aumentado e verificação SSL desativada
                    m3u_contents = {}  # Dicionário para armazenar conteúdo por URL
                    failed_downloads = []  # Lista para armazenar URLs que falharam
                    
                    # Aumenta o tamanho do lote para reduzir atualizações de interface
                    batch_size = 5000
                    update_interval = 5  # Atualiza a interface a cada 5 segundos
                    
                    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                        future_to_url = {executor.submit(
                            lambda u: requests.get(
                                u, 
                                headers=headers, 
                                timeout=60,
                                verify=False,
                                allow_redirects=True
                            ), 
                            url
                        ): url for url in links}
                        
                        for future in concurrent.futures.as_completed(future_to_url):
                            url = future_to_url[future]
                            try:
                                response = future.result()
                                response.raise_for_status()
                                
                                # Verifica se o conteúdo é realmente um arquivo M3U
                                content = response.text.splitlines()
                                if not any(line.startswith('#EXTINF:') for line in content):
                                    raise ValueError("O conteúdo não parece ser um arquivo M3U válido")
                                    
                                m3u_contents[url] = content
                                if multi_url_window.winfo_exists():
                                    append_to_terminal(f"Download concluído: {url}", 'green')
                            except requests.exceptions.SSLError:
                                if multi_url_window.winfo_exists():
                                    append_to_terminal(f"Erro SSL ao baixar {url}. Tentando novamente sem verificação SSL...", 'yellow')
                                try:
                                    response = requests.get(url, headers=headers, timeout=60, verify=False, allow_redirects=True)
                                    response.raise_for_status()
                                    content = response.text.splitlines()
                                    if not any(line.startswith('#EXTINF:') for line in content):
                                        raise ValueError("O conteúdo não parece ser um arquivo M3U válido")
                                    m3u_contents[url] = content
                                    if multi_url_window.winfo_exists():
                                        append_to_terminal(f"Download concluído após retry: {url}", 'green')
                                except Exception as e:
                                    failed_downloads.append((url, str(e)))
                                    if multi_url_window.winfo_exists():
                                        append_to_terminal(f"Erro ao baixar {url} mesmo sem SSL: {str(e)}", 'red')
                            except Exception as e:
                                failed_downloads.append((url, str(e)))
                                if multi_url_window.winfo_exists():
                                    append_to_terminal(f"Erro ao baixar {url}: {str(e)}", 'red')
                    
                    if not m3u_contents:
                        if multi_url_window.winfo_exists():
                            safe_update_interface("Nenhum conteúdo encontrado nos links!", 'red')
                        return
                    
                    if multi_url_window.winfo_exists():
                        append_to_terminal(f"\nProcessando {sum(len(content) for content in m3u_contents.values())} linhas...", 'cyan')
                    
                    # Desabilita temporariamente as restrições do banco de dados
                    thread_cursor.execute("PRAGMA foreign_keys=OFF")
                    thread_cursor.execute("PRAGMA synchronous=OFF")
                    thread_cursor.execute("PRAGMA journal_mode=MEMORY")
                    
                    # Prepara a query de inserção em lote
                    insert_query = '''
                        INSERT OR IGNORE INTO videos (name, url, type, season, username, category)
                        VALUES (?, ?, ?, ?, ?, ?)
                    '''
                    
                    # Lista para armazenar os dados em lote
                    batch_data = []
                    total_processed = 0
                    total_added = 0
                    last_update = time.time()
                    
                    # Processa cada M3U separadamente
                    for m3u_url, content in m3u_contents.items():
                        if cancel_process:
                            break
                            
                        if multi_url_window.winfo_exists():
                            append_to_terminal(f"\nProcessando M3U: {m3u_url}", 'cyan')
                        
                        # Processa em chunks maiores para melhor performance
                        chunk_size = 50000
                        for i in range(0, len(content), chunk_size):
                            if cancel_process:
                                break
                                
                            chunk = content[i:i + chunk_size]
                            progress = (i / len(content)) * 100
                            
                            # Atualiza a interface apenas a cada update_interval segundos
                            current_time = time.time()
                            if current_time - last_update >= update_interval:
                                def update_ui():
                                    if multi_url_window.winfo_exists():
                                        safe_update_interface(f"Processando chunk {i//chunk_size + 1}...", progress)
                                threading.Thread(target=update_ui, daemon=True).start()
                                last_update = current_time
                            
                            # Processa o chunk
                            for j in range(len(chunk)):
                                if chunk[j].startswith("#EXTINF:"):
                                    try:
                                        # Extrai informações do vídeo
                                        name = None
                                        category = None
                                        if 'tvg-name="' in chunk[j]:
                                            name = chunk[j].split('tvg-name="')[1].split('"')[0]
                                        elif ',' in chunk[j]:
                                            name = chunk[j].split(',', 1)[1].strip()
                                            
                                        # Extrai a categoria (group-title)
                                        if 'group-title="' in chunk[j]:
                                            category = chunk[j].split('group-title="')[1].split('"')[0]
                                        
                                        if not name or j + 1 >= len(chunk):
                                            continue
                                            
                                        url_video = chunk[j + 1].strip()
                                        if not url_video or url_video.startswith('#'):
                                            continue
                                            
                                        # Ignora URLs que contenham /play/
                                        if '/play/' in url_video:
                                            continue
                                        
                                        # Verifica a extensão do arquivo
                                        url_lower = url_video.lower()
                                        if url_lower.endswith('.ts') or not (url_lower.endswith('.mp4') or url_lower.endswith('.mkv')):
                                            ignored_links += 1
                                            continue
                                        
                                        # Determina o tipo e temporada
                                        content_type = "Filme"
                                        season = "-"
                                        
                                        match = re.search(r"(.*?)\s*(S\d{2})\s*E\d{2}", name)
                                        if match:
                                            content_type = "Série"
                                            season = match.group(2)
                                        
                                        total_processed += 1
                                        batch_data.append((name, url_video, content_type, season, m3u_url, category))
                                        
                                        # Quando o lote atinge o tamanho definido, insere no banco
                                        if len(batch_data) >= batch_size:
                                            thread_cursor.executemany(insert_query, batch_data)
                                            thread_conn.commit()
                                            total_added += len(batch_data)
                                            batch_data = []
                                    except Exception as e:
                                        if multi_url_window.winfo_exists():
                                            append_to_terminal(f"Erro ao processar item: {str(e)}", 'red')
                                        continue
                    
                    # Insere o lote restante
                    if batch_data:
                        thread_cursor.executemany(insert_query, batch_data)
                        thread_conn.commit()
                        total_added += len(batch_data)
                    
                    # Reativa as restrições do banco de dados
                    thread_cursor.execute("PRAGMA foreign_keys=ON")
                    thread_cursor.execute("PRAGMA synchronous=NORMAL")
                    thread_cursor.execute("PRAGMA journal_mode=DELETE")
                    
                    # Verifica o tamanho final do banco
                    thread_cursor.execute("SELECT COUNT(*) FROM videos")
                    final_count = thread_cursor.fetchone()[0]
                    
                    # Atualiza interface após conclusão
                    if multi_url_window.winfo_exists():
                        if process_button.winfo_exists():
                            process_button.configure(state="normal")
                        if cancel_button.winfo_exists():
                            cancel_button.configure(state="disabled")
                    
                    if not cancel_process:
                        if multi_url_window.winfo_exists():
                            append_to_terminal(f"\n{'='*50}", 'cyan')
                            append_to_terminal("RESUMO DO PROCESSAMENTO", 'cyan')
                            append_to_terminal(f"{'='*50}", 'cyan')
                            append_to_terminal(f"Total de vídeos no banco antes: {initial_count}", 'cyan')
                            append_to_terminal(f"Total de vídeos no banco após: {final_count}", 'cyan')
                            append_to_terminal(f"Novos vídeos adicionados: {final_count - initial_count}", 'green')
                            append_to_terminal(f"Total de itens processados: {total_processed}", 'yellow')
                            append_to_terminal(f"Links ignorados por extensão: {ignored_links}", 'yellow')
                            append_to_terminal(f"{'='*50}\n", 'cyan')
                            
                            final_msg = (f"Processamento concluído!\n"
                                       f"Total processado: {total_processed}\n"
                                       f"Novos itens: {total_added}\n"
                                       f"Total no banco: {final_count}")
                            safe_update_interface(final_msg, 'green')
                            
                            if total_processed > 0:
                                # Aguarda 3 segundos antes de fechar
                                multi_url_window.after(3000, multi_url_window.destroy)

                    # Cria um log das falhas após o processamento
                    if failed_downloads:
                        # Cria diretório de logs se não existir
                        log_dir = "logs"
                        if not os.path.exists(log_dir):
                            os.makedirs(log_dir)
                            
                        # Salva em arquivo de log
                        log_file = os.path.join(log_dir, "failed_downloads.log")
                        with open(log_file, 'w', encoding='utf-8') as log_file:
                            log_file.write("Playlists que falharam ao serem baixadas:\n")
                            for failed_url, error_msg in failed_downloads:
                                log_file.write(f"{failed_url}: {error_msg}\n")
                            append_to_terminal("Log de falhas criado: logs/failed_downloads.log", 'yellow')
                
                finally:
                    # Garante que todas as alterações foram salvas
                    try:
                        thread_conn.commit()
                        thread_conn.close()
                    except:
                        pass
                    # A conexão é fechada pelo self.__del__ ou quando a aplicação finaliza
            
            def cancel_processing():
                nonlocal cancel_process
                cancel_process = True
                safe_update_interface("Cancelando...", 'yellow')
                append_to_terminal("Cancelando processamento...", 'yellow')
                if multi_url_window.winfo_exists():
                    cancel_button.configure(state="disabled")
            
            # Botões
            process_button = ctk.CTkButton(
                button_frame,
                text="Processar Links",
                command=lambda: threading.Thread(target=process_links).start(),
                fg_color="#2ecc71",  # Verde
                hover_color="#27ae60"  # Verde escuro para hover
            )
            process_button.pack(side=tk.RIGHT, padx=5)
            
            cancel_button = ctk.CTkButton(
                button_frame,
                text="Cancelar",
                command=cancel_processing,
                state="disabled",
                fg_color="#e74c3c",  # Vermelho
                hover_color="#c0392b"  # Vermelho escuro para hover
            )
            cancel_button.pack(side=tk.RIGHT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir janela de múltiplos links: {str(e)}")
            
    def init_database(self):
        """Inicializa o banco de dados e carrega na memória"""
        try:
            # Verifica se o arquivo do banco existe
            db_exists = os.path.exists('videos.db')
            
            # Conecta ao banco de dados com configurações otimizadas
            self.conn = sqlite3.connect('videos.db')
            self.cursor = self.conn.cursor()
            
            # Otimizações para carregamento rápido
            self.cursor.execute("PRAGMA synchronous = OFF")
            self.cursor.execute("PRAGMA journal_mode = MEMORY")
            self.cursor.execute("PRAGMA cache_size = -5000000")  # 5GB de cache
            self.cursor.execute("PRAGMA temp_store = MEMORY")
            
            # Cria tabela se não existir
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    type TEXT NOT NULL,
                    season TEXT NOT NULL,
                    username TEXT, 
                    category TEXT,
                    downloaded INTEGER DEFAULT 0
                )
            """)
            # --- Otimização: Criar índices para acelerar as buscas ---
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_name ON videos (name);")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_category ON videos (category);")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_type ON videos (type);")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_username ON videos (username);")
            # ---------------------------------------------------------

            
            self.conn.commit()
            
            print("Banco de dados inicializado com sucesso")
            
            # Apenas verifica a quantidade de registros sem carregar todos os dados
            self.cursor.execute('SELECT COUNT(*) FROM videos')
            total_records = self.cursor.fetchone()[0]
            
            if not db_exists:
                print("Banco de dados criado com sucesso")
            else:
                print(f"Banco de dados conectado com sucesso. Total de registros: {total_records}")
            
            # --- Inicialização do novo banco de dados 'downloads.db' ---
            try:
                jobs_conn = sqlite3.connect('downloads.db')
                jobs_cursor = jobs_conn.cursor()
                jobs_cursor.execute("""
                    CREATE TABLE IF NOT EXISTS download_jobs (
                        name TEXT PRIMARY KEY,
                        url TEXT NOT NULL,
                        remote_size INTEGER
                    )
                """)
                jobs_conn.commit()
                jobs_conn.close()
                print("Banco de dados 'downloads.db' inicializado com sucesso.")
            except Exception as e:
                print(f"Erro ao inicializar 'downloads.db': {e}")

        except Exception as e:
            print(f"Erro ao inicializar banco de dados: {str(e)}")
            raise

    def resume_unfinished_downloads(self):
        """Verifica o banco por downloads inacabados e os adiciona à fila."""
        if self.is_downloading:
            return # Não faz nada se já estiver baixando

        try:
            local_conn = sqlite3.connect('downloads.db') # Conecta ao DB de trabalhos
            local_cursor = local_conn.cursor()
            local_cursor.execute("SELECT name, url, remote_size FROM download_jobs")
            unfinished_downloads = local_cursor.fetchall()
            local_conn.close()

            if not unfinished_downloads:
                print("Nenhum trabalho de download pendente encontrado.")
                return

            resumed_count = 0
            skipped_count = 0
            downloads_to_remove = []

            base_download_path = self.download_path.get()

            for name, url, remote_size in unfinished_downloads:
                try:
                    found_path = self.find_file_recursively(base_download_path, name)

                    if found_path:
                        local_size = os.path.getsize(found_path)
                        if local_size >= remote_size:
                            # Download completo, marcar para remoção
                            downloads_to_remove.append(name)
                            print(f"Download já completo, removendo da lista de trabalhos: {name}")
                        else:
                            # Incompleto, verifica limite de estagnação antes de re-enfileirar
                            if self.can_retry_download(name):
                                self.increment_retry_count(name)
                                if (name, url, base_download_path) not in self.download_queue:
                                    self.download_queue.append((name, url, base_download_path))
                                    resumed_count += 1
                                    print(f"Adicionado à fila para retomada (tamanho incorreto): {name}")
                            else:
                                # Atingiu o limite de estagnação, remover do DB
                                downloads_to_remove.append(name)
                                skipped_count += 1
                                print(f"LIMITE ATINGIDO: '{name}' não será mais retomado ({self.max_retries} ciclos de estagnação).")
                    else:
                        # Arquivo não encontrado, verifica limite de estagnação antes de re-enfileirar
                        if self.can_retry_download(name):
                            self.increment_retry_count(name)
                            if (name, url, base_download_path) not in self.download_queue:
                                self.download_queue.append((name, url, base_download_path))
                                resumed_count += 1
                                print(f"Adicionado à fila para retomada (arquivo ausente): {name}")
                        else:
                            # Atingiu o limite de estagnação, remover do DB
                            downloads_to_remove.append(name)
                            skipped_count += 1
                            print(f"LIMITE ATINGIDO: '{name}' não será mais retomado ({self.max_retries} ciclos de estagnação).")
                except Exception as e:
                    print(f"Erro ao verificar trabalho pendente {name}: {e}")

            # Remove os downloads concluídos e os que atingiram o limite do DB de trabalhos
            if downloads_to_remove:
                local_conn = sqlite3.connect('downloads.db')
                local_cursor = local_conn.cursor()
                for job_name in downloads_to_remove:
                    local_cursor.execute("DELETE FROM download_jobs WHERE name = ?", (job_name,))
                local_conn.commit()
                local_conn.close()

            if resumed_count > 0:
                # Atualiza contador de estagnação baseado na quantidade reenfileirada
                self.update_stagnation_counter(resumed_count)

                messagebox.showinfo("Downloads Retomados", f"{resumed_count} downloads inacabados foram adicionados à fila.")
                # Inicia o processamento da fila se houver itens
                self.process_download_queue()
            elif skipped_count > 0:
                # Nenhum download reenfileirado, mas alguns atingiram o limite
                # NAO atualiza o contador - apenas remove do DB
                messagebox.showinfo("Limite Atingido", f"{skipped_count} downloads foram removidos por atingir o limite de {self.max_retries} ciclos de estagnação.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao tentar retomar trabalhos de download: {e}")
    
    def run(self):
        """Inicia o programa"""
        self.root.mainloop()

    def sort_treeview(self, col):
        """Ordena a Treeview pela coluna clicada"""
        # Obtém todos os itens
        items = [(self.tree.set(item, col), item) for item in self.tree.get_children('')]
        
        # Se clicou na mesma coluna, inverte a ordem
        if self.last_sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_reverse = False
            self.last_sort_column = col
        
        # Ordena os itens
        items.sort(reverse=self.sort_reverse)
        
        # Reordena os itens na Treeview
        for index, (val, item) in enumerate(items):
            self.tree.move(item, '', index)
            
        # Atualiza o indicador de ordenação nas colunas
        for column in self.tree['columns']:
            if column == col:
                self.tree.heading(column, text=f"{column} {'↓' if self.sort_reverse else '↑'}")
            else:
                self.tree.heading(column, text=column)

    def copy_selected_link(self):
        """Copia o link do vídeo selecionado para a área de transferência"""
        url = self.get_url_from_selection()
        if not url:
            messagebox.showinfo("Aviso", "Por favor, selecione um vídeo da lista.")
            return
            
        self.root.clipboard_clear()
        self.root.clipboard_append(url)
        messagebox.showinfo("Sucesso", "Link copiado para a área de transferência!")
    
    def open_selected_in_browser(self):
        """Abre o vídeo selecionado na lista no navegador"""
        url = self.get_url_from_selection()
        if not url:
            messagebox.showinfo("Aviso", "Por favor, selecione um vídeo da lista.")
            return
            
        try:
            webbrowser.open(url)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir no navegador: {str(e)}")

    def change_theme(self, theme_name):
        """Muda o tema da aplicação"""
        try:
            self.active_theme = theme_name  # Atualiza o tema ativo
            self.root.set_theme(theme_name)
            # Atualiza o OptionMenu para refletir o tema selecionado
            if hasattr(self, 'theme_menu'):
                self.theme_menu.set(theme_name)
            # Salva a configuração automaticamente
            self.save_config()
            messagebox.showinfo("Tema alterado", f"Tema alterado para: {theme_name}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao mudar o tema: {e}")

    def change_player(self, player_name):
        """Muda o player da aplicação"""
        self.player_type = player_name
        messagebox.showinfo("Player alterado", f"Player configurado para: {player_name}")

    def change_user_agent(self, choice):
        """
        Gerencia a mudança de User-Agent.
        - Se for "Custom...", mostra campo para entrada personalizada
        - Caso contrário, define o User-Agent selecionado
        """
        if choice == "Custom...":
            # Mostra campo para User-Agent personalizado
            self.ua_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            self.ua_entry.bind("<Return>", lambda e: self.set_custom_user_agent())
        else:
            # Esconde campo personalizado e define User-Agent
            self.ua_entry.pack_forget()
            self.user_agent.set(choice)
            self.save_config()  # Salva a configuração automaticamente
            
    def set_custom_user_agent(self):
        """
        Define um User-Agent personalizado.
        - Obtém o valor do campo de entrada
        - Remove espaços em branco
        - Define como User-Agent atual
        """
        custom_ua = self.ua_entry.get().strip()
        if custom_ua:
            self.user_agent.set(custom_ua)
            self.ua_entry.pack_forget()
            self.save_config()  # Salva a configuração automaticamente

    def editar_urls_banco(self):
        """Interface para editar URLs no banco de dados"""
        try:
            # Verifica se há conexão com o banco
            if not self.conn or not self.cursor:
                messagebox.showerror("Erro", "Banco de dados não está conectado. Tente carregar o banco primeiro.")
                return
            
            # Cria janela de edição
            edit_window = ctk.CTkToplevel()
            edit_window.title("Editor de URLs - Banco de Dados")
            edit_window.geometry("600x400")
            edit_window.resizable(True, True)
            
            # Configura a janela como modal de forma mais segura
            edit_window.transient(self.root)
            edit_window.focus_set()
            
            # Tenta fazer a janela modal de forma segura
            try:
                edit_window.grab_set()
            except tk.TclError:
                # Se falhar, apenas foca na janela
                edit_window.focus_set()
            
            # Frame principal
            main_frame = ctk.CTkFrame(edit_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            main_frame.grid_columnconfigure(0, weight=1) # Make column 0 expandable
            
            # Título
            title_label = ctk.CTkLabel(main_frame, text="Editor de URLs no Banco de Dados", 
                                     font=ctk.CTkFont(size=16, weight="bold"))
            title_label.grid(row=0, column=0, pady=(0, 10), sticky="ew")
            
            # Frame para configurações
            config_frame = ctk.CTkFrame(main_frame)
            config_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
            
            # URL de origem
            ctk.CTkLabel(config_frame, text="URL de origem (será substituída):").pack(anchor=tk.W, padx=10, pady=(10, 5))
            url_origem_entry = ctk.CTkEntry(config_frame, placeholder_text="url anterior")
            url_origem_entry.pack(padx=10, pady=(0, 10))
            url_origem_entry.insert(0, "")
            
            # URL de destino
            ctk.CTkLabel(config_frame, text="URL de destino (nova URL):").pack(anchor=tk.W, padx=10, pady=(10, 5))
            url_destino_entry = ctk.CTkEntry(config_frame, placeholder_text="url posterior")
            url_destino_entry.pack(padx=10, pady=(0, 10))
            url_destino_entry.insert(0, "")
            
            # Frame para preview
            preview_frame = ctk.CTkFrame(main_frame)
            preview_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
            main_frame.grid_rowconfigure(2, weight=1) # Make row 2 expandable
            
            ctk.CTkLabel(preview_frame, text="Preview das URLs afetadas:").pack(anchor=tk.W, padx=10, pady=(10, 5))
            
            # Treeview para preview
            preview_tree = ttk.Treeview(preview_frame, columns=("nome", "url_atual", "url_nova"), show="headings", height=8)
            preview_tree.heading("nome", text="Nome")
            preview_tree.heading("url_atual", text="URL Atual")
            preview_tree.heading("url_nova", text="Nova URL")
            
            preview_tree.column("nome", width=200)
            preview_tree.column("url_atual", width=200)
            preview_tree.column("url_nova", width=200)
            
            # Scrollbar para o treeview
            preview_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=preview_tree.yview)
            preview_tree.configure(yscrollcommand=preview_scrollbar.set)
            
            preview_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
            preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
            
            # Frame para botões
            button_frame = ctk.CTkFrame(main_frame)
            button_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
            
            def preview_urls():
                """Mostra preview das URLs que serão alteradas"""
                try:
                    # Verifica se o cursor existe
                    assert self.cursor is not None, "Cursor do banco não está disponível"
                    
                    # Limpa o treeview
                    for item in preview_tree.get_children():
                        preview_tree.delete(item)
                    
                    url_origem = url_origem_entry.get().strip()
                    url_destino = url_destino_entry.get().strip()
                    
                    if not url_origem or not url_destino:
                        messagebox.showwarning("Aviso", "Preencha ambas as URLs")
                        return
                    
                    # Busca URLs que contêm o domínio de origem
                    self.cursor.execute("""
                        SELECT name, url FROM videos 
                        WHERE url LIKE ? 
                        LIMIT 50
                    """, ("%" + url_origem + "%",))
                    
                    resultados = self.cursor.fetchall()
                    
                    if not resultados:
                        messagebox.showinfo("Info", "Nenhuma URL encontrada com o padrão especificado")
                        return
                    
                    # Adiciona resultados ao treeview
                    for nome, url_atual in resultados:
                        nova_url = url_atual.replace(url_origem, url_destino)
                        preview_tree.insert("", tk.END, values=(nome, url_atual, nova_url))
                    
                    # Mostra total de registros afetados
                    self.cursor.execute("""
                        SELECT COUNT(*) FROM videos 
                        WHERE url LIKE ?
                    """, ("%" + url_origem + "%",))
                    
                    total = self.cursor.fetchone()[0]
                    messagebox.showinfo("Preview", f"Encontrados {total} registros que serão alterados.\nMostrando os primeiros 50 no preview.")
                    
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao fazer preview: {str(e)}")
            
            def aplicar_alteracoes():
                """Aplica as alterações no banco de dados"""
                try:
                    # Verifica se o cursor e conexão existem
                    assert self.cursor is not None, "Cursor do banco não está disponível"
                    assert self.conn is not None, "Conexão do banco não está disponível"
                    
                    url_origem = url_origem_entry.get().strip()
                    url_destino = url_destino_entry.get().strip()
                    
                    if not url_origem or not url_destino:
                        messagebox.showwarning("Aviso", "Preencha ambas as URLs")
                        return
                    
                    # Confirma a operação
                    resposta = messagebox.askyesno(
                        "Confirmar Alteração", 
                        f"Tem certeza que deseja substituir todas as URLs que começam com:\n"
                        f"'{url_origem}'\n"
                        f"por:\n"
                        f"'{url_destino}'?\n\n"
                        f"Esta operação não pode ser desfeita!"
                    )
                    
                    if not resposta:
                        return
                    
                    # Conta quantos registros serão afetados
                    self.cursor.execute("""
                        SELECT COUNT(*) FROM videos 
                        WHERE url LIKE ?
                    """, ("%" + url_origem + "%",))
                    
                    total_afetados = self.cursor.fetchone()[0]
                    
                    if total_afetados == 0:
                        messagebox.showinfo("Info", "Nenhuma URL encontrada para alterar")
                        return
                    
                    # Executa a atualização
                    self.cursor.execute("""
                        UPDATE videos 
                        SET url = REPLACE(url, ?, ?) 
                        WHERE url LIKE ?
                    """, (url_origem, url_destino, "%" + url_origem + "%"))
                    
                    # Confirma as alterações
                    self.conn.commit()
                    
                    registros_alterados = self.cursor.rowcount
                    
                    messagebox.showinfo(
                        "Sucesso", 
                        f"Alteração concluída com sucesso!\n\n"
                        f"Registros alterados: {registros_alterados}\n"
                        f"URLs substituídas de '{url_origem}' para '{url_destino}'"
                    )
                    
                    
                    # Fecha a janela
                    edit_window.destroy()
                    
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao aplicar alterações: {str(e)}")
                    if self.conn:
                        self.conn.rollback()
            
            # Botões
            preview_button = ctk.CTkButton(
                button_frame, 
                text="Preview", 
                command=preview_urls,
                fg_color="#3498db",
                hover_color="#2980b9"
            )
            preview_button.pack(side=tk.LEFT, padx=5)
            
            aplicar_button = ctk.CTkButton(
                button_frame, 
                text="Aplicar Alterações", 
                command=aplicar_alteracoes,
                fg_color="#e74c3c",
                hover_color="#c0392b"
            )
            aplicar_button.pack(side=tk.LEFT, padx=5)
            
            cancelar_button = ctk.CTkButton(
                button_frame, 
                text="Cancelar", 
                command=edit_window.destroy
            )
            cancelar_button.pack(side=tk.RIGHT, padx=5)
            
            # --- Seção para Remover por Fonte ---
            remover_frame = ctk.CTkFrame(main_frame, fg_color=("#e0e0e0", "#2d2d2d"))
            remover_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=(20, 5))
            
            ctk.CTkLabel(remover_frame, text="Remover Conteúdo por Fonte (DNS)", font=ctk.CTkFont(weight="bold")).pack(pady=(5,10))
            
            fonte_entry = ctk.CTkEntry(remover_frame, placeholder_text="Digite a URL da fonte a ser removida")
            fonte_entry.pack(fill="x", expand=True, padx=10, pady=5)

            def remover_por_fonte():
                """Remove todos os registros de uma fonte específica."""
                fonte_url = fonte_entry.get().strip()
                if not fonte_url:
                    messagebox.showwarning("Aviso", "Por favor, digite a URL da fonte para remover.")
                    return

                try:
                    assert self.cursor is not None, "Cursor do banco não está disponível"
                    assert self.conn is not None, "Conexão do banco não está disponível"

                    # Contar quantos registros serão afetados
                    self.cursor.execute("SELECT COUNT(*) FROM videos WHERE username LIKE ?", (f"%{fonte_url}%",))
                    count = self.cursor.fetchone()[0]

                    if count == 0:
                        messagebox.showinfo("Informação", f"Nenhum conteúdo encontrado para a fonte: {fonte_url}")
                        return

                    # Primeira confirmação
                    if not messagebox.askyesno("Confirmar Remoção", 
                        f"Você está prestes a remover {count} registros da fonte:\n\n{fonte_url}\n\nEsta ação não pode ser desfeita. Deseja continuar?"):
                        return

                    # Segunda confirmação (mais forte)
                    if not messagebox.askyesno("ATENÇÃO - Confirmação Final", 
                        "⚠️ ATENÇÃO: A remoção é permanente!\n\nConfirma a exclusão de todos os dados desta fonte?"):
                        return

                    # Executar a remoção
                    self.cursor.execute("DELETE FROM videos WHERE username LIKE ?", (f"%{fonte_url}%",))
                    self.conn.commit()
                    
                    registros_removidos = self.cursor.rowcount

                    messagebox.showinfo("Sucesso", f"{registros_removidos} registros da fonte '{fonte_url}' foram removidos com sucesso.")


                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao remover por fonte: {str(e)}")
                    if self.conn:
                        self.conn.rollback()

            remover_button = ctk.CTkButton(remover_frame, text="Remover Fonte", command=remover_por_fonte, fg_color="#e74c3c", hover_color="#c0392b")
            remover_button.pack(pady=10)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir editor de URLs: {str(e)}")


    def atualizar_interface(self):
        """Atualiza a interface com os dados atuais"""
        try:
            # Limpa a Treeview
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Contador para numeração
            contador = 1
            
            # Adiciona os dados M3U
            for item in self.dados_m3u:
                # Ordem: Nº, Nome, Tipo, Temporada, Servidor, Categoria, Link de Origem
                self.tree.insert('', 'end', values=(contador, item[0], item[1], item[2], item[3], item[4], item[5]))
                contador += 1
            
            # Se não houver dados M3U mas houver dados do banco, mostra os dados do banco
            if not self.dados_m3u and self.dados_db:
                for item in self.dados_db:
                    servidor, username = self.extrair_servidor_e_username(item[2])
                    # Ordem: Nº, Nome, Tipo, Temporada, Servidor, Categoria, Link de Origem
                    self.tree.insert('', 'end', values=(contador, item[1], item[3], item[4], servidor, item[6], item[2]))
                    contador += 1
        except Exception as e:
            print(f"Erro ao atualizar interface: {str(e)}")
            messagebox.showerror("Erro", f"Erro ao atualizar interface: {str(e)}")

    def abrir_submenu_reserva(self):
        """Abre um submenu com as opções D2-Request e D3-Urllib"""
        # Cria uma janela popup para o submenu
        submenu_window = ctk.CTkToplevel(self.root)
        submenu_window.title("Modo Reserva")
        submenu_window.geometry("250x150")
        submenu_window.resizable(False, False)  # Impede redimensionamento
        
        # Centraliza a janela em relação à janela principal
        self.root.update_idletasks()  # Atualiza a geometria da janela principal
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()
        
        x = root_x + (root_width // 2) - 125  # 250/2
        y = root_y + (root_height // 2) - 75  # 150/2
        
        submenu_window.geometry(f"{250}x{150}+{x}+{y}")
        
        # Torna a janela modal
        submenu_window.transient(self.root)
        try:
            submenu_window.grab_set()
        except tk.TclError:
            pass  # Ignora erro se a janela não puder ser configurada como modal
        
        # Configura o protocolo de fechamento
        submenu_window.protocol("WM_DELETE_WINDOW", submenu_window.destroy)
        
        # Botões do submenu
        btn_d2 = ctk.CTkButton(
            submenu_window,
            text="D2-Request",
            command=self.download_selected_advanced,
            fg_color=CORES_BOTOES['D2_REQUEST'],  # Laranja
            hover_color=CORES_BOTOES['D2_REQUEST_HOVER']  # Laranja escuro para hover
        )
        btn_d2.pack(pady=5, padx=10, fill=tk.X)

        btn_d3 = ctk.CTkButton(
            submenu_window,
            text="D3-Urllib",
            command=self.download_selected_v3,
            fg_color=CORES_BOTOES['D3_URLLIB'],  # Verde água
            hover_color=CORES_BOTOES['D3_URLLIB_HOVER']  # Verde água escuro para hover
        )
        btn_d3.pack(pady=5, padx=10, fill=tk.X)

        # Botão para fechar o submenu
        btn_fechar = ctk.CTkButton(
            submenu_window,
            text="Fechar",
            command=submenu_window.destroy,
            fg_color=CORES_BOTOES['FECHAR'],  # Cinza
            hover_color=CORES_BOTOES['FECHAR_HOVER']  # Cinza escuro
        )
        btn_fechar.pack(pady=5, padx=10, fill=tk.X)
        
        # Força o foco na nova janela
        submenu_window.focus_force()

    def limpar_banco(self):
        """Limpa o banco de dados videos.db"""
        if messagebox.askyesno("Confirmar", "Tem certeza que deseja limpar o banco de dados?\n\nEsta ação removerá todos os registros do banco 'videos.db' e não pode ser desfeita."):
            try:
                # Fecha a conexão com o banco de dados ANTES de remover o arquivo
                if self.cursor:
                    self.cursor.close()
                    self.cursor = None
                if self.conn:
                    self.conn.close()
                    self.conn = None
                
                # Aguarda brevemente para garantir que o arquivo foi liberado
                import time
                time.sleep(0.1)
                
                if os.path.exists('videos.db'):
                    os.remove('videos.db')
                    messagebox.showinfo("Sucesso", "Banco de dados 'videos.db' foi removido com sucesso.")
                    # Limpa os dados em memória
                    self.dados_db = []
                    self.dados_m3u = []
                    self.limpar_indices()
                    # Reinicializa o banco de dados
                    self.init_database()
                    # Atualiza a interface para refletir a limpeza
                    for item in self.tree.get_children():
                        self.tree.delete(item)
                    # Adiciona mensagem indicando que o banco está vazio
                    self.tree.insert('', 'end', values=('', 'Banco de dados limpo. Carregue novos dados ou M3U.', '', '', '', '', ''))
                else:
                    messagebox.showinfo("Informação", "O arquivo 'videos.db' não existe.")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao remover o banco de dados: {str(e)}")

    def mostrar_estatisticas(self):
        """Mostra as estatísticas de uso do programa"""
        stats_text = f"""
Estatísticas do Palantir:

Downloads realizados: {self.estatisticas['downloads_realizados']}
Buscas realizadas: {self.estatisticas['buscas_realizadas']}
Erros encontrados: {self.estatisticas['erros_encontrados']}
        """
        messagebox.showinfo("Estatísticas", stats_text)

    def gerar_m3u_automatico(self):
        """Gera playlists M3U automaticamente a partir da pasta de download usando URL base do config.json"""
        import os
        import re
        import json
        from tkinter import messagebox

        # Trava contra execuções múltiplas
        if self.is_generating_m3u:
            messagebox.showwarning("Aguarde", "Já existe uma geração de M3U em andamento. Aguarde concluir.")
            return
        
        # Confirmar com o usuário antes de iniciar
        if not messagebox.askyesno("Confirmar", "Tem certeza que deseja gerar as playlists M3U?\n\nEsta ação irá varrer as pastas FILMES e SERIES na pasta de download e criar arquivos M3U organizados por categoria com URLs completas."):
            return
        
        # Ativa a trava
        self.is_generating_m3u = True

        try:
            # Carregar URL base do config.json
            try:
                try:
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                except json.JSONDecodeError:
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    content = content.replace('\\', '\\\\').replace('\\\\"', '\\"')
                    config = json.loads(content)
                base_url = config.get('m3u_base_url', 'DIGITE AQUI SUA URL').rstrip('/')
            except Exception as e:
                print(f"Aviso: Não foi possível ler m3u_base_url do config.json, usando padrão: {e}")
                base_url = 'DIGITE AQUI SUA URL'

            # Obter a pasta de download configurada
            pasta_base = self.download_path.get()

            if not os.path.exists(pasta_base):
                messagebox.showerror("Erro", f"Pasta de download não encontrada: {pasta_base}")
                self.is_generating_m3u = False
                return

            # Definir subpastas
            pasta_filmes = os.path.join(pasta_base, "FILMES")
            pasta_series = os.path.join(pasta_base, "SERIES")
            
            # Pasta de saída das M3U (dentro da pasta base)
            pasta_saida_m3u = pasta_base

            print(f"\n{'='*60}")
            print(f"📡 URL Base: {base_url}")
            print(f"📁 Pasta Base: {pasta_base}")
            print(f"{'='*60}\n")

            # Função para limpar nome da categoria
            def format_category_name(category):
                """Formata o nome da categoria para o arquivo"""
                category = re.sub(r'[<>:"/\\|?*]', '', category)
                words = category.split()
                formatted_words = []
                for word in words:
                    if word.upper() in ['XXX', 'S.W.A.T.', 'TV']:
                        formatted_words.append(word.upper())
                    else:
                        formatted_words.append(word.capitalize())
                return ' '.join(formatted_words).strip()

            # Função para buscar poster do TMDB
            def buscar_poster_tmdb(nome_video, tipo_conteudo='movie'):
                """Busca o poster do TMDB pelo nome do vídeo"""
                try:
                    api_key = self.tmdb_api_key.get()
                    if not api_key:
                        return ""

                    # Limpar o nome para busca
                    nome_limpo = re.sub(r'\.(mp4|mkv|avi|mov|wmv|flv|webm|m4v)$', '', nome_video, flags=re.IGNORECASE)
                    nome_limpo = re.sub(r'\s*\(\d{4}\)\s*$', '', nome_limpo)  # Remove ano no final
                    nome_limpo = re.sub(r'\s*S\d+E\d+.*$', '', nome_limpo, flags=re.IGNORECASE)  # Remove temporada/episódio

                    # Determinar tipo de busca (movie ou tv)
                    if tipo_conteudo == 'SERIES' or 'S' in nome_limpo.upper() and 'E' in nome_limpo.upper():
                        tipo_busca = 'tv'
                    else:
                        tipo_busca = 'movie'

                    # Buscar no TMDB
                    search_url = f"https://api.themoviedb.org/3/search/{tipo_busca}?api_key={api_key}&query={requests.utils.quote(nome_limpo)}&language=pt-BR&include_adult=true"
                    response = requests.get(search_url, timeout=5)

                    if response.status_code == 200:
                        dados = response.json()
                        if dados.get('results') and len(dados['results']) > 0:
                            # Pega o primeiro resultado
                            poster_path = dados['results'][0].get('poster_path')
                            if poster_path:
                                return f"https://image.tmdb.org/t/p/w600_and_h900_bestv2{poster_path}"
                    return ""
                except Exception as e:
                    print(f"Erro ao buscar poster TMDB para '{nome_video}': {e}")
                    return ""

            # Função para varrer pasta e gerar M3U
            def varrer_pasta_para_m3u(pasta_origem, nome_pasta, tipo_conteudo):
                """
                Varre uma pasta e gera arquivos M3U por categoria.
                tipo_conteudo: 'FILMES' ou 'SERIES'
                """
                if not os.path.exists(pasta_origem):
                    print(f"Pasta {nome_pasta} não encontrada: {pasta_origem}")
                    return 0, []

                print(f"\n🔍 Varrendo pasta: {pasta_origem}")

                # Encontrar todos os arquivos de vídeo
                arquivos_video = []
                subpastas_encontradas = set()
                for root, dirs, files in os.walk(pasta_origem):
                    # Mostra todas as subpastas e arquivos encontrados
                    print(f"   📂 Root: {root}")
                    print(f"      Dirs: {dirs}")
                    print(f"      Files: {files}")
                    if dirs:
                        print(f"   Subpastas em {root}: {dirs}")
                    for d in dirs:
                        subpastas_encontradas.add(d)
                    for file in files:
                        if file.lower().endswith(('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v')):
                            caminho_completo = os.path.join(root, file)
                            print(f"      ✅ Arquivo vídeo encontrado: {file}")
                            # Calcular caminho relativo à pasta de origem (FILMES ou SERIES)
                            caminho_relativo = os.path.relpath(caminho_completo, pasta_origem)
                            arquivos_video.append(caminho_relativo)
                        else:
                            print(f"      ⚠️ Ignorado (não é vídeo): {file}")

                print(f"\n📂 {nome_pasta}: {len(arquivos_video)} arquivos de vídeo encontrados")
                print(f"📁 Subpastas encontradas: {subpastas_encontradas}")
                for av in arquivos_video[:20]:  # Mostra primeiros 20
                    print(f"   - {av}")
                if len(arquivos_video) > 20:
                    print(f"   ... e mais {len(arquivos_video) - 20} arquivos")

                if not arquivos_video:
                    print(f"Nenhum arquivo de vídeo encontrado em {nome_pasta}")
                    return 0, []

                # Organizar por categorias (subpastas)
                categorias = {}
                for arquivo in arquivos_video:
                    partes = arquivo.split(os.sep)
                    if len(partes) >= 1:  # Pelo menos a categoria
                        categoria = partes[0]  # A primeira parte é a categoria
                        if categoria not in categorias:
                            categorias[categoria] = []
                        categorias[categoria].append(arquivo)

                print(f"📁 Categorias encontradas em {nome_pasta}: {list(categorias.keys())}")

                # Gerar um arquivo M3U para cada categoria
                arquivos_gerados = 0
                arquivos_m3u_gerados = []
                
                for categoria, lista_arquivos in categorias.items():
                    nome_arquivo_m3u = f"{categoria}.m3u"
                    caminho_arquivo_m3u = os.path.join(pasta_saida_m3u, nome_arquivo_m3u)

                    print(f"\n🎬 Gerando {nome_arquivo_m3u} com {len(lista_arquivos)} arquivos...")

                    m3u_content = "#EXTM3U\n"
                    successful_entries = 0

                    for arquivo_video in lista_arquivos:
                        # Extrair nome do vídeo (sem extensão)
                        nome_video = os.path.splitext(os.path.basename(arquivo_video))[0]

                        # Buscar poster do TMDB
                        poster_url = buscar_poster_tmdb(nome_video, tipo_conteudo)

                        # Construir URL completa com forward slashes
                        # URL: DIGITE AQUI SUA URL/FILMES/Acao/filme.mp4 ou DIGITE AQUI SUA URL/SERIES/Drama/serie.mp4
                        url_completa = f"{base_url}/{tipo_conteudo}/{arquivo_video.replace(os.sep, '/')}"

                        # Gerar entrada M3U
                        logo_attr = f' tvg-logo="{poster_url}"' if poster_url else ' tvg-logo=""'
                        extinf = f'#EXTINF:-1 tvg-name="{nome_video}"{logo_attr} group-title="{categoria}",{nome_video}\n'
                        m3u_content += extinf
                        m3u_content += f'{url_completa}\n'
                        successful_entries += 1

                    # Salvar o arquivo M3U
                    with open(caminho_arquivo_m3u, 'w', encoding='utf-8') as f:
                        f.write(m3u_content)

                    arquivos_gerados += 1
                    arquivos_m3u_gerados.append(nome_arquivo_m3u)
                    print(f"  ✅ {nome_arquivo_m3u} salvo com {successful_entries} entradas!")

                return arquivos_gerados, arquivos_m3u_gerados

            # Processar ambas as pastas
            total_arquivos = 0
            total_m3u = 0
            m3u_gerados = []

            print(f"\n{'='*60}")
            print("🎬 Processando FILMES...")
            print(f"{'='*60}")
            if os.path.exists(pasta_filmes):
                arquivos_filmes, m3u_filmes = varrer_pasta_para_m3u(pasta_filmes, "FILMES", "FILMES")
                total_arquivos += arquivos_filmes
                total_m3u += len(m3u_filmes)
                m3u_gerados.extend(m3u_filmes)
                print(f"Processados {arquivos_filmes} arquivos M3U em FILMES")

            print(f"\n{'='*60}")
            print("📺 Processando SERIES...")
            print(f"{'='*60}")
            if os.path.exists(pasta_series):
                arquivos_series, m3u_series = varrer_pasta_para_m3u(pasta_series, "SERIES", "SERIES")
                total_arquivos += arquivos_series
                total_m3u += len(m3u_series)
                m3u_gerados.extend(m3u_series)
                print(f"Processados {arquivos_series} arquivos M3U em SERIES")

            # Mensagem final
            if total_m3u > 0:
                lista_m3u = "\n".join(f"  • {m}" for m in sorted(m3u_gerados))
                messagebox.showinfo(
                    "Sucesso", 
                    f"Geração de M3U concluída!\n\n"
                    f"📄 Total de arquivos M3U gerados: {total_m3u}\n"
                    f"📁 Local: {pasta_saida_m3u}\n\n"
                    f"Arquivos gerados:\n{lista_m3u}"
                )
            else:
                messagebox.showinfo("Informação", "Nenhum arquivo de vídeo encontrado para gerar M3U.")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar playlists M3U: {str(e)}")
            print(f"Erro ao gerar M3U: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Libera a trava
            self.is_generating_m3u = False

    def __del__(self):
        """Limpa os processos ao fechar o programa"""
        try:
            # Encerra o processo do aria2c iniciado pelo programa
            if hasattr(self, 'aria2c_process') and self.aria2c_process:
                if self.aria2c_process.poll() is None:  # Se ainda está rodando
                    self.aria2c_process.terminate()
                    try:
                        self.aria2c_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.aria2c_process.kill()
                    print("aria2c encerrado corretamente")
            else:
                # Mata o processo do aria2c se não tivermos a referência (segurança)
                subprocess.run(['pkill', 'aria2c'],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)

            # Termina o processo MPV se estiver rodando
            if self.mpv_process and self.mpv_process.poll() is None:
                self.mpv_process.terminate()
                self.mpv_process.wait(timeout=5)
                if self.mpv_process.poll() is None:
                    self.mpv_process.kill()

            # Fecha a conexão com o banco de dados
            if self.conn:
                self.conn.close()

        except Exception as e:
            print(f"Erro ao limpar recursos: {e}")

    def atualizar_cache(self, nome, dados):
        """Atualiza o cache em memória com novos dados"""
        if self.db_cache_loaded:
            self.db_cache[nome] = dados

    def remover_do_cache(self, nome):
        """Remove um item do cache em memória"""
        if self.db_cache_loaded and nome in self.db_cache:
            del self.db_cache[nome]

    def inserir_no_banco(self, nome, url, tipo, temporada, username=None, category=None): # Adicionado 'category'
        """Insere um novo registro no banco e atualiza o cache"""
        try:
            # Garante que o banco está conectado
            if self.conn is None or self.cursor is None:
                self.init_database()
                if self.conn is None or self.cursor is None:
                    print("Erro: conexão com o banco de dados não pôde ser inicializada.")
                    return False
            # Garante que temporada não seja None
            if temporada is None:
                temporada = "-"  # Valor padrão quando não há temporada
            # Verifica se o vídeo já existe
            self.cursor.execute('SELECT COUNT(*) FROM videos WHERE name = ?', (nome,))
            if self.cursor.fetchone()[0] > 0:
                # Se existir, atualiza
                self.cursor.execute('''
                    UPDATE videos 
                    SET url = ?, type = ?, season = ?, username = ?, category = ?
                    WHERE name = ?
                ''', (url, tipo, temporada, username, category, nome))
            else:
                # Se não existir, insere
                self.cursor.execute('''
                    INSERT INTO videos (name, url, type, season, username, category)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (nome, url, tipo, temporada, username, category))
            self.conn.commit()
            # Atualiza o cache
            if self.db_cache_loaded:
                self.cursor.execute('SELECT * FROM videos WHERE name = ?', (nome,))
                novo_registro = self.cursor.fetchone()
                if novo_registro:
                    self.atualizar_cache(nome, novo_registro)
            return True
        except Exception as e:
            print(f"Erro ao inserir/atualizar no banco: {str(e)}")
            return False

    def atualizar_no_banco(self, nome, url, tipo, temporada, username=None, category=None): # Adicionado 'category'
        """Atualiza um registro existente no banco e no cache"""
        try:
            # Garante que o banco está conectado
            if self.conn is None or self.cursor is None:
                self.init_database()
                if self.conn is None or self.cursor is None:
                    print("Erro: conexão com o banco de dados não pôde ser inicializada.")
                    return False
            # Garante que temporada não seja None
            if temporada is None:
                temporada = "-"  # Valor padrão quando não há temporada
            self.cursor.execute('''
                UPDATE videos 
                SET url = ?, type = ?, season = ?, username = ?, category = ?
                WHERE name = ?
            ''', (url, tipo, temporada, username, category, nome))
            self.conn.commit()
            # Atualiza o cache
            if self.db_cache_loaded and nome in self.db_cache:
                registro_atual = self.db_cache[nome]
                novo_registro = (registro_atual[0], nome, url, tipo, temporada, username, category, registro_atual[7])
                self.atualizar_cache(nome, novo_registro)
            return True
        except Exception as e:
            print(f"Erro ao atualizar no banco: {str(e)}")
            return False

    def deletar_do_banco(self, nome):
        """Remove um registro do banco e do cache"""
        try:
            # Garante que o banco está conectado
            if self.conn is None or self.cursor is None:
                self.init_database()
                if self.conn is None or self.cursor is None:
                    print("Erro: conexão com o banco de dados não pôde ser inicializada.")
                    return False
            self.cursor.execute('DELETE FROM videos WHERE name = ?', (nome,))
            self.conn.commit()
            # Remove do cache
            self.remover_do_cache(nome)
            return True
        except Exception as e:
            print(f"Erro ao deletar do banco: {str(e)}")
            return False

    def download_selected_advanced(self):
        """Inicia o download avançado dos itens selecionados"""
        try:
            # Reseta o controle de estagnação para começar como se fosse a primeira vez
            self.reset_stagnation_control()

            selected_items = self.tree.selection()
            if not selected_items:
                messagebox.showwarning("Aviso", "Por favor, selecione um vídeo para download.")
                return

            download_path = self.download_path.get()
            base_download_path = self.download_path.get()
            if not os.path.exists(download_path):
                messagebox.showerror("Erro", "Pasta de download inválida.")
                return

            # Cria uma instância do AdvancedDownloader
            self.advanced_downloader = AdvancedDownloader(
                self.root,
                download_path,
                self.user_agent.get(),
                self.dns_server.get()
            )

            # Passa os widgets de progresso
            self.advanced_downloader.set_progress_widgets(
                self.progress_label,
                self.speed_label,
                self.download_info_label
            )

            # Adiciona os vídeos selecionados à fila
            for item in selected_items:
                time.sleep(0.1) # Adiciona um pequeno delay para não sobrecarregar o servidor com HEAD requests
                values = self.tree.item(item)['values']
                if not values or len(values) < 7:
                    continue
                nome_video = values[1]
                url = self.get_url_from_selection(item)

                if url:
                    # Determina o caminho final do arquivo para registrar no DB
                    content_name, season = self.extract_content_info(nome_video)
                    sanitized_content_name = self.sanitize_directory_name(content_name)
                    final_dir = os.path.join(base_download_path, sanitized_content_name)
                    if season:
                        final_dir = os.path.join(final_dir, self.sanitize_directory_name(season))

                    # O AdvancedDownloader pode mudar a extensão, mas registramos com .mp4 como placeholder
                    final_path = os.path.join(final_dir, f"{self.sanitize_directory_name(nome_video)}.mp4")

                if url:
                    # Lógica de registro no DB de trabalhos (similar ao Download 1)
                    try:
                        # 1. Inserir imediatamente no banco de dados com tamanho 0.
                        # O tamanho será atualizado posteriormente pelo worker de download.
                        self._db_execute_jobs(
                            "INSERT OR IGNORE INTO download_jobs (name, url, remote_size) VALUES (?, ?, ?)",
                            (nome_video, url, 0)
                        )
                        print(f"Trabalho registrado em downloads.db para download avançado: {nome_video}")
                        self.advanced_downloader.download_queue.append((nome_video, url, download_path))
                    except Exception as e: # Captura outros erros de DB
                        messagebox.showerror("Erro de Registro", f"Erro ao registrar trabalho de download para {nome_video}: {e}")
                        continue # Pula este item se não conseguir registrar no DB

                else:
                    messagebox.showwarning("Aviso", f"URL não encontrada para o vídeo: {nome_video}")

            # Inicia o processamento da fila
            if not self.advanced_downloader.is_downloading:
                self.advanced_downloader.process_download_queue()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao iniciar download avançado: {str(e)}")

    def find_file_recursively(self, base_path, name_to_find):
        """
        Busca recursivamente por um arquivo cujo nome (sem extensão) comece
        com o nome sanitizado fornecido.
        """
        sanitized_name_to_find = self.sanitize_directory_name(name_to_find)
        for root, dirs, files in os.walk(base_path):
            for file in files:
                # Compara o início do nome do arquivo (sem extensão) com o nome sanitizado
                file_name_without_ext, _ = os.path.splitext(file)
                if self.sanitize_directory_name(file_name_without_ext).startswith(sanitized_name_to_find):
                    return os.path.join(root, file)
        return None
        
    def verificar_e_retomar_pendentes(self):
        """
        Verifica o 'downloads.db' por trabalhos pendentes e os re-enfileira se necessário.
        """
        if self.is_downloading:
            return

        try:
            progress_window = ctk.CTkToplevel(self.root)
            progress_window.title("Verificando Downloads")
            progress_window.transient(self.root)
            progress_window.grab_set()
            progress_window.focus_set()
            progress_window.geometry("500x300")
            
            main_frame = ctk.CTkFrame(progress_window, fg_color="transparent")
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            status_label = ctk.CTkLabel(main_frame, text="Verificando downloads pendentes...")
            status_label.pack(pady=10)

            progress_bar = ctk.CTkProgressBar(main_frame, mode='indeterminate')
            progress_bar.pack(fill=tk.X, padx=10, pady=5)
            progress_bar.start()

            log_text = ctk.CTkTextbox(main_frame, height=150, state="disabled")
            log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            def add_log(message):
                """Adiciona log de forma thread-safe usando after()"""
                try:
                    self.root.after(0, lambda: _add_log_safe(message))
                except:
                    pass  # Ignora se a janela já foi destruída

            def _add_log_safe(message):
                """Função segura para adicionar log na thread principal"""
                try:
                    if log_text.winfo_exists():
                        log_text.configure(state="normal")
                        log_text.insert("end", message + "\n")
                        log_text.configure(state="disabled")
                        log_text.see("end")
                except:
                    pass  # Ignora se a janela já foi destruída

            def run_verification():
                try:
                    # 1. Ler todos os trabalhos do downloads.db
                    local_conn = sqlite3.connect('downloads.db')
                    local_cursor = local_conn.cursor()
                    local_cursor.execute("SELECT name, url, remote_size FROM download_jobs")
                    pending_jobs = local_cursor.fetchall()
                    local_conn.close()

                    if not pending_jobs:
                        add_log("Nenhum trabalho de download pendente encontrado.")
                        self.root.after(2000, progress_window.destroy)
                        return

                    add_log(f"Encontrados {len(pending_jobs)} trabalhos pendentes. Verificando arquivos...")
                    base_download_path = self.download_path.get()

                    to_re_add = []
                    jobs_to_remove = []

                    # 2. Verificar cada trabalho
                    for name, url, remote_size in pending_jobs:
                        try:
                            # 3. Busca recursiva pelo arquivo
                            found_path = self.find_file_recursively(base_download_path, name)

                            if found_path:
                                local_size = os.path.getsize(found_path)
                                # 4. Verificação de sucesso
                                # Considera completo se:
                                # - O tamanho remoto é conhecido (>0) e o local é igual ou maior.
                                # - OU o tamanho remoto é desconhecido (0), mas o arquivo local existe e tem tamanho > 0.
                                if (remote_size > 0 and local_size >= remote_size) or \
                                   (remote_size == 0 and local_size > 0):
                                    add_log(f"OK: '{name}' encontrado e completo. Removendo da lista de trabalhos.")
                                    jobs_to_remove.append(name)
                                else:
                                    add_log(f"INCOMPLETO: '{name}' encontrado, mas com tamanho divergente. Re-enfileirando.")
                                    to_re_add.append((name, url, base_download_path))
                            else:
                                # 5. Verificação de falha (arquivo não encontrado)
                                add_log(f"AUSENTE: '{name}' não encontrado no diretório. Re-enfileirando.")
                                to_re_add.append((name, url, base_download_path))
                        except Exception as e:
                            add_log(f"ERRO ao verificar o trabalho '{name}': {e}")

                    # Re-enfileirar trabalhos pendentes (respeitando o limite de estagnação)
                    requeued_count = 0
                    skipped_count = 0

                    if to_re_add:
                        for name, url, download_dir in to_re_add:
                            # Verifica se ainda pode tentar baseado no contador de estagnação
                            if self.can_retry_download(name):
                                self.increment_retry_count(name)
                                if (name, url, download_dir) not in self.download_queue:
                                    self.download_queue.append((name, url, download_dir))
                                    requeued_count += 1
                            else:
                                # Atingiu o limite de estagnação, remover do DB
                                jobs_to_remove.append(name)
                                skipped_count += 1
                                add_log(f"LIMITE ATINGIDO: '{name}' não será mais retomado ({self.max_retries} ciclos de estagnação).")

                        add_log(f"\n{requeued_count} trabalhos foram re-enfileirados para download.")

                        # Atualiza contador de estagnação baseado na quantidade reenfileirada
                        self.update_stagnation_counter(requeued_count)

                        if skipped_count > 0:
                            add_log(f"{skipped_count} trabalhos foram removidos (limite de estagnação atingido).")

                        # Inicia o processamento da fila novamente se não estiver em andamento
                        if not self.is_downloading:
                            add_log("Reiniciando o processo de download...")
                            self.root.after(100, self.process_download_queue)

                    # Remover trabalhos concluídos e os que atingiram o limite do DB
                    if jobs_to_remove:
                        local_conn = sqlite3.connect('downloads.db')
                        local_cursor = local_conn.cursor()
                        for job_name in jobs_to_remove:
                            local_cursor.execute("DELETE FROM download_jobs WHERE name = ?", (job_name,))
                        local_conn.commit()
                        local_conn.close()
                        add_log(f"\n{len(jobs_to_remove)} trabalhos foram removidos do banco.")

                    add_log("\nVerificação concluída.")
                    self.root.after(3000, progress_window.destroy)

                except Exception as e:
                    add_log(f"ERRO GERAL na verificação: {e}")
                    self.root.after(3000, progress_window.destroy)

            # Inicia a verificação em uma thread para não travar a UI
            threading.Thread(target=run_verification, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao iniciar verificação: {e}")

    def organize_folders(self):
        """Organiza os arquivos de vídeo em pastas por gênero usando módulo externo"""
        try:
            from organize_folders_wrapper import organize_folders_wrapper
            organize_folders_wrapper(self.download_path.get(), self.root)
        except ImportError:
            messagebox.showerror("Erro", "Módulo organize_folders_wrapper.py não encontrado!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao organizar pastas: {e}")

    def limpar_pastas(self):
        """Move arquivos dos subdiretórios para o diretório pai e remove subdiretórios vazios"""
        try:
            from organize_folders_wrapper import clean_folders_wrapper
            clean_folders_wrapper(self.download_path.get(), self.root)
        except ImportError:
            messagebox.showerror("Erro", "Módulo organize_folders_wrapper.py não encontrado!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao limpar pastas: {e}")

    def download_selected_v3(self):
        """Inicia o Download 3 para os itens selecionados (modo urllib)."""
        try:
            # Reseta o controle de estagnação para começar como se fosse a primeira vez
            self.reset_stagnation_control()
            
            selected_items = self.tree.selection()
            if not selected_items:
                messagebox.showwarning("Aviso", "Por favor, selecione um vídeo para download.")
                return

            download_path = self.download_path.get()
            base_download_path = self.download_path.get()
            if not os.path.exists(download_path):
                messagebox.showerror("Erro", "Pasta de download inválida.")
                return

            # Importação tardia para não impactar startup
            try:
                from downloaders.download3 import download3
            except Exception as imp_err:
                messagebox.showerror("Erro", f"Falha ao carregar Download 3: {imp_err}")
                return

            def run_download(item_id):
                try:
                    values = self.tree.item(item_id)['values']
                    if not values or len(values) < 7:
                        return
                    nome_video = values[1]
                    # Tenta obter categoria da tabela; se não existir, busca nos dados M3U
                    category = None
                    try:
                        category = values[5]  # dependendo da configuração das colunas
                        if category and isinstance(category, str) and category.strip():
                            category = category.strip()
                        else:
                            category = None
                    except Exception:
                        category = None
                    if category is None:
                        try:
                            for item_m3u in self.dados_m3u:
                                if item_m3u and len(item_m3u) >= 5 and item_m3u[0] == nome_video:
                                    category = item_m3u[4]
                                    break
                        except Exception:
                            category = None
                    url = self.get_url_from_selection(item_id)
                    if not url or not url.startswith(('http://', 'https://')):
                        return

                    # --- Início: Lógica de Registro em downloads.db ---
                    try:
                        # 1. Obter o tamanho do arquivo remoto
                        # 1. Inserir imediatamente no banco de dados com tamanho 0.
                        # O tamanho será atualizado posteriormente pelo worker de download.
                        self._db_execute_jobs(
                            "INSERT OR IGNORE INTO download_jobs (name, url, remote_size) VALUES (?, ?, ?)",
                            (nome_video, url, 0)
                        )
                        print(f"Trabalho registrado em downloads.db para Download 3: {nome_video}")
                    except Exception as e:
                        self.root.after(0, lambda: messagebox.showerror("Erro de Registro", f"Erro ao registrar trabalho para Download 3: {e}"))
                        return # Não continua se não conseguir registrar
                    # --- Fim: Lógica de Registro ---

                    self.download_info_label.configure(text=f"Download 3: {nome_video}")

                    def on_progress(done, total):
                        try:
                            if total and total > 0:
                                progress = (done / total) * 100.0
                                self.progress_label.configure(text=f"{progress:.1f}%")
                                self.download_progress.set(progress)
                            else:
                                self.progress_label.configure(text=f"{done} bytes")
                        except Exception:
                            pass

                    def on_status(msg):
                        try:
                            # mensagens simples no label de velocidade
                            self.speed_label.configure(text=str(msg))
                        except Exception:
                            pass

                    user_agent = self.user_agent.get() if hasattr(self.user_agent, 'get') else "Mozilla/5.0"
                    output_path = download3(
                        display_name=nome_video,
                        url=url,
                        category=category,
                        base_download_path=base_download_path,
                        user_agent=user_agent,
                        progress_callback=on_progress,
                        status_callback=on_status,
                    )

                    self.root.after(0, lambda: messagebox.showinfo("Concluído", f"Download finalizado em:\n{output_path}"))
                except Exception as err:
                    self.root.after(0, lambda: messagebox.showerror("Erro", f"Falha no Download 3:\n{err}"))

            # Rodar cada item em uma thread para não travar a UI
            for item in selected_items:
                Thread(target=run_download, args=(item,), daemon=True).start()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao iniciar Download 3: {str(e)}")



def signal_handler(signum, frame):
    """Handler para capturar sinais de erro"""
    print(f"\n❌ Sinal {signum} recebido!")
    print("Stack trace:")
    traceback.print_stack(frame)
    
    # Tenta salvar informações de debug
    try:
        with open("crash_log.txt", "w") as f:
            f.write(f"Crash em {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Sinal: {signum}\n")
            f.write("Stack trace:\n")
            traceback.print_stack(frame, file=f)
    except:
        pass
    
    sys.exit(1)

if __name__ == "__main__":
    # Configura handlers de sinal para capturar crashes
    signal.signal(signal.SIGSEGV, signal_handler)
    signal.signal(signal.SIGABRT, signal_handler)
    signal.signal(signal.SIGFPE, signal_handler)
    
    try:
        app = Palantir()
        app.run()
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        traceback.print_exc()
        
        # Salva log de erro
        try:
            with open("error_log.txt", "w") as f:
                f.write(f"Erro em {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Erro: {e}\n")
                traceback.print_exc(file=f)
        except:
            pass
        
        sys.exit(1)
