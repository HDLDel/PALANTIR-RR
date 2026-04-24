"""
Módulo PlayerManager - Responsável por gerenciar a reprodução de vídeos
"""
import os
import subprocess
import traceback
import platform
import sys
from tkinter import messagebox


def get_base_dir():
    """Obtém o diretório base, funcionando tanto para script quanto para executável PyInstaller"""
    if getattr(sys, 'frozen', False):
        # Modo executável compilado
        return os.path.dirname(sys.executable)
    else:
        # Modo script normal
        return os.path.dirname(os.path.abspath(__file__))


class PlayerManager:
    def __init__(self):
        """Inicializa o PlayerManager"""
        self.mpv_process = None
        self.player_type = "mpv_appimage"

        # Configura os caminhos dos players (relativo ao executável, não ao script)
        base_dir = get_base_dir()

        if os.name == 'nt':
            # Windows: players da pasta Players (sem busca na raiz)
            self.mpv_path = os.path.join(base_dir, 'Players', 'mpv', 'mpv.exe')
            self.vlc_path = os.path.join(base_dir, 'Players', 'VLCPortable', 'VLCPortable.exe')
            self.mpv_appimage_path = os.path.join(base_dir, 'Players', 'mpv.AppImage')
        else:
            # Linux: MPV do PATH do sistema, AppImages da pasta Players
            self.mpv_path = "mpv"  # PATH do sistema
            self.vlc_path = os.path.join(base_dir, 'Players', 'VLC.AppImage')
            self.mpv_appimage_path = os.path.join(base_dir, 'Players', 'mpv.AppImage')
    
    def set_player_type(self, player_type):
        """Define o tipo de player a ser usado"""
        self.player_type = player_type
    
    def get_player_type(self):
        """Retorna o tipo de player atual"""
        return self.player_type
    
    def get_supported_players(self):
        """Retorna a lista de players suportados"""
        return ["MPV AppImage", "VLC AppImage", "MPV (Sistema)"]
    
    def play_video(self, url):
        """
        Reproduz um vídeo usando o player selecionado em um subprocesso
        
        Args:
            url: URL do vídeo a ser reproduzido
            
        Returns:
            bool: True se o player foi iniciado com sucesso, False caso contrário
        """
        try:
            # Encerra o processo do player anterior se estiver rodando
            if self.mpv_process and self.mpv_process.poll() is None:
                self.mpv_process.terminate()
                self.mpv_process.wait()
            
            player_executable = ""
            player_args = []

            # Configura os argumentos baseados no player selecionado
            if self.player_type == "MPV AppImage":
                player_executable = self.mpv_appimage_path
                player_args = [player_executable, url, '--no-config']
            elif self.player_type == "VLC AppImage":
                player_executable = self.vlc_path
                player_args = [player_executable, url, '--fullscreen', '--no-qt-privacy-ask']
            elif self.player_type == "MPV (Sistema)":
                player_executable = self.mpv_path
                player_args = [player_executable, url, '--no-config']
            else:
                messagebox.showerror("Erro", "Nenhum player selecionado ou player inválido.")
                return False

            # Verifica se o executável do player existe e tem permissão de execução
            if not os.path.exists(player_executable):
                messagebox.showerror("Erro", f"Player não encontrado: {player_executable}")
                return False
            
            if not os.access(player_executable, os.X_OK):
                # Tenta adicionar permissão de execução se for um AppImage
                if player_executable.endswith(".AppImage"):
                    try:
                        os.chmod(player_executable, 0o755)
                        print(f"Permissão de execução adicionada a {player_executable}")
                    except Exception as e:
                        messagebox.showerror("Erro", f"Sem permissão de execução para o player: {player_executable}\nErro: {e}")
                        return False
                else:
                    messagebox.showerror("Erro", f"Sem permissão de execução para o player: {player_executable}")
                    return False

            # Sanitiza a URL para remover aspas simples e duplas que podem causar problemas
            sanitized_url = url.replace("'", "").replace('"', '')
            
            # Substitui a URL original pela sanitizada nos argumentos
            player_args[1] = sanitized_url

            # Inicia o processo do player
            self.mpv_process = subprocess.Popen(player_args)
            print(f"{self.player_type} iniciado. PID: {self.mpv_process.pid}")
            
            return True
            
        except FileNotFoundError:
            messagebox.showerror("Erro", f"{self.player_type} não encontrado. Por favor, certifique-se de que o player está instalado e no seu PATH ou na pasta 'Players'.")
            print(f"Erro FileNotFoundError ao iniciar {self.player_type}.")
            traceback.print_exc()
            return False
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao reproduzir vídeo com {self.player_type}: {str(e)}")
            print(f"Erro geral ao iniciar {self.player_type}: {str(e)}")
            traceback.print_exc()
            return False
    
    def stop_playback(self):
        """Para a reprodução atual"""
        try:
            if self.mpv_process and self.mpv_process.poll() is None:
                self.mpv_process.terminate()
                self.mpv_process.wait(timeout=5)
                if self.mpv_process.poll() is None:
                    self.mpv_process.kill()
                return True
        except Exception as e:
            print(f"Erro ao parar reprodução: {e}")
            return False
        return False
    
    def is_playing(self):
        """Verifica se há reprodução em andamento"""
        return self.mpv_process and self.mpv_process.poll() is None
    
    def cleanup(self):
        """Limpa os recursos do player"""
        self.stop_playback()

# Função de conveniência para criar instância rápida
def create_player_manager(player_type="mpv_appimage"):
    """
    Cria uma instância do PlayerManager com configuração rápida
    
    Args:
        player_type: Tipo de player a ser usado
        
    Returns:
        Instância do PlayerManager configurada
    """
    manager = PlayerManager()
    manager.set_player_type(player_type)
    return manager
