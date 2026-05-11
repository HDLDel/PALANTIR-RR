"""
Módulo para organização e manipulação de arquivos e diretórios.
Contém funções utilitárias para sanitização de nomes, extração de informações e limpeza.
"""

import os
import re
from typing import Tuple, Optional


def sanitize_directory_name(name: str) -> str:
    """
    Remove caracteres inválidos de nomes de diretórios mantendo a estrutura do nome.
    
    Args:
        name: Nome do diretório a ser sanitizado
        
    Returns:
        Nome sanitizado seguro para uso em sistemas de arquivos
    """
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


def extract_content_info(name: str) -> Tuple[str, Optional[str]]:
    """
    Extrai informações do conteúdo (nome e temporada) a partir do nome.
    
    Args:
        name: Nome do conteúdo (ex: "Série S01E01 Episódio")
        
    Returns:
        Tuple com (nome_do_conteúdo, temporada) ou (nome_do_conteúdo, None) para filmes
    """
    match = re.search(r"(.*?)\s*(S\d{2})\s*E\d{2}", name)
    if match:
        content_name = match.group(1).strip()
        season = match.group(2).strip()
        return content_name, season
    else:
        return name, None


def clean_folders(base_dir: str) -> int:
    """
    Limpa as pastas de download removendo arquivos de vídeo e pastas vazias.
    
    Args:
        base_dir: Diretório base para limpeza
        
    Returns:
        Número total de itens removidos
    """
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
    
    # Processa os itens
    for item in items_to_remove:
        try:
            if os.path.isfile(item):
                os.remove(item)
            elif os.path.isdir(item):
                os.rmdir(item)
            removed_items += 1
        except Exception as e:
            print(f"Erro ao remover {item}: {e}")
    
    return removed_items


def create_content_folders(base_path: str, content_name: str, season: Optional[str] = None) -> str:
    """
    Cria a estrutura de pastas para o conteúdo.
    
    Args:
        base_path: Caminho base de download
        content_name: Nome do conteúdo
        season: Temporada (opcional)
        
    Returns:
        Caminho completo da pasta onde o arquivo deve ser salvo
    """
    # Sanitiza os nomes
    content_name = sanitize_directory_name(content_name)
    if season:
        season = sanitize_directory_name(season)
    
    # Cria a pasta do conteúdo
    content_folder = os.path.join(base_path, content_name)
    if not os.path.exists(content_folder):
        os.makedirs(content_folder)
    
    # Se for uma série, cria a pasta da temporada
    if season:
        season_folder = os.path.join(content_folder, season)
        if not os.path.exists(season_folder):
            os.makedirs(season_folder)
        return season_folder
    else:
        return content_folder


def get_safe_file_path(base_path: str, content_name: str, file_name: str, season: Optional[str] = None) -> str:
    """
    Retorna um caminho seguro para salvar o arquivo.
    
    Args:
        base_path: Caminho base de download
        content_name: Nome do conteúdo
        file_name: Nome do arquivo
        season: Temporada (opcional)
        
    Returns:
        Caminho completo seguro para o arquivo
    """
    # Cria a estrutura de pastas
    content_folder = create_content_folders(base_path, content_name, season)
    
    # Sanitiza o nome do arquivo
    safe_file_name = sanitize_directory_name(file_name)
    
    return os.path.join(content_folder, f"{safe_file_name}.mp4")
