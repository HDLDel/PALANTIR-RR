import os
import requests
import shutil
import re
import unicodedata
from datetime import datetime
from urllib.parse import quote
from categorias import PASTAS, FOLDER_MAPPING, CATEGORIAS_VALIDAS, normalizar

# Chave da API atualizada
API_KEY = os.environ.get("TMDB_API_KEY", "")
LANGUAGE = "pt-BR"

def normalizar(texto):
    """Remove acentos e coloca em minúsculo para comparação"""
    return unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf-8').lower()

def nome_simplificado(nome):
    """Limpa e simplifica o nome do arquivo para busca"""
    nome = os.path.splitext(nome)[0]
    nome = nome.replace(".", " ").replace("_", " ").replace("-", " ")
    
    # Remove anos entre parênteses
    nome = re.sub(r'\(\d{4}\)', '', nome)
    # Remove [L], (L), LEG e variações
    nome = re.sub(r'\[L\]|\(L\)|\bLEG\b', '', nome, flags=re.IGNORECASE)
    # Remove texto entre parênteses e colchetes
    nome = re.sub(r'\([^)]*\)|\[[^]]*\]', '', nome)
    
    termos_remover = [
        '1080p', '720p', '480p', 'bluray', 'brrip', 'webrip', 'hdtv',
        'x264', 'x265', 'hevc', 'dvdrip', 'dual audio', 'dublado',
        'legendado', 'web-dl', 'hdrip', 'aac', 'mp4', 'mkv',
        'pt-br', 'br', 'dublado', 'legendado', 'bdrip', 'ac3',
        '5.1', '7.1', 'hd', 'sd', 'dts', 'h264', 'h265'
    ]
    
    for termo in termos_remover:
        nome = re.sub(r'\b' + re.escape(termo) + r'\b', '', nome, flags=re.IGNORECASE)
    
    nome = re.sub(r'\s+', ' ', nome)
    return nome.strip()

def contem_4k(nome_arquivo):
    return "4k" in nome_arquivo.lower()

def obter_genero_valido(filme):
    """Obtém o gênero válido mais apropriado para o filme"""
    try:
        # Primeiro tenta buscar em português
        filme_encoded = quote(filme)
        url = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={filme_encoded}&language={LANGUAGE}"
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"❌ Erro na API para {filme} (código: {response.status_code})")
            return "DIVERSOS"

        resultados = response.json().get("results")
        if not resultados:
            # Se não encontrar, tenta buscar em inglês
            url = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={filme_encoded}&language=en-US"
            response = requests.get(url)
            if response.status_code != 200 or not response.json().get("results"):
                print(f"⚠️ Nenhum resultado para {filme}")
                return "DIVERSOS"
            resultados = response.json().get("results")

        id_filme = resultados[0]["id"]

        # Busca detalhes do filme para pegar os gêneros
        url_detalhes = f"https://api.themoviedb.org/3/movie/{id_filme}?api_key={API_KEY}&language={LANGUAGE}"
        response = requests.get(url_detalhes)
        if response.status_code != 200:
            print(f"❌ Erro ao buscar detalhes de {filme}")
            return "DIVERSOS"

        detalhes = response.json()
        generos = detalhes.get("genres", [])

        for genero in generos:
            nome_genero = genero.get("name", "")
            genero_normalizado = normalizar(nome_genero)
            if genero_normalizado in CATEGORIAS_VALIDAS:
                return nome_genero  # Retorna o nome original do gênero

        return "DIVERSOS"

    except Exception as e:
        print(f"❌ Erro ao processar {filme}: {str(e)}")
        return "DIVERSOS"

def mover_para_categoria(caminho_arquivo, genero, pasta_base):
    """Move o arquivo para a pasta correspondente ao seu gênero"""
    # Normaliza o gênero para busca
    genero_normalizado = normalizar(genero)
    
    # Encontra o nome padrão da pasta
    genero_pasta = "Diversos"
    for nome_padrao, variantes in PASTAS.items():
        if genero_normalizado in [normalizar(v) for v in variantes]:
            genero_pasta = nome_padrao  # Usa o nome exato como definido em PASTAS
            break
    
    # Usa o nome exato da pasta como definido em PASTAS
    pasta_destino = os.path.join(pasta_base, genero_pasta)
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)
        print(f"Criada pasta: {pasta_destino}")

    destino = os.path.join(pasta_destino, os.path.basename(caminho_arquivo))
    
    try:
        shutil.move(caminho_arquivo, destino)
        print(f"Movido: {os.path.basename(caminho_arquivo)} → {genero_pasta}/")
    except Exception as e:
        print(f"Falha ao mover {os.path.basename(caminho_arquivo)}: {str(e)}")

def organize_folders(base_dir):
    """
    Organiza os arquivos de vídeo em pastas por gênero.
    
    Args:
        base_dir (str): Diretório base para organização
        
    Returns:
        int: Número de arquivos organizados
    """
    try:
        print(f"Iniciando organização na pasta: {base_dir}")
        formatos_suportados = ('.mp4', '.mkv', '.avi', '.mov', '.wmv')
        arquivos_processados = 0
        arquivos_4k = 0
        arquivos_por_genero = {}

        # Função para processar arquivos em uma pasta
        def processar_pasta(pasta):
            nonlocal arquivos_processados, arquivos_4k
            print(f"Processando pasta: {pasta}")
            
            for item in os.listdir(pasta):
                caminho_completo = os.path.join(pasta, item)
                
                # Se for uma pasta, processa recursivamente
                if os.path.isdir(caminho_completo):
                    processar_pasta(caminho_completo)
                    continue
                
                # Processa apenas arquivos de vídeo
                if item.lower().endswith(formatos_suportados):
                    nome_filme = nome_simplificado(item)
                    print(f"Processando arquivo: {nome_filme}")

                    if contem_4k(item):
                        mover_para_categoria(caminho_completo, "4K", base_dir)
                        arquivos_processados += 1
                        arquivos_4k += 1
                        continue

                    genero = obter_genero_valido(nome_filme)
                    arquivos_por_genero[genero] = arquivos_por_genero.get(genero, 0) + 1
                    mover_para_categoria(caminho_completo, genero, base_dir)
                    arquivos_processados += 1

        # Inicia o processamento recursivo
        processar_pasta(base_dir)
        
        # Resumo
        print("\n=== Resumo da Organização ===")
        print(f"Total de arquivos processados: {arquivos_processados}")
        print(f"Arquivos 4K: {arquivos_4k}")
        print("\nArquivos por gênero:")
        for genero, quantidade in arquivos_por_genero.items():
            print(f"- {genero}: {quantidade} arquivos")
        
        return arquivos_processados

    except Exception as e:
        print(f"Erro ao organizar pastas: {str(e)}")
        return 0

if __name__ == "__main__":
    # Exemplo de uso
    pasta_execucao = os.path.dirname(os.path.abspath(__file__))
    total = organize_folders(pasta_execucao)
    print(f"\nTotal de arquivos organizados: {total}") 