#!/usr/bin/env python3
"""
Módulo independente para organizar pastas de vídeos por gênero
Pode ser executado separadamente para evitar congelamento do programa principal
"""

import os
import re
import shutil
import time
import requests
import unicodedata
import json
import sys
from urllib.parse import quote
from unidecode import unidecode

# Importa as categorias do módulo principal, que é a única fonte.
# Se este import falhar, o script irá parar, o que é o comportamento desejado
# para garantir que o código não execute com dados de categoria inconsistentes.
from categorias import PASTAS, normalizar, CATEGORIAS_VALIDAS

def setup_logging(log_dir="logs"):
    """Configura o sistema de logging"""
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, f"organize_folders_{time.strftime('%Y%m%d_%H%M%S')}.log")
    
    def log_message(message, level="INFO"):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
        except Exception as e:
            print(f"Erro ao escrever no log: {e}")
    
    return log_message

def nome_simplificado(nome):
    """Limpa e simplifica o nome do arquivo para busca"""
    nome = os.path.splitext(nome)[0]
    nome = nome.replace(".", " ").replace("_", " ").replace("-", " ")
    
    # Remove anos entre parênteses ou colchetes
    nome = re.sub(r'[\[\(]\d{4}[\]\)]', '', nome)
    
    # Remove anos soltos (4 dígitos)
    nome = re.sub(r'\b\d{4}\b', '', nome)
    
    # Remove indicadores de qualidade
    qualidade_patterns = [
        r'\b\d{3,4}p\b',  # 720p, 1080p, etc
        r'\bHD\b',        # HD
        r'\bFHD\b',       # FHD
        r'\bUHD\b',       # UHD
        r'\b4K\b',        # 4K
        r'\bHDR\b',       # HDR
        r'\bWEB-DL\b',    # WEB-DL
        r'\bWEBRIP\b',    # WEBRIP
        r'\bBRRIP\b',     # BRRIP
        r'\bHDRIP\b',     # HDRIP
        r'\bDVDRIP\b',    # DVDRIP
        r'\bBLURAY\b',    # BLURAY
        r'\bREMUX\b',     # REMUX
        r'\bPROPER\b',    # PROPER
        r'\bREPACK\b',    # REPACK
        r'\bRESTORED\b',  # RESTORED
        r'\bEXTENDED\b',  # EXTENDED
        r'\bUNCUT\b',     # UNCUT
        r'\bDIRECTORS\s*CUT\b',  # DIRECTORS CUT
        r'\bDC\b',        # DC
        r'\bIMAX\b',      # IMAX
        r'\bDUBBED\b',    # DUBBED
        r'\bDUB\b',       # DUB
        r'\bSUBBED\b',    # SUBBED
        r'\bSUB\b',       # SUB
        r'\bLEG\b',       # LEG
        r'\[L\]',         # [L]
        r'\(L\)',         # (L)
        r'\bDTS\b',       # DTS
        r'\bAC3\b',       # AC3
        r'\bAAC\b',       # AAC
        r'\bx264\b',      # x264
        r'\bx265\b',      # x265
        r'\bHEVC\b',      # HEVC
        r'\bH264\b',      # H264
        r'\bH265\b',      # H265
        r'\b10bit\b',     # 10bit
        r'\b8bit\b',      # 8bit
        r'\bDD5\.1\b',    # DD5.1
        r'\bDD2\.0\b',    # DD2.0
        r'\bDTS-HD\b',    # DTS-HD
        r'\bDTS-X\b',     # DTS-X
        r'\bATMOS\b',     # ATMOS
        r'\bAAC2\.0\b',   # AAC2.0
        r'\bAAC5\.1\b',   # AAC5.1
    ]
    
    for pattern in qualidade_patterns:
        nome = re.sub(pattern, '', nome, flags=re.IGNORECASE)
    
    # Remove múltiplos espaços
    nome = re.sub(r'\s+', ' ', nome)
    
    # Remove espaços no início e fim
    nome = nome.strip()
    
    return nome

def contem_4k(nome_arquivo):
    """Verifica se o arquivo contém indicação de 4K"""
    return "4k" in nome_arquivo.lower()

