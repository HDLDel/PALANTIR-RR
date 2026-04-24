import requests
import re
import json
from urllib.parse import unquote, quote
import time
import os

class M3UGenerator:
    def __init__(self):
        self.tmdb_api_key = "<PLACEHOLDER>"
        self.base_url = "http://xtyre.top"
        self.session = requests.Session()
        
    def extract_movie_info(self, file_path):
        """Extrai informações do filme do caminho do arquivo"""
        # CORREÇÃO: Remove aspas e vírgulas do caminho
        clean_path = file_path.strip().replace('"', '').replace(',', '')
        parts = clean_path.split('/')
        
        if len(parts) >= 2:
            # A categoria é sempre a primeira parte do caminho
            category = parts[0]
            filename = parts[-1]
            
            # Remove extensão do arquivo
            movie_name = os.path.splitext(filename)[0]
            
            # Constrói a URL completa
            full_url = f"{self.base_url}/SERIES/{clean_path}"
            
            return {
                'category': category,
                'movie_name': movie_name,
                'full_url': full_url,
                'file_path': clean_path  # INCLUI file_path
            }
        return None
    
    def search_tmdb(self, title, is_movie=True):
        """Busca informações no TMDB para filmes e séries"""
        clean_name = self.clean_title_name(title)
        
        if is_movie:
            url = "https://api.themoviedb.org/3/search/movie"
        else:
            url = "https://api.themoviedb.org/3/search/tv"
            
        params = {
            'api_key': self.tmdb_api_key,
            'query': clean_name,
            'language': 'pt-BR'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['results']:
                    item = data['results'][0]
                    return {
                        'poster_path': item.get('poster_path', ''),
                        'title': item.get('title' if is_movie else 'name', clean_name),
                        'release_date': item.get('release_date' if is_movie else 'first_air_date', ''),
                        'overview': item.get('overview', '')
                    }
        except Exception as e:
            print(f"Erro ao buscar {clean_name}: {e}")
        
        return None
    
    def clean_title_name(self, title):
        """Limpa o nome para busca no TMDB"""
        # Remove informações de temporada/episódio
        clean_name = re.sub(r'\s*S\d{2}E\d{2}', '', title)
        clean_name = re.sub(r'\s*\(\d{4}\)', '', title)
        clean_name = re.sub(r'\s*\[.*?\]', '', clean_name)
        clean_name = re.sub(r'[^\w\s\-&]', ' ', clean_name)
        clean_name = ' '.join(clean_name.split())
        return clean_name.strip()
    
    def format_category_name(self, category):
        """Formata o nome da categoria para o arquivo"""
        # Remove caracteres inválidos
        category = re.sub(r'[<>:"/\\|?*]', '', category)
        return category.strip()
    
    def generate_m3u_entry(self, movie_info, tmdb_data):
        """Gera uma entrada M3U para um filme"""
        poster_url = ""
        if tmdb_data and tmdb_data.get('poster_path'):
            poster_url = f"https://image.tmdb.org/t/p/w600_and_h900_bestv2{tmdb_data['poster_path']}"
        
        # Remove caracteres problemáticos
        category = movie_info['category'].replace('"', '').replace(',', '')
        movie_name = movie_info['movie_name'].replace('"', '').replace(',', '')
        
        # CORREÇÃO: Gera a entrada sem vírgula no final
        entry = f'#EXTINF:-1 tvg-name="{movie_name}" tvg-logo="{poster_url}" group-title="{category}",{movie_name}\n'
        entry += f'{movie_info["full_url"]}\n'  # APENAS A URL, SEM VÍRGULA
        
        return entry
    
    def extract_season_episode(self, file_path):
        """Extrai temporada e episódio do caminho do arquivo"""
        match = re.search(r'S(\d{1,2})E(\d{1,2})', file_path, re.IGNORECASE)
        if match:
            season = int(match.group(1))
            episode = int(match.group(2))
            return season, episode
        return None, None
    
    def sort_episodes(self, movies):
        """Ordena episódios por temporada e episódio"""
        def get_sort_key(movie_info):
            season, episode = self.extract_season_episode(movie_info['file_path'])
            return (season or 0, episode or 0)
        
        return sorted(movies, key=get_sort_key)
    
    def extract_series_name(self, full_name):
        """Extrai o nome base da série removendo temporada/episódio"""
        # Remove S01E01, S01E02, etc
        series_name = re.sub(r'\s*S\d{1,2}E\d{1,2}', '', full_name, flags=re.IGNORECASE)
        
        # Remove Temporada 1, Season 1, etc
        series_name = re.sub(r'\s*(Temporada|Season)\s*\d+', '', series_name, flags=re.IGNORECASE)
        
        # Remove números entre parênteses (ano)
        series_name = re.sub(r'\s*\(\d{4}\)', '', series_name)
        
        # Remove espaços extras
        series_name = ' '.join(series_name.split())
        
        return series_name.strip()
    
    def organize_movies_by_category(self, movie_list):
        """Organiza os filmes por categoria e por série"""
        categories = {}
        
        for movie_path in movie_list:
            movie_info = self.extract_movie_info(movie_path)
            if movie_info:
                category = movie_info['category'].replace('"', '').replace(',', '')
                if category not in categories:
                    categories[category] = {}
                
                # Extrai o nome base da série (sem temporada/episódio)
                series_name = self.extract_series_name(movie_info['movie_name'])
                
                if series_name not in categories[category]:
                    categories[category][series_name] = []
                
                categories[category][series_name].append(movie_info)
        
        # Ordena as séries por nome e os episódios dentro de cada série
        sorted_categories = {}
        for category, series_dict in categories.items():
            # Ordena séries alfabeticamente
            sorted_series = dict(sorted(series_dict.items()))
            
            # Ordena episódios dentro de cada série
            for series_name, episodes in sorted_series.items():
                sorted_series[series_name] = self.sort_episodes(episodes)
            
            # Cria lista plana com todas as séries ordenadas
            flat_list = []
            for series_name in sorted(sorted_series.keys()):
                flat_list.extend(sorted_series[series_name])
            
            sorted_categories[category] = flat_list
        
        return sorted_categories
    
    def generate_single_category_m3u(self, category_name, movies, output_dir="playlists"):
        """Gera um arquivo M3U para uma categoria específica"""
        formatted_category = self.format_category_name(category_name.replace('"', '').replace(',', ''))
        filename = f"{formatted_category}.m3u"
        filepath = os.path.join(output_dir, filename)
        
        m3u_content = "#EXTM3U\n"
        
        print(f"🎬 Gerando {filename} com {len(movies)} filmes...")
        
        successful_posters = 0
        series_cache = {}
        
        for i, movie_info in enumerate(movies, 1):
            print(f"  [{i}/{len(movies)}] Processando: {movie_info['movie_name']}")
            
            tmdb_data = None
            
            # Busca no TMDB
            if self.is_movie(movie_info['file_path']):
                tmdb_data = self.search_tmdb(movie_info['movie_name'], is_movie=True)
            else:
                series_name = self.clean_title_name(movie_info['movie_name'])
                
                if series_name not in series_cache:
                    series_cache[series_name] = self.search_tmdb(series_name, is_movie=False)
                    time.sleep(0.3)
                
                tmdb_data = series_cache[series_name]
            
            if tmdb_data:
                successful_posters += 1
                print(f"    ✅ Poster encontrado")
            else:
                print(f"    ⚠️  Poster não encontrado")
            
            # Gera entrada M3U
            m3u_entry = self.generate_m3u_entry(movie_info, tmdb_data)
            m3u_content += m3u_entry
        
        # Cria diretório se não existir
        os.makedirs(output_dir, exist_ok=True)
        
        # Salva o arquivo
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        
        print(f"  ✅ {filename} salvo com sucesso! ({successful_posters}/{len(movies)} posters encontrados)")
        return filepath
    
    def is_movie(self, file_path):
        """Verifica se é um filme ou série baseado no caminho"""
        if re.search(r'S\d{1,2}E\d{1,2}', file_path, re.IGNORECASE):
            return False
        if re.search(r'Temporada|Season', file_path, re.IGNORECASE):
            return False
        if re.search(r'/S\d{1,2}/', file_path, re.IGNORECASE):
            return False
        return True
    
    def load_movies_from_file(self, filename="resultadoSERIES.txt"):
        """Carrega a lista de filmes do arquivo resultadoSERIES.txt"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(script_dir, filename)
            
            if not os.path.exists(file_path):
                print(f"❌ Arquivo {filename} não encontrado na pasta do script!")
                return []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                # CORREÇÃO: Remove aspas e vírgulas de cada linha
                movie_list = [line.strip().replace('"', '').replace(',', '') for line in f if line.strip()]
            
            print(f"✅ Carregados {len(movie_list)} filmes de {filename}")
            return movie_list
            
        except Exception as e:
            print(f"❌ Erro ao ler arquivo {filename}: {e}")
            return []
    
    def process_movie_list(self, movie_list, output_dir="playlists"):
        """Processa a lista de filmes e gera arquivos M3U separados por categoria"""
        print("Iniciando processamento...")
        print(f"📁 Gerando arquivos M3U separados em: {output_dir}/")
        
        categories = self.organize_movies_by_category(movie_list)
        
        total_movies = len(movie_list)
        generated_files = []
        
        print(f"\n📊 Encontradas {len(categories)} categorias:")
        for category in categories:
            print(f"   • {category}: {len(categories[category])} filmes")
        
        for category_name, movies in categories.items():
            print(f"\n{'='*50}")
            filepath = self.generate_single_category_m3u(category_name, movies, output_dir)
            generated_files.append(filepath)
        
        print(f"\n{'='*50}")
        print("✅ Processamento concluído!")
        print(f"📁 Total de categorias processadas: {len(categories)}")
        print(f"🎬 Total de filmes processados: {total_movies}")
        
        print("\n📄 Arquivos gerados:")
        for filepath in generated_files:
            filename = os.path.basename(filepath)
            print(f"   • {filename}")
    
    def process_from_file(self, input_file="resultadoSERIES.txt", output_dir="playlists"):
        """Processa filmes diretamente do arquivo resultadoSERIES.txt"""
        movie_list = self.load_movies_from_file(input_file)
        
        if movie_list:
            self.process_movie_list(movie_list, output_dir)
        else:
            print("❌ Nenhum filme para processar!")

# Versão alternativa sem API do TMDB
class SimpleM3UGenerator:
    def __init__(self):
        self.base_url = "http://xtyre.top"
    
    def extract_movie_info(self, file_path):
        """Extrai informações do filme do caminho do arquivo"""
        clean_path = file_path.strip().replace('"', '').replace(',', '')
        parts = clean_path.split('/')
        
        if len(parts) >= 2:
            category = parts[0]
            filename = parts[-1]
            movie_name = os.path.splitext(filename)[0]
            
            full_url = f"{self.base_url}/SERIES/{clean_path}"
            
            # CORREÇÃO: Inclui 'file_path' no dicionário
            return {
                'category': category,
                'movie_name': movie_name,
                'full_url': full_url,
                'file_path': clean_path  # ADICIONA ESTA LINHA
            }
        return None
    
    def format_category_name(self, category):
        """Formata o nome da categoria para o arquivo"""
        category = re.sub(r'[<>:"/\\|?*]', '', category)
        return category.strip()
    
    def generate_m3u_entry(self, movie_info):
        """Gera uma entrada M3U sem poster do TMDB"""
        category = movie_info['category'].replace('"', '').replace(',', '')
        movie_name = movie_info['movie_name'].replace('"', '').replace(',', '')
        
        entry = f'#EXTINF:-1 tvg-name="{movie_name}" tvg-logo="" group-title="{category}",{movie_name}\n'
        entry += f'{movie_info["full_url"]}\n'  # SEM VÍRGULA
        
        return entry
    
    def extract_season_episode(self, file_path):
        """Extrai temporada e episódio do caminho do arquivo"""
        match = re.search(r'S(\d{1,2})E(\d{1,2})', file_path, re.IGNORECASE)
        if match:
            season = int(match.group(1))
            episode = int(match.group(2))
            return season, episode
        return None, None
    
    def sort_episodes(self, movies):
        """Ordena episódios por temporada e episódio"""
        def get_sort_key(movie_info):
            season, episode = self.extract_season_episode(movie_info['file_path'])
            return (season or 0, episode or 0)
        
        return sorted(movies, key=get_sort_key)
    
    def extract_series_name(self, full_name):
        """Extrai o nome base da série removendo temporada/episódio"""
        series_name = re.sub(r'\s*S\d{1,2}E\d{1,2}', '', full_name, flags=re.IGNORECASE)
        series_name = re.sub(r'\s*(Temporada|Season)\s*\d+', '', series_name, flags=re.IGNORECASE)
        series_name = re.sub(r'\s*\(\d{4}\)', '', series_name)
        series_name = ' '.join(series_name.split())
        return series_name.strip()
    
    def organize_movies_by_category(self, movie_list):
        """Organiza os filmes por categoria e por série"""
        categories = {}
        
        for movie_path in movie_list:
            movie_info = self.extract_movie_info(movie_path)
            if movie_info:
                category = movie_info['category'].replace('"', '').replace(',', '')
                if category not in categories:
                    categories[category] = {}
                
                # Extrai o nome base da série
                series_name = self.extract_series_name(movie_info['movie_name'])
                
                if series_name not in categories[category]:
                    categories[category][series_name] = []
                
                categories[category][series_name].append(movie_info)
        
        # Ordena as séries por nome e os episódios dentro de cada série
        sorted_categories = {}
        for category, series_dict in categories.items():
            # Ordena séries alfabeticamente
            sorted_series = dict(sorted(series_dict.items()))
            
            # Ordena episódios dentro de cada série
            for series_name, episodes in sorted_series.items():
                sorted_series[series_name] = self.sort_episodes(episodes)
            
            # Cria lista plana com todas as séries ordenadas
            flat_list = []
            for series_name in sorted(sorted_series.keys()):
                flat_list.extend(sorted_series[series_name])
            
            sorted_categories[category] = flat_list
        
        return sorted_categories
    
    def generate_single_category_m3u(self, category_name, movies, output_dir="playlists_simples"):
        """Gera um arquivo M3U para uma categoria específica (sem TMDB)"""
        formatted_category = self.format_category_name(category_name.replace('"', '').replace(',', ''))
        filename = f"{formatted_category}.m3u"
        filepath = os.path.join(output_dir, filename)
        
        m3u_content = "#EXTM3U\n"
        
        print(f"🎬 Gerando {filename} com {len(movies)} filmes...")
        
        for i, movie_info in enumerate(movies, 1):
            season, episode = self.extract_season_episode(movie_info['file_path'])
            if season and episode:
                print(f"  [{i}/{len(movies)}] S{season:02d}E{episode:02d} - {movie_info['movie_name']}")
            else:
                print(f"  [{i}/{len(movies)}] {movie_info['movie_name']}")
            
            m3u_entry = self.generate_m3u_entry(movie_info)
            m3u_content += m3u_entry
        
        os.makedirs(output_dir, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        
        print(f"  ✅ {filename} salvo com sucesso!")
        return filepath
    
    def load_movies_from_file(self, filename="resultadoSERIES.txt"):
        """Carrega a lista de filmes do arquivo resultadoSERIES.txt"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(script_dir, filename)
            
            if not os.path.exists(file_path):
                print(f"❌ Arquivo {filename} não encontrado na pasta do script!")
                return []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                movie_list = [line.strip().replace('"', '').replace(',', '') for line in f if line.strip()]
            
            print(f"✅ Carregados {len(movie_list)} filmes de {filename}")
            return movie_list
            
        except Exception as e:
            print(f"❌ Erro ao ler arquivo {filename}: {e}")
            return []
    
    def process_movie_list(self, movie_list, output_dir="playlists_simples"):
        """Processa a lista de filmes e gera arquivos M3U separados por categoria (sem TMDB)"""
        print("Iniciando processamento (versão simples)...")
        print(f"📁 Gerando arquivos M3U separados em: {output_dir}/")
        
        categories = self.organize_movies_by_category(movie_list)
        
        total_movies = len(movie_list)
        generated_files = []
        
        print(f"\n📊 Encontradas {len(categories)} categorias:")
        for category in categories:
            print(f"   • {category}: {len(categories[category])} filmes")
        
        for category_name, movies in categories.items():
            print(f"\n{'='*50}")
            filepath = self.generate_single_category_m3u(category_name, movies, output_dir)
            generated_files.append(filepath)
        
        print(f"\n{'='*50}")
        print("✅ Processamento concluído!")
        print(f"📁 Total de categorias processadas: {len(categories)}")
        print(f"🎬 Total de filmes processados: {total_movies}")
        
        print("\n📄 Arquivos gerados:")
        for filepath in generated_files:
            filename = os.path.basename(filepath)
            print(f"   • {filename}")
    
    def process_from_file(self, input_file="resultadoSERIES.txt", output_dir="playlists_simples"):
        """Processa filmes diretamente do arquivo resultadoSERIES.txt"""
        movie_list = self.load_movies_from_file(input_file)
        
        if movie_list:
            self.process_movie_list(movie_list, output_dir)
        else:
            print("❌ Nenhum filme para processar!")

# Exemplo de uso
def main():
    print("=== GERADOR COM TMDB (ARQUIVOS SEPARADOS COM POSTERS) ===")
    generator = M3UGenerator()
    generator.process_from_file("resultadoSERIES.txt", "playlists_com_posters")
    
    print("\n=== GERADOR SIMPLES (ARQUIVOS SEPARADOS SEM POSTERS) ===")
    simple_generator = SimpleM3UGenerator()
    simple_generator.process_from_file("resultadoSERIES.txt", "playlists_sem_posters")

if __name__ == "__main__":
    main()
