import os
import re
import sys
import gzip
from io import BytesIO
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

def escapeChars(string, is_category=False):
    if not string:
        return None
    string = string.strip()
    if is_category:
        return re.sub(r'[\\/*"<>]', '-', string)
    return re.sub(r'[\\/*"<>|]', '-', string)

def get_series_name(name):
    base_name = re.sub(r'\s*S\d{2}E\d{2}\s*', '', name).strip()
    base_name = re.sub(r'\s*\d+$', '', base_name).strip()
    return base_name

def dlProgress(downloaded, totalSize):
    percent = int(downloaded * 100 / totalSize) if totalSize > 0 else 0
    bar_length = 40
    filled_length = int(bar_length * percent // 100)
    bar = '=' * filled_length + '-' * (bar_length - filled_length)
    sys.stdout.write(f"\r|{bar}| {percent}%")
    sys.stdout.flush()

def download_file(url, filename, headers):
    try:
        req = Request(url, headers=headers)
        with urlopen(req) as response, open(filename, 'wb') as out_file:
            file_size = int(response.getheader('Content-Length', 0))
            downloaded = 0
            block_size = 8192
            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                downloaded += len(buffer)
                out_file.write(buffer)
                dlProgress(downloaded, file_size)
    except HTTPError as e:
        print(f"\nErro HTTP ao baixar {filename}: {e.code}")
    except URLError as e:
        print(f"\nErro URL ao baixar {filename}: {e.reason}")

def download3(display_name, url, category=None, base_download_path="~/Downloads", user_agent=None, progress_callback=None, status_callback=None):
    """
    Função principal para download no estilo 'Download 3'.
    Compatível com a interface CLI existente.
    """
    # Expandir o caminho base
    base_download_path = os.path.expanduser(base_download_path)
    
    if status_callback:
        status_callback(f"Iniciando download: {display_name}")
    
    # Determinar se é série ou filme baseado no nome
    is_series = re.search(r'S\d{2}E\d{2}', display_name) is not None
    
    if is_series:
        # É uma série
        if status_callback:
            status_callback("Processando como série...")
        
        # Extrair informações da série
        series_name = get_series_name(display_name)
        season_episode = re.search(r"S(\d{2})E(\d{2,3})", display_name)
        
        if not season_episode:
            if status_callback:
                status_callback("Formato de série inválido")
            return None
        
        season = season_episode.group(1)
        episode = season_episode.group(2)
        
        # Criar estrutura de pastas
        category_folder_name = escapeChars(category or "Séries", is_category=True)
        series_folder_name = escapeChars(series_name)
        
        if not series_folder_name:
            if status_callback:
                status_callback("Nome de série inválido")
            return None
        
        # Construir caminho completo
        series_folder_path = os.path.join(base_download_path, category_folder_name, series_folder_name, f"S{season}")
        os.makedirs(series_folder_path, exist_ok=True)
        
        filename = os.path.join(series_folder_path, f"{series_folder_name} S{season}E{episode}.mp4")
        
    else:
        # É um filme
        if status_callback:
            status_callback("Processando como filme...")
        
        category_folder_name = escapeChars(category or "Filmes", is_category=True)
        movie_folder = os.path.join(base_download_path, category_folder_name)
        os.makedirs(movie_folder, exist_ok=True)
        
        filename = os.path.join(movie_folder, f"{escapeChars(display_name)}.mp4")
    
    if status_callback:
        status_callback(f"Destino: {filename}")
    
    # Verificar se arquivo já existe
    if os.path.exists(filename):
        if status_callback:
            status_callback("Arquivo já existe, pulando download")
        return filename
    
    # Headers para download
    headers = {
        'User-Agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept-Encoding': 'gzip, deflate',
        'Accept': '*/*',
        'Connection': 'keep-alive'
    }
    
    # Realizar download
    try:
        if status_callback:
            status_callback("Iniciando download...")
        
        download_file(url, filename, headers)
        
        if status_callback:
            status_callback("Download concluído com sucesso!")
        
        return filename
        
    except Exception as e:
        if status_callback:
            status_callback(f"Erro no download: {str(e)}")
        return None

# Função para compatibilidade com o CLI existente
def download3_cli(display_name, url, category=None, base_download_path="~/Downloads", user_agent=None, progress_callback=None, status_callback=None):
    """
    Wrapper para compatibilidade com a interface CLI existente.
    """
    return download3(display_name, url, category, base_download_path, user_agent, progress_callback, status_callback)

if __name__ == "__main__":
    print("---------------------------------")
    print("Bem Vindo a Downloads de VODs V5")
    print("---------------------------------")
    print("Todos os Direitos reservados a Datec Play")
    print("---------------------------------")
    print("Estao prontos criancas?")
    print("---------------------------------")
    print("Estamos Capitao!")

    m3url = input("Digite sua URL: ").strip()
    print()
    print("Movies = 1")
    print("Series = 2")
    vodorseries = input("Digite 1 para Filmes, Digite 2 para Séries: ").strip()

    if vodorseries not in ['1', '2']:
        print("Opção inválida. Tente novamente.")
        sys.exit()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept-Encoding': 'gzip, deflate',
        'Accept': '*/*',
        'Connection': 'keep-alive'
    }

    try:
        req = Request(m3url, headers=headers)
        response = urlopen(req)
        encoding = response.getheader('Content-Encoding')
        raw_data = response.read()

        if encoding == 'gzip':
            buf = BytesIO(raw_data)
            with gzip.GzipFile(fileobj=buf) as f:
                text = f.read().decode('utf-8')
        else:
            text = raw_data.decode('utf-8')

    except HTTPError as e:
        print(f"Erro HTTP: {e.code}")
        sys.exit()
    except URLError as e:
        print(f"Erro URL: {e.reason}")
        sys.exit()

    lines = [line for line in text.split("\n") if not line.startswith("#EXT-X-SESSION-DATA")]

    if vodorseries == '1':
        print("Carregando categorias de Filmes... (não implementado)")
    else:
        print("Carregando categorias de Séries...")
        list_categories = []

        for i in range(len(lines)):
            if lines[i].startswith("#EXTINF") and i + 1 < len(lines) and "/series/" in lines[i + 1]:
                infos = re.search(r'group-title="([^"]+)"', lines[i])
                if infos:
                    category = infos.group(1).replace("SRS | ", "").strip()
                    if category and category not in list_categories:
                        list_categories.append(category)

        print("\nCategorias encontradas:")
        for category in list_categories:
            print(f"- {category}")

        chosen_category = input("\nEscolha uma categoria: ").strip()
        if chosen_category not in list_categories:
            print("Categoria inválida.")
            sys.exit()

        category_folder_name = escapeChars(chosen_category, is_category=True)
        if not category_folder_name:
            print("Nome de categoria inválido após limpeza.")
            sys.exit()

        category_folder = os.path.join('~/series/', category_folder_name)
        if not os.path.exists(category_folder):
            print(f"Criando categoria: {category_folder}")
            os.makedirs(category_folder, exist_ok=True)

        for i in range(len(lines)):
            if lines[i].startswith("#EXTINF") and i + 1 < len(lines) and "/series/" in lines[i + 1]:
                infos = re.search(r'group-title="([^"]+)"', lines[i])
                if not infos:
                    continue

                category = infos.group(1).replace("SRS | ", "").strip()
                if category != chosen_category:
                    continue

                name = lines[i].split(",")[-1].strip()
                season_episode = re.search(r"S(\d{2})E(\d{2,3})", name)
                if not season_episode:
                    print(f"Sem SxxExx em: {name} — ignorado")
                    continue

                season = season_episode.group(1)
                episode = season_episode.group(2)

                series_name = get_series_name(name)
                if not series_name:
                    print(f"Nome de série vazio para: {name} — ignorado")
                    continue

                series_folder_name = escapeChars(series_name)
                if not series_folder_name:
                    print(f"Nome de pasta inválido para: {series_name} — ignorado")
                    continue

                series_folder_path = os.path.join(category_folder, series_name)
                if not os.path.exists(series_folder_path):
                    print(f"Criando pasta da série: {series_folder_path}")
                    os.makedirs(series_folder_path, exist_ok=True)

                season_folder_path = os.path.join(series_folder_path, f"S{season}")
                if not os.path.exists(season_folder_path):
                    print(f"Criando pasta da temporada: {season_folder_path}")
                    os.makedirs(season_folder_path, exist_ok=True)

                filename = os.path.join(
                    season_folder_path,
                    f"{series_folder_name} S{season}E{episode}.mp4"
                )

                file_url = lines[i + 1].strip()
                print(f"\nBaixando: {filename}")

                if not os.path.exists(filename):
                    download_file(file_url, filename, headers)
                    print(f"\nDownload concluído: {filename}")
                else:
                    print(f"Arquivo já existe: {filename}")