def obter_genero_valido(filme, log_func):
    """Obtém o gênero válido mais apropriado para o filme"""
    try:
        log_func(f"🔍 Buscando gênero para: {filme}")
        
        # Chave da API do TMDB
        API_KEY = "<PLACEHOLDER>"
        LANGUAGE = "pt-BR"

        # Timeout para a requisição
        timeout = 10  # 10 segundos
        
        # Primeiro tenta buscar em português
        filme_encoded = quote(filme)
        url = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={filme_encoded}&language={LANGUAGE}"
        
        log_func(f"🌐 Fazendo requisição para: {url}")
        response = requests.get(url, timeout=timeout)
        
        if response.status_code != 200:
            log_func(f"❌ Erro na API para {filme} (código: {response.status_code})")
            return "DIVERSOS"

        resultados = response.json().get("results")
        if not resultados:
            log_func(f"⚠️ Nenhum resultado em português para {filme}, tentando inglês...")
            # Se não encontrar, tenta buscar em inglês
            url = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={filme_encoded}&language=en-US"
            response = requests.get(url, timeout=timeout)
            if response.status_code != 200 or not response.json().get("results"):
                log_func(f"⚠️ Nenhum resultado para {filme}")
                return "DIVERSOS"
            resultados = response.json().get("results")

        id_filme = resultados[0]["id"]
        log_func(f"🎬 ID do filme encontrado: {id_filme}")

        # Busca detalhes do filme para pegar os gêneros
        url_detalhes = f"https://api.themoviedb.org/3/movie/{id_filme}?api_key={API_KEY}&language={LANGUAGE}"
        log_func(f"🌐 Buscando detalhes: {url_detalhes}")
        response = requests.get(url_detalhes, timeout=timeout)
        if response.status_code != 200:
            log_func(f"❌ Erro ao buscar detalhes de {filme}")
            return "DIVERSOS"

        detalhes = response.json()
        generos = detalhes.get("genres", [])
        log_func(f"🎭 Gêneros encontrados: {[g.get('name', '') for g in generos]}")

        for genero in generos:
            nome_genero = genero.get("name", "")
            genero_normalizado = unicodedata.normalize('NFD', nome_genero).encode('ascii', 'ignore').decode('utf-8').lower()
            if genero_normalizado in CATEGORIAS_VALIDAS:
                log_func(f"✅ Gênero válido encontrado: {nome_genero}")
                return nome_genero  # Retorna o nome original do gênero

        log_func(f"⚠️ Nenhum gênero válido encontrado para {filme}, usando DIVERSOS")
        return "DIVERSOS"
        
    except requests.exceptions.Timeout:
        log_func(f"⏰ Timeout na API para {filme}")
        return "DIVERSOS"
    except requests.exceptions.RequestException as e:
        log_func(f"🌐 Erro de rede para {filme}: {str(e)}")
        return "DIVERSOS"
    except Exception as e:
        log_func(f"❌ Erro ao processar {filme}: {str(e)}")
        return "DIVERSOS"

def mover_para_categoria(caminho_arquivo, genero, pasta_base, log_func):
    """Move o arquivo para a pasta correspondente ao seu gênero"""
    try:
        log_func(f"📁 Movendo arquivo: {os.path.basename(caminho_arquivo)} para gênero: {genero}")
        
        # Verifica se o arquivo ainda existe
        if not os.path.exists(caminho_arquivo):
            log_func(f"❌ Arquivo não encontrado: {caminho_arquivo}")
            return False
        
        # Normaliza o gênero para busca
        genero_normalizado = normalizar(genero)
        log_func(f"🔄 Gênero normalizado: {genero_normalizado}")
        
        # Encontra o nome padrão da pasta
        genero_pasta = "Diversos"
        for nome_padrao, variantes in PASTAS.items():
            if genero_normalizado in [normalizar(v) for v in variantes]:
                genero_pasta = nome_padrao  # Usa o nome exato como definido em PASTAS
                log_func(f"📂 Pasta encontrada: {genero_pasta}")
                break
        
        # Usa o nome exato da pasta como definido em PASTAS
        pasta_destino = os.path.join(pasta_base, genero_pasta)
        log_func(f"🎯 Pasta de destino: {pasta_destino}")
        
        if not os.path.exists(pasta_destino):
            try:
                os.makedirs(pasta_destino)
                log_func(f"✅ Pasta criada: {pasta_destino}")
            except Exception as e:
                log_func(f"❌ Erro ao criar pasta {pasta_destino}: {str(e)}")
                return False

        destino = os.path.join(pasta_destino, os.path.basename(caminho_arquivo))
        log_func(f"📄 Arquivo de destino: {destino}")
        
        # Verifica se já existe um arquivo com o mesmo nome
        if os.path.exists(destino):
            log_func(f"⚠️ Arquivo já existe no destino: {destino}")
            # Adiciona sufixo numérico
            nome, ext = os.path.splitext(os.path.basename(caminho_arquivo))
            i = 1
            while os.path.exists(destino):
                novo_nome = f"{nome}_{i}{ext}"
                destino = os.path.join(pasta_destino, novo_nome)
                i += 1
            log_func(f"🔄 Novo nome do arquivo: {os.path.basename(destino)}")
        
        try:
            shutil.move(caminho_arquivo, destino)
            log_func(f"✅ Movido com sucesso: {os.path.basename(caminho_arquivo)} → {genero_pasta}/")
            return True
        except Exception as e:
            log_func(f"❌ Falha ao mover {os.path.basename(caminho_arquivo)}: {str(e)}")
            return False
            
    except Exception as e:
        log_func(f"❌ Erro geral ao mover arquivo: {str(e)}")
        return False

