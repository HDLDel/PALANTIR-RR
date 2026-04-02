import os
import json
from typing import Optional, Tuple, Dict, Any

class ConfigManager:
    # Versão atual das configurações
    CONFIG_VERSION = "2.0.0"
    
    # Configurações padrão
    DEFAULT_CONFIG = {
        'version': CONFIG_VERSION,
        'download_path': os.path.expanduser("~/Downloads"),
        'user_agent': "Mozilla/5.0",
        'dns_server': "",
        'theme': "black",
        'player_type': "mpv_appimage"
    }
    
    # Temas disponíveis
    AVAILABLE_THEMES = [
        "arc", "equilux", "breeze", "clearlooks", "elegance", "radiance",
        "plastik", "alt", "classic", "default", "clam", "vista", "winnative",
        "xpnative", "keramik", "keramik_alt", "aquativo", "black", "blue",
        "winxpblue", "ubuntu", "ubuntu-mono-dark", "ubuntu-mono-light",
        "ubuntu-mono", "ubuntu-dark", "ubuntu-light", "ubuntu"
    ]
    
    # Players suportados
    SUPPORTED_PLAYERS = ["MPV AppImage", "VLC AppImage", "MPV (Sistema)"]

    def __init__(self):
        """Inicializa o gerenciador de configurações"""
        self.config_dir = os.path.join(os.path.expanduser('~'), '.config', 'palantir')
        self.config_file = os.path.join(self.config_dir, 'config.json')
        
        # Inicializa com valores padrão
        self.download_path_str = self.DEFAULT_CONFIG['download_path']
        self.user_agent_str = self.DEFAULT_CONFIG['user_agent']
        self.dns_server_str = self.DEFAULT_CONFIG['dns_server']
        self.active_theme = self.DEFAULT_CONFIG['theme']
        self.player_type = self.DEFAULT_CONFIG['player_type']
        
        # Carrega configurações do arquivo
        self.load_config()
        
    def validate_theme(self, theme: str) -> bool:
        """Valida se o tema é suportado"""
        return theme in self.AVAILABLE_THEMES
        
    def validate_player(self, player: str) -> bool:
        """Valida se o player é suportado"""
        return player in self.SUPPORTED_PLAYERS
        
    def validate_path(self, path: str) -> bool:
        """Valida se o caminho é válido"""
        try:
            return os.path.exists(os.path.dirname(path))
        except:
            return False

    def load_config(self) -> Tuple[bool, str]:
        """Carrega as configurações do arquivo"""
        try:
            if not os.path.exists(self.config_file):
                # Cria arquivo de config com valores padrão
                self.save_config()
                return True, "Arquivo de configuração criado com valores padrão"
                
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Verifica versão da configuração
            if config.get('version', '1.0.0') != self.CONFIG_VERSION:
                # Atualiza arquivo para nova versão mantendo valores existentes
                new_config = self.DEFAULT_CONFIG.copy()
                new_config.update({k: v for k, v in config.items() if k in self.DEFAULT_CONFIG})
                config = new_config
                self.save_config(**config)
            
            # Validação de valores
            self.download_path_str = config.get('download_path', self.DEFAULT_CONFIG['download_path'])
            if not self.validate_path(self.download_path_str):
                self.download_path_str = self.DEFAULT_CONFIG['download_path']
                
            self.active_theme = config.get('theme', self.DEFAULT_CONFIG['theme'])
            if not self.validate_theme(self.active_theme):
                self.active_theme = self.DEFAULT_CONFIG['theme']
                
            player = config.get('player_type', self.DEFAULT_CONFIG['player_type'])
            self.player_type = player if self.validate_player(player) else self.DEFAULT_CONFIG['player_type']
            
            self.user_agent_str = config.get('user_agent', self.DEFAULT_CONFIG['user_agent'])
            if not self.validate_user_agent(self.user_agent_str):
                self.user_agent_str = self.DEFAULT_CONFIG['user_agent']
                
            self.dns_server_str = config.get('dns_server', self.DEFAULT_CONFIG['dns_server'])
            if not self.validate_dns_server(self.dns_server_str):
                self.dns_server_str = self.DEFAULT_CONFIG['dns_server']
            
            return True, "Configurações carregadas com sucesso"
            
        except json.JSONDecodeError:
            # Arquivo corrompido - cria novo com valores padrão
            self.reset_to_defaults()
            return False, "Arquivo de configuração corrompido. Usando valores padrão."
        except Exception as e:
            return False, f"Erro ao carregar configurações: {e}"

    def save_config(self, **kwargs) -> Tuple[bool, str]:
        """Salva as configurações com validação"""
        try:
            # Atualiza valores se fornecidos e válidos
            for key, value in kwargs.items():
                if hasattr(self, f'validate_{key}') and getattr(self, f'validate_{key}')(value):
                    setattr(self, f'{key}_str' if key != 'player_type' else key, value)

            # Prepara configurações para salvar
            config = {
                'version': self.CONFIG_VERSION,
                'default_download_path': self.download_path_str,
                'user_agent': self.user_agent_str,
                'dns_server': self.dns_server_str,
                'theme': self.active_theme,
                'player_type': self.player_type
            }
            
            # Garante que o diretório existe
            os.makedirs(self.config_dir, exist_ok=True)
            
            # Salva com encoding UTF-8 e backup
            temp_file = f"{self.config_file}.tmp"
            backup_file = f"{self.config_file}.bak"
            
            # Salva primeiro em arquivo temporário
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            # Faz backup do arquivo atual se existir
            if os.path.exists(self.config_file):
                os.replace(self.config_file, backup_file)
                
            # Move arquivo temporário para posição final
            os.replace(temp_file, self.config_file)
            
            return True, "Configurações salvas com sucesso"
                
        except Exception as e:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return False, f"Erro ao salvar configurações: {e}"

    def change_theme(self, theme_name, root=None, theme_menu=None):
        """
        Muda o tema da aplicação e salva a configuração
        
        Args:
            theme_name: Nome do novo tema
            root: Instância da janela principal (opcional)
            theme_menu: Menu de seleção de tema (opcional)
        """
        try:
            if not self.validate_theme(theme_name):
                return False, "Tema inválido"
                
            self.active_theme = theme_name
            
            # Atualiza o tema na janela se fornecida
            if root:
                root.set_theme(theme_name)
                
            # Atualiza o menu se fornecido    
            if theme_menu:
                theme_menu.set(theme_name)
                
            # Salva a configuração
            self.save_config()
            return True, "Tema alterado com sucesso"
            
        except Exception as e:
            return False, f"Erro ao mudar o tema: {e}"

    def change_player(self, player_name):
        """
        Muda o player de vídeo padrão
        
        Args:
            player_name: Nome do player ("MPV AppImage", "VLC AppImage" ou "MPV (Sistema)")
        """
        try:
            if not self.validate_player(player_name):
                return False, "Player inválido"
                
            self.player_type = player_name
            success, msg = self.save_config(player_type=player_name)  # Salva explicitamente
            if not success:
                return False, f"Erro ao salvar configuração: {msg}"
                
            return True, "Player alterado com sucesso"
        except Exception as e:
            return False, f"Erro ao mudar player: {e}"

    def change_user_agent(self, choice, ua_entry=None):
        """
        Gerencia a mudança de User-Agent
        
        Args:
            choice: Novo user agent ou "Custom..."
            ua_entry: Widget de entrada para UA personalizado (opcional)
        """
        try:
            if choice == "Custom..." and ua_entry:
                # Mostra campo para entrada personalizada
                ua_entry.pack(side="left", padx=5, fill="x", expand=True)
                ua_entry.bind("<Return>", lambda e: self.set_custom_user_agent(ua_entry))
            else:
                # Esconde campo personalizado se existir
                if ua_entry:
                    ua_entry.pack_forget()
                # Define o user agent
                self.user_agent_str = choice
                self.save_config()
            return True, "User Agent atualizado"
        except Exception as e:
            return False, f"Erro ao mudar User Agent: {e}"

    def set_custom_user_agent(self, ua_entry):
        """
        Define um User-Agent personalizado
        
        Args:
            ua_entry: Widget de entrada contendo o UA personalizado
        """
        try:
            custom_ua = ua_entry.get().strip()
            if custom_ua:
                self.user_agent_str = custom_ua
                ua_entry.pack_forget()
                self.save_config()
                return True, "User Agent personalizado definido"
            return False, "User Agent não pode ser vazio"
        except Exception as e:
            return False, f"Erro ao definir User Agent: {e}"

    def get_config(self) -> Dict[str, Any]:
        """Retorna todas as configurações atuais"""
        return {
            'default_download_path': self.download_path_str,
            'user_agent': self.user_agent_str,
            'dns_server': self.dns_server_str,
            'theme': self.active_theme,
            'player_type': self.player_type
        }

    def reset_to_defaults(self) -> Tuple[bool, str]:
        """Reseta todas as configurações para os valores padrão"""
        try:
            self.download_path_str = self.DEFAULT_CONFIG['download_path']
            self.user_agent_str = self.DEFAULT_CONFIG['user_agent']
            self.dns_server_str = self.DEFAULT_CONFIG['dns_server']
            self.active_theme = self.DEFAULT_CONFIG['theme']
            self.player_type = self.DEFAULT_CONFIG['player_type']
            
            return self.save_config()
        except Exception as e:
            return False, f"Erro ao resetar configurações: {e}"

    def validate_user_agent(self, user_agent: str) -> bool:
        """Valida se o user agent é válido"""
        return bool(user_agent and isinstance(user_agent, str) and len(user_agent.strip()) > 0)

    def validate_dns_server(self, dns: str) -> bool:
        """Valida se o servidor DNS é válido"""
        import re
        if not dns:
            return True  # DNS vazio é permitido
        # Validação básica de IP
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        return bool(re.match(ip_pattern, dns))

    def update_config(self, **kwargs) -> Tuple[bool, str]:
        """
        Atualiza múltiplas configurações de uma vez
        Retorna (sucesso, mensagem)
        """
        try:
            changes = {}
            
            # Valida cada configuração antes de aplicar
            for key, value in kwargs.items():
                if key == 'download_path' and self.validate_path(value):
                    changes[key] = value
                elif key == 'theme' and self.validate_theme(value):
                    changes[key] = value
                elif key == 'player_type' and self.validate_player(value):
                    changes[key] = value
                elif key == 'user_agent' and self.validate_user_agent(value):
                    changes[key] = value
                elif key == 'dns_server' and self.validate_dns_server(value):
                    changes[key] = value
                else:
                    return False, f"Valor inválido para {key}: {value}"
            
            # Se chegou aqui, todas as validações passaram
            return self.save_config(**changes)
            
        except Exception as e:
            return False, f"Erro ao atualizar configurações: {e}"
