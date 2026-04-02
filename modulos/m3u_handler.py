"""
Módulo M3UHandler - Responsável por processar arquivos M3U
Depende do DatabaseManager para inserir dados no banco
"""
import re
import requests
import threading
from typing import List, Tuple, Optional
import sqlite3
import os
from urllib.parse import urlparse
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class M3UHandler:
    def __init__(self, database_manager=None):
        """
        Inicializa o M3UHandler
        
        Args:
            database_manager: Instância do DatabaseManager para operações no banco
        """
        self.database_manager = database_manager
        self.dados_m3u = []
        
    def set_database_manager(self, database_manager):
        """Define o DatabaseManager para operações no banco"""
        self.database_manager = database_manager
    
    def extrair_servidor_e_username(self, url: str) -> Tuple[str, str]:
        """
        Extrai o nome do servidor e username da URL
        
        Args:
            url: URL do vídeo
            
        Returns:
            Tuple contendo (servidor, username)
        """
        try:
            # Remove o protocolo (http:// ou https://)
            url_sem_protocolo = re.sub(r'^https?://', '', url)
            
            # Divide a URL em partes
            partes = url_sem_protocolo.split('/')
            
            # Pega o servidor (primeira parte)
            servidor = partes[0].split(':')[0] if partes else "Desconhecido"
            
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
        except Exception as e:
            logger.error(f"Erro ao extrair servidor e username: {e}")
            return "Desconhecido", "N/A"
    
    def processar_linhas_m3u(self, linhas: List[str]) -> List[Tuple]:
        """
        Processa as linhas de um arquivo M3U e extrai os dados dos vídeos
        
        Args:
            linhas: Lista de linhas do arquivo M3U
            
        Returns:
            Lista de tuplas com dados dos vídeos (nome, tipo, temporada, servidor, categoria, url)
        """
        dados_processados = []
        nome = None
        category = None
        
        for i, linha in enumerate(linhas):
            linha = linha.strip()
            
            if linha.startswith('#EXTINF:'):
                # Extrai o nome do cabeçalho EXTINF
                if 'tvg-name="' in linha:
                    nome_match = re.search('tvg-name="([^"]*)"', linha)
                    if nome_match:
                        nome = nome_match.group(1)
                
                if not nome and ',' in linha:
                    nome = linha.split(',', 1)[1].strip()
                    
                # Extrai a categoria (group-title)
                if 'group-title="' in linha:
                    category_match = re.search('group-title="([^"]*)"', linha)
                    if category_match:
                        category = category_match.group(1)
            
            elif linha and not linha.startswith('#') and nome:
                # Esta é a linha da URL
                tipo = "Filme"
                temporada = "None"
                
                # Verifica se é uma série
                if nome:
                    match = re.search(r"(.*?)\s*(S\d{2})\s*E\d{2}", nome)
                    if match:
                        tipo = "Série"
                        temporada = match.group(2)
                
                # Extrai servidor e username da URL
                servidor, username = self.extrair_servidor_e_username(linha)
                
                # Adiciona aos dados processados
                dados_processados.append((nome, tipo, temporada, servidor, category, linha))
                nome = None  # Reset para próximo item
                category = None
        
        return dados_processados
    
    def carregar_m3u_url(self, url: str, user_agent: str = None) -> List[Tuple]:
        """
        Carrega dados de um arquivo M3U via URL
        
        Args:
            url: URL do arquivo M3U
            user_agent: User-Agent para a requisição HTTP
            
        Returns:
            Lista de tuplas com dados dos vídeos
        """
        try:
            headers = {'User-Agent': user_agent or 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            conteudo = response.text
            linhas = conteudo.split('\n')
            
            return self.processar_linhas_m3u(linhas)
            
        except Exception as e:
            logger.error(f"Erro ao carregar M3U da URL {url}: {e}")
            raise
    
    def carregar_m3u_local(self, caminho_arquivo: str) -> List[Tuple]:
        """
        Carrega dados de um arquivo M3U local
        
        Args:
            caminho_arquivo: Caminho para o arquivo M3U local
            
        Returns:
            Lista de tuplas com dados dos vídeos
        """
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as file:
                linhas = file.readlines()
            
            return self.processar_linhas_m3u(linhas)
            
        except Exception as e:
            logger.error(f"Erro ao carregar M3U local {caminho_arquivo}: {e}")
            raise
    
    def processar_multiplos_links(self, links: List[str], user_agent: str = None) -> dict:
        """
        Processa múltiplos links M3U em paralelo
        
        Args:
            links: Lista de URLs M3U
            user_agent: User-Agent para as requisições HTTP
            
        Returns:
            Dicionário com resultados do processamento
        """
        resultados = {
            'sucesso': {},
            'falhas': []
        }
        
        def processar_link(link):
            try:
                dados = self.carregar_m3u_url(link, user_agent)
                resultados['sucesso'][link] = dados
                logger.info(f"Link processado com sucesso: {link} - {len(dados)} itens")
            except Exception as e:
                resultados['falhas'].append((link, str(e)))
                logger.error(f"Falha ao processar link {link}: {e}")
        
        # Processa os links em threads
        threads = []
        for link in links:
            thread = threading.Thread(target=processar_link, args=(link,))
            threads.append(thread)
            thread.start()
        
        # Aguarda todas as threads terminarem
        for thread in threads:
            thread.join()
        
        return resultados
    
    def inserir_dados_no_banco(self, dados_m3u: List[Tuple], fonte: str = "m3u") -> int:
        """
        Insere os dados processados no banco de dados
        
        Args:
            dados_m3u: Lista de tuplas com dados dos vídeos
            fonte: Fonte dos dados (ex: "m3u", "url")
            
        Returns:
            Número de registros inseridos/atualizados
        """
        if not self.database_manager:
            raise ValueError("DatabaseManager não configurado")
        
        registros_processados = 0
        
        for item in dados_m3u:
            nome, tipo, temporada, servidor, category, url = item
            
            try:
                # Garante que temporada não seja None
                if temporada is None:
                    temporada = "-"
                
                # Insere ou atualiza no banco
                success = self.database_manager.inserir_no_banco(
                    nome=nome,
                    url=url,
                    tipo=tipo,
                    temporada=temporada,
                    username=servidor,
                    category=category
                )
                
                if success:
                    registros_processados += 1
                
            except Exception as e:
                logger.error(f"Erro ao inserir item no banco: {nome} - {e}")
                continue
        
        return registros_processados
    
    def limpar_dados_m3u(self):
        """Limpa os dados M3U em memória"""
        self.dados_m3u = []
    
    def obter_dados_m3u(self) -> List[Tuple]:
        """Retorna os dados M3U processados"""
        return self.dados_m3u
    
    def normalizar_texto(self, text: str) -> str:
        """
        Remove acentos, caracteres especiais e normaliza pontuação do texto
        Mantido para compatibilidade com código existente
        
        Args:
            text: Texto a ser normalizado
            
        Returns:
            Texto normalizado
        """
        import unicodedata
        
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

# Função de conveniência para uso rápido
def criar_m3u_handler_com_db(caminho_db: str = 'videos.db') -> M3UHandler:
    """
    Cria um M3UHandler com DatabaseManager configurado
    
    Args:
        caminho_db: Caminho para o arquivo do banco de dados
        
    Returns:
        Instância do M3UHandler configurada
    """
    from database_manager import DatabaseManager
    
    db_manager = DatabaseManager(caminho_db)
    m3u_handler = M3UHandler(db_manager)
    
    return m3u_handler