def organize_folders(base_dir, progress_callback=None, log_callback=None):
    """
    Organiza os arquivos de vídeo em pastas por gênero usando a API do TMDB
    
    Args:
        base_dir: Diretório base para organizar
        progress_callback: Função para atualizar progresso (opcional)
        log_callback: Função para logging (opcional)
    
    Returns:
        dict: Estatísticas da organização
    """
    # Configura logging
    log_func = log_callback if log_callback else setup_logging()
    
    try:
        log_func(f"🎬 Iniciando organização em: {base_dir}")
        
        if not os.path.exists(base_dir):
            log_func(f"❌ Diretório não encontrado: {base_dir}")
            return {"error": "Diretório não encontrado"}
        
        formatos_suportados = ('.mp4', '.mkv', '.avi', '.mov', '.wmv')
        arquivos = [f for f in os.listdir(base_dir) if f.lower().endswith(formatos_suportados)]
        total_arquivos = len(arquivos)
        
        if total_arquivos == 0:
            log_func("ℹ️ Nenhum arquivo encontrado para organizar.")
            return {"arquivos_processados": 0, "arquivos_movidos": 0, "arquivos_4k": 0}
        
        log_func(f"📁 Encontrados {total_arquivos} arquivos para organizar")
        
        arquivos_movidos = 0
        arquivos_4k = 0
        arquivos_por_genero = {}
        
        for i, arquivo in enumerate(arquivos):
            try:
                # Atualiza progresso se callback fornecido
                if progress_callback:
                    progress = (i + 1) / total_arquivos * 100
                    progress_callback(f"Processando: {arquivo}", progress)
                
                caminho_arquivo = os.path.join(base_dir, arquivo)
                nome_filme = nome_simplificado(arquivo)
                log_func(f"\n🎬 Processando: {nome_filme}")
                
                if contem_4k(arquivo):
                    if mover_para_categoria(caminho_arquivo, "4K", base_dir, log_func):
                        log_func(f"✅ Movido para pasta 4K: {arquivo}")
                        arquivos_movidos += 1
                        arquivos_4k += 1
                    continue
                
                genero = obter_genero_valido(nome_filme, log_func)
                arquivos_por_genero[genero] = arquivos_por_genero.get(genero, 0) + 1
                
                if mover_para_categoria(caminho_arquivo, genero, base_dir, log_func):
                    log_func(f"✅ Movido para pasta {genero}: {arquivo}")
                    arquivos_movidos += 1
                
            except Exception as e:
                log_func(f"❌ Erro ao processar {arquivo}: {str(e)}")
                continue
        
        # Mostra resumo
        log_func(f"\n✨ Organização concluída:")
        log_func(f"📦 Total de arquivos processados: {arquivos_movidos}")
        log_func(f"🎥 Arquivos 4K: {arquivos_4k}")
        log_func("\n📊 Arquivos por gênero:")
        for genero, quantidade in arquivos_por_genero.items():
            log_func(f"- {genero}: {quantidade} arquivos")
        
        return {
            "arquivos_processados": total_arquivos,
            "arquivos_movidos": arquivos_movidos,
            "arquivos_4k": arquivos_4k,
            "arquivos_por_genero": arquivos_por_genero
        }
        
    except Exception as e:
        log_func(f"❌ Erro ao organizar pastas: {str(e)}")
        return {"error": str(e)}

def main():
    """Função principal para execução independente"""
    if len(sys.argv) != 2:
        print("Uso: python organize_folders_module.py <diretório>")
        sys.exit(1)
    
    base_dir = sys.argv[1]
    
    if not os.path.exists(base_dir):
        print(f"Erro: Diretório '{base_dir}' não encontrado.")
        sys.exit(1)
    
    print(f"🎬 Iniciando organização de pastas em: {base_dir}")
    print("=" * 50)
    
    def progress_callback(message, progress):
        print(f"[{progress:.1f}%] {message}")
    
    def log_callback(message):
        print(message)
    
    resultado = organize_folders(base_dir, progress_callback, log_callback)
    
    if "error" in resultado:
        print(f"❌ Erro: {resultado['error']}")
        sys.exit(1)
    else:
        print("\n" + "=" * 50)
        print("✅ Organização concluída com sucesso!")
        print(f"📦 Arquivos processados: {resultado['arquivos_processados']}")
        print(f"📁 Arquivos movidos: {resultado['arquivos_movidos']}")
        print(f"🎥 Arquivos 4K: {resultado.get('arquivos_4k', 0)}")

if __name__ == "__main__":
    main() 