import unicodedata

def normalizar(texto):
    """Remove acentos e coloca em minúsculo para comparação"""
    return unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf-8').lower()

# Definição centralizada das pastas e suas variações
# Esta é a fonte única da verdade para todas as categorias no projeto.
PASTAS = {
    "Acao": ["acao", "ação", "action"],
    "Comedia": ["comedia", "comédia", "comedy"],
    "Drama": ["drama"],
    "Terror": ["terror", "horror"],
    "Ficcao": ["ficcao", "ficção", "sci-fi", "science fiction"],
    "Romance": ["romance", "romantic"],
    "Aventura": ["aventura", "adventure"],
    "Suspense": ["suspense", "thriller"],
    "Animacao": ["animacao", "animação", "animation"],
    "Documentarios": ["documentario", "documentário", "documentary"],
    "Guerra": ["guerra", "war"],
    "Faroeste": ["faroeste", "western"],
    "Fantasia": ["fantasia", "fantasy"],
    "Crime": ["crime"],
    "Familia": ["familia", "família", "family"],
    "Religiosos": ["religiosos", "religious"],
    "Nacionais": ["nacionais", "national"],
    "Legendados": ["legendados", "subtitled"],
    "4K": ["4k"],
    "Diversos": ["diversos", "misc"]
}

# Cria o mapeamento reverso para normalização
FOLDER_MAPPING = {}
for pasta_padrao, variantes in PASTAS.items():
    for variante in variantes:
        FOLDER_MAPPING[variante] = pasta_padrao
        # Adiciona também a versão normalizada do nome padrão
        FOLDER_MAPPING[normalizar(pasta_padrao)] = pasta_padrao

# Categorias válidas são todas as variantes de nomes
CATEGORIAS_VALIDAS = set()
for variantes in PASTAS.values():
    CATEGORIAS_VALIDAS.update(variantes) 