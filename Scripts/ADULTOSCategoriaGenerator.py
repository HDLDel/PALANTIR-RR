import requests
import re
import json
from urllib.parse import unquote
import time
import os

class M3UGenerator:
    def __init__(self):
        self.tmdb_api_key = "<PLACEHOLDER>"
        self.base_url = "http://xtyre.top"
        self.adult_poster_url = "https://www.acstatic.co/vod/capinha/adult.jpg"
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
        """Busca informações do filme no TMDB (não será usado, mas mantido por compatibilidade)"""
        # Não usaremos TMDB, sempre retornamos o banner adulto
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
        # Sempre usa o banner adulto
        poster_url = self.adult_poster_url
        
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
        
        for i, movie_info in enumerate(movies, 1):
            print(f"  [{i}/{len(movies)}] Processando: {movie_info['movie_name']}")
            
            # Sempre usa o banner adulto, não busca no TMDB
            tmdb_data = None  # Não usaremos dados do TMDB
            
            # Gera entrada M3U
            m3u_entry = self.generate_m3u_entry(movie_info, tmdb_data)
            m3u_content += m3u_entry
            
            # Delay reduzido pois não estamos usando API externa
            time.sleep(0.1)
        
        # Cria diretório se não existir
        os.makedirs(output_dir, exist_ok=True)
        
        # Salva o arquivo
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        
        print(f"  ✅ {filename} salvo com sucesso! (usando banner adulto para todos)")
        return filepath
    
    def process_movie_list(self, movie_list, output_dir="playlists"):
        """Processa a lista de filmes e gera arquivos M3U separados por categoria"""
        print("Iniciando processamento...")
        print(f"📁 Gerando arquivos M3U separados em: {output_dir}/")
        print("🎭 Usando banner adulto: https://www.acstatic.co/vod/capinha/adult.jpg")
        
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

# Versão alternativa sem API do TMDB - REMOVIDA conforme solicitado
# Mantenho apenas a classe principal com modificações

# Exemplo de uso
def main():
    # Lê a lista de filmes do arquivo resultadoADULTOS.txt
    input_file = "resultadoADULTOS.txt"
    
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
    
    # Usa apenas o gerador com banner adulto fixo
    print("\n=== GERADOR M3U COM BANNER ADULTO FIXO ===")
    print("🎭 Usando banner: https://www.acstatic.co/vod/capinha/adult.jpg")
    
    generator = M3UGenerator()
    generator.process_movie_list(movie_list, "playlists_adultos")

if __name__ == "__main__":
    main()
