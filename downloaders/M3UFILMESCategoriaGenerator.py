import requests
import re
import json
from urllib.parse import unquote
import time
import os

class M3UGenerator:
    def __init__(self):
        self.tmdb_api_key = os.environ.get("TMDB_API_KEY", "")
        self.base_url = "http://xtyre.top"
        self.session = requests.Session()
        
    def extract_movie_info(self, file_path):
        """Extrai informações do filme do caminho do arquivo"""
        parts = file_path.strip().split('/')
        
        if len(parts) >= 2:
            category = parts[0]
            filename = parts[-1]
            movie_name = filename.replace('.mp4', '')
            full_url = f"{self.base_url}/FILMES/{file_path.strip()}"
            
            return {
                'category': category,
                'movie_name': movie_name,
                'full_url': full_url
            }
        return None
    
    def search_tmdb_movie(self, movie_name):
        """Busca informações do filme no TMDB"""
        clean_name = self.clean_movie_name(movie_name)
        
        url = "https://api.themoviedb.org/3/search/movie"
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
                    movie = data['results'][0]
                    return {
                        'poster_path': movie.get('poster_path', ''),
                        'title': movie.get('title', clean_name),
                        'release_date': movie.get('release_date', ''),
                        'overview': movie.get('overview', '')
                    }
        except Exception as e:
            print(f"Erro ao buscar {clean_name}: {e}")
        
        return None
    
    def clean_movie_name(self, movie_name):
        """Limpa o nome do filme para busca no TMDB"""
        clean_name = re.sub(r'\s*\(\d{4}\)', '', movie_name)
        clean_name = re.sub(r'\s*\[.*?\]', '', clean_name)
        clean_name = re.sub(r'[^\w\s\-&]', ' ', clean_name)
        clean_name = ' '.join(clean_name.split())
        return clean_name.strip()
    
    def format_category_name(self, category):
        """Formata o nome da categoria para o arquivo"""
        # Remove "Filmes | " se existir
        category = category.replace('Filmes | ', '')
        
        # Remove colchetes e conteúdo dentro
        category = re.sub(r'\s*\[.*?\]', '', category)
        
        # Remove caracteres inválidos para nome de arquivo
        category = re.sub(r'[<>:"/\\|?*]', '', category)
        
        # Capitaliza palavras
        words = category.split()
        formatted_words = []
        for word in words:
            if word.upper() in ['XXX', 'S.W.A.T.']:
                formatted_words.append(word.upper())
            else:
                formatted_words.append(word.capitalize())
        
        return ' '.join(formatted_words).strip()
    
    def generate_m3u_entry(self, movie_info, tmdb_data):
        """Gera uma entrada M3U para um filme"""
        poster_url = ""
        if tmdb_data and tmdb_data.get('poster_path'):
            poster_url = f"https://image.tmdb.org/t/p/w600_and_h900_bestv2{tmdb_data['poster_path']}"
        
        category = self.format_category_name(movie_info['category'])
        
        entry = f'#EXTINF:-1 tvg-name="{movie_info["movie_name"]}" tvg-logo="{poster_url}" group-title="Filmes | {category}",{movie_info["movie_name"]}\n'
        entry += f'{movie_info["full_url"]}\n'
        
        return entry
    
    def organize_movies_by_category(self, movie_list):
        """Organiza os filmes por categoria"""
        categories = {}
        
        for movie_path in movie_list:
            movie_info = self.extract_movie_info(movie_path)
            if movie_info:
                category = movie_info['category']
                if category not in categories:
                    categories[category] = []
                categories[category].append(movie_info)
        
        return categories
    
    def generate_single_category_m3u(self, category_name, movies, output_dir="playlists"):
        """Gera um arquivo M3U para uma categoria específica"""
        formatted_category = self.format_category_name(category_name)
        filename = f"{formatted_category}.m3u"
        filepath = os.path.join(output_dir, filename)
        
        # Cabeçalho do arquivo M3U
        m3u_content = "#EXTM3U\n"
        
        print(f"🎬 Gerando {filename} com {len(movies)} filmes...")
        
        successful_posters = 0
        
        for i, movie_info in enumerate(movies, 1):
            print(f"  [{i}/{len(movies)}] Buscando: {movie_info['movie_name']}")
            
            # Busca no TMDB
            tmdb_data = self.search_tmdb_movie(movie_info['movie_name'])
            
            if tmdb_data:
                successful_posters += 1
                print(f"    ✅ Poster encontrado")
            else:
                print(f"    ⚠️  Poster não encontrado")
            
            # Gera entrada M3U
            m3u_entry = self.generate_m3u_entry(movie_info, tmdb_data)
            m3u_content += m3u_entry
            
            # Delay para não sobrecarregar a API
            time.sleep(0.3)
        
        # Cria diretório se não existir
        os.makedirs(output_dir, exist_ok=True)
        
        # Salva o arquivo
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        
        print(f"  ✅ {filename} salvo com sucesso! ({successful_posters}/{len(movies)} posters encontrados)")
        return filepath
    
    def process_movie_list(self, movie_list, output_dir="playlists"):
        """Processa a lista de filmes e gera arquivos M3U separados por categoria"""
        print("Iniciando processamento...")
        print(f"📁 Gerando arquivos M3U separados em: {output_dir}/")
        
        # Organiza filmes por categoria
        categories = self.organize_movies_by_category(movie_list)
        
        total_movies = len(movie_list)
        generated_files = []
        
        print(f"\n📊 Encontradas {len(categories)} categorias:")
        for category in categories:
            print(f"   • {self.format_category_name(category)}: {len(categories[category])} filmes")
        
        # Gera um arquivo M3U para cada categoria
        for category_name, movies in categories.items():
            print(f"\n{'='*50}")
            filepath = self.generate_single_category_m3u(category_name, movies, output_dir)
            generated_files.append(filepath)
        
        print(f"\n{'='*50}")
        print("✅ Processamento concluído!")
        print(f"📁 Total de categorias processadas: {len(categories)}")
        print(f"🎬 Total de filmes processados: {total_movies}")
        print(f"📄 Arquivos gerados em: {output_dir}/")
        
        # Lista os arquivos gerados
        print("\n📄 Arquivos gerados:")
        for filepath in generated_files:
            filename = os.path.basename(filepath)
            print(f"   • {filename}")
    
    def process_movies_from_file(self, input_file, output_dir="playlists"):
        """Processa filmes de um arquivo de texto"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                movie_list = [line.strip() for line in f if line.strip()]
            
            self.process_movie_list(movie_list, output_dir)
        except FileNotFoundError:
            print(f"❌ Arquivo não encontrado: {input_file}")
        except Exception as e:
            print(f"❌ Erro ao ler arquivo: {e}")

# Versão alternativa sem API do TMDB
class SimpleM3UGenerator:
    def __init__(self):
        self.base_url = "http://xtyre.top"
    
    def extract_movie_info(self, file_path):
        """Extrai informações do filme do caminho do arquivo"""
        parts = file_path.strip().split('/')
        
        if len(parts) >= 2:
            category = parts[0]
            filename = parts[-1]
            movie_name = filename.replace('.mp4', '')
            full_url = f"{self.base_url}/FILMES/{file_path.strip()}"
            
            return {
                'category': category,
                'movie_name': movie_name,
                'full_url': full_url
            }
        return None
    
    def format_category_name(self, category):
        """Formata o nome da categoria para o arquivo"""
        category = category.replace('Filmes | ', '')
        category = re.sub(r'\s*\[.*?\]', '', category)
        category = re.sub(r'[<>:"/\\|?*]', '', category)
        
        words = category.split()
        formatted_words = []
        for word in words:
            if word.upper() in ['XXX', 'S.W.A.T.']:
                formatted_words.append(word.upper())
            else:
                formatted_words.append(word.capitalize())
        
        return ' '.join(formatted_words).strip()
    
    def generate_m3u_entry(self, movie_info):
        """Gera uma entrada M3U sem poster do TMDB"""
        category = self.format_category_name(movie_info['category'])
        
        entry = f'#EXTINF:-1 tvg-name="{movie_info["movie_name"]}" tvg-logo="" group-title="Filmes | {category}",{movie_info["movie_name"]}\n'
        entry += f'{movie_info["full_url"]}\n'
        
        return entry
    
    def organize_movies_by_category(self, movie_list):
        """Organiza os filmes por categoria"""
        categories = {}
        
        for movie_path in movie_list:
            movie_info = self.extract_movie_info(movie_path)
            if movie_info:
                category = movie_info['category']
                if category not in categories:
                    categories[category] = []
                categories[category].append(movie_info)
        
        return categories
    
    def generate_single_category_m3u(self, category_name, movies, output_dir="playlists_simples"):
        """Gera um arquivo M3U para uma categoria específica (sem TMDB)"""
        formatted_category = self.format_category_name(category_name)
        filename = f"{formatted_category}.m3u"
        filepath = os.path.join(output_dir, filename)
        
        m3u_content = "#EXTM3U\n"
        
        print(f"🎬 Gerando {filename} com {len(movies)} filmes...")
        
        for i, movie_info in enumerate(movies, 1):
            print(f"  [{i}/{len(movies)}] {movie_info['movie_name']}")
            
            # Gera entrada M3U
            m3u_entry = self.generate_m3u_entry(movie_info)
            m3u_content += m3u_entry
        
        # Cria diretório se não existir
        os.makedirs(output_dir, exist_ok=True)
        
        # Salva o arquivo
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        
        print(f"  ✅ {filename} salvo com sucesso!")
        return filepath
    
    def process_movie_list(self, movie_list, output_dir="playlists_simples"):
        """Processa a lista de filmes e gera arquivos M3U separados por categoria (sem TMDB)"""
        print("Iniciando processamento (versão simples)...")
        print(f"📁 Gerando arquivos M3U separados em: {output_dir}/")
        
        # Organiza filmes por categoria
        categories = self.organize_movies_by_category(movie_list)
        
        total_movies = len(movie_list)
        generated_files = []
        
        print(f"\n📊 Encontradas {len(categories)} categorias:")
        for category in categories:
            print(f"   • {self.format_category_name(category)}: {len(categories[category])} filmes")
        
        # Gera um arquivo M3U para cada categoria
        for category_name, movies in categories.items():
            print(f"\n{'='*50}")
            filepath = self.generate_single_category_m3u(category_name, movies, output_dir)
            generated_files.append(filepath)
        
        print(f"\n{'='*50}")
        print("✅ Processamento concluído!")
        print(f"📁 Total de categorias processadas: {len(categories)}")
        print(f"🎬 Total de filmes processados: {total_movies}")
        
        # Lista os arquivos gerados
        print("\n📄 Arquivos gerados:")
        for filepath in generated_files:
            filename = os.path.basename(filepath)
            print(f"   • {filename}")

# Exemplo de uso
def main():
    # Lê a lista de filmes do arquivo resultadoFILMES.txt
    input_file = "resultadoFILMES.txt"
    
    # Verifica se o arquivo existe
    if not os.path.exists(input_file):
        print(f"❌ Arquivo {input_file} não encontrado!")
        return
    
    # Lê os filmes do arquivo e REMOVE ASPAS E VÍRGULAS
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            movie_list = []
            for line in f:
                if line.strip():
                    # Remove aspas e vírgulas do início e final
                    clean_line = line.strip().strip('",')
                    movie_list.append(clean_line)
        
        print(f"✅ Carregados {len(movie_list)} filmes do arquivo {input_file}")
        print("📝 Primeiras 3 linhas (após limpeza):")
        for i, movie in enumerate(movie_list[:3]):
            print(f"   {i+1}: {movie}")
        
    except Exception as e:
        print(f"❌ Erro ao ler arquivo {input_file}: {e}")
        return
    
    # Opção 1: Com API do TMDB (com posters)
    print("\n=== GERADOR COM TMDB (ARQUIVOS SEPARADOS COM POSTERS) ===")
    generator = M3UGenerator()
    generator.process_movie_list(movie_list, "playlists_com_posters")
    
    # Opção 2: Sem API do TMDB (arquivos separados sem posters)
    print("\n=== GERADOR SIMPLES (ARQUIVOS SEPARADOS SEM POSTERS) ===")
    simple_generator = SimpleM3UGenerator()
    simple_generator.process_movie_list(movie_list, "playlists_sem_posters")

if __name__ == "__main__":
    main()
