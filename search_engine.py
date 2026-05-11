"""
Módulo para gerenciamento de busca e indexação do Palantir.
Integrado com DatabaseManager para sincronização automática.
"""
from unidecode import unidecode
from typing import List, Dict, Any, Optional, Tuple, Union
import threading
import time

class SearchEngine:
    def __init__(self, db_manager=None):
        """
        Inicializa o motor de busca
        
        Args:
            db_manager: Instância opcional de DatabaseManager para sincronização automática
        """
        self.cache = {}
        self.busca_nome = {}
        self.busca_url = {}
        self.busca_categoria = {}
        self.busca_tipo = {}
        self.busca_servidor = {}
        self.busca_username = {}
        self.busca_season = {}
        
        # Integração com DatabaseManager
        self.db_manager = db_manager
        self.last_sync_time = 0
        self.sync_interval = 300  # 5 minutos entre sincronizações
        self.lock = threading.Lock()
        
        # Estatísticas
        self.stats = {
            'total_indexed': 0,
            'last_index_time': 0,
            'search_count': 0,
            'avg_search_time': 0
        }

    def normalize_text(self, text: str) -> str:
        """Remove acentos e caracteres especiais do texto e normaliza pontuação"""
        if not isinstance(text, str):
            return ""
            
        try:
            # Remove acentos
            normalized = unidecode(str(text).lower())
            
            # Remove caracteres especiais
            chars_to_remove = [":", ",", "'", '"', "(", ")", "[", "]", "{", "}"]
            for char in chars_to_remove:
                normalized = normalized.replace(char, "")
                
            # Normaliza pontuação
            normalized = normalized.replace(".", " ")
            normalized = normalized.replace("-", " ")
            normalized = normalized.replace("_", " ")
            normalized = normalized.replace("/", " ")
            
            # Remove espaços extras
            return " ".join(normalized.split())
            
        except Exception as e:
            print(f"Erro ao normalizar texto: {str(e)}")
            return str(text).lower()

    def indexar_item(self, item: tuple, fonte: str = "db") -> None:
        """
        Indexa um item nos dicionários de busca
        
        Args:
            item: Tupla contendo os dados do item (id, nome, url, tipo, season, username, categoria)
            fonte: Origem dos dados ("db" ou "m3u")
        """
        try:
            # Extrai os campos do item
            name = str(item[1])  # Nome
            url = str(item[2])   # URL 
            tipo = str(item[3])  # Tipo
            season = str(item[4]) # Temporada
            username = str(item[5]) if len(item) > 5 else ""  # Username
            categoria = str(item[6]) if len(item) > 6 else "" # Categoria
            
            # Normaliza os campos para busca
            norm_name = self.normalize_text(name)
            norm_url = self.normalize_text(url)
            norm_categoria = self.normalize_text(categoria)
            norm_tipo = self.normalize_text(tipo)
            norm_username = self.normalize_text(username)
            norm_season = self.normalize_text(season)
            
            # Extrai e normaliza servidor da URL
            servidor = ""
            if "://" in url:
                servidor = self.normalize_text(url.split("://")[1].split("/")[0])
            
            # Indexa os campos nos respectivos dicionários
            self._add_to_index(self.busca_nome, norm_name, item, fonte)
            self._add_to_index(self.busca_url, norm_url, item, fonte)
            self._add_to_index(self.busca_categoria, norm_categoria, item, fonte)
            self._add_to_index(self.busca_tipo, norm_tipo, item, fonte)
            self._add_to_index(self.busca_servidor, servidor, item, fonte)
            self._add_to_index(self.busca_username, norm_username, item, fonte)
            self._add_to_index(self.busca_season, norm_season, item, fonte)
            
            # Atualiza estatísticas
            with self.lock:
                self.stats['total_indexed'] += 1
                self.stats['last_index_time'] = time.time()
            
        except Exception as e:
            print(f"Erro ao indexar item {item}: {str(e)}")

    def _add_to_index(self, index: Dict[str, List[tuple]], key: str, item: tuple, fonte: str) -> None:
        """
        Adiciona um item a um índice específico
        
        Args:
            index: Dicionário que serve como índice
            key: Chave para indexação
            item: Item a ser indexado
            fonte: Origem dos dados
        """
        if not key:
            return
            
        if key not in index:
            index[key] = []
        
        # Adiciona o item apenas se não existir
        if item not in index[key]:
            index[key].append((item, fonte))

    def buscar(self, termo: str, campo: str = "nome", partial_match: bool = True) -> List[Tuple[tuple, str]]:
        """
        Busca itens pelo termo especificado
        
        Args:
            termo: Termo de busca
            campo: Campo onde buscar ("nome", "url", "categoria", "tipo", "servidor", "username", "season")
            partial_match: Se True, faz busca parcial. Se False, requer match exato
            
        Returns:
            Lista de tuplas (item, fonte)
        """
        start_time = time.time()
        
        # Sincroniza com o banco se necessário
        self._sync_with_database()
        
        # Normaliza o termo de busca
        termo_norm = self.normalize_text(termo)
        if not termo_norm:
            return []
            
        # Seleciona o índice apropriado
        indices = {
            "nome": self.busca_nome,
            "url": self.busca_url,
            "categoria": self.busca_categoria,
            "tipo": self.busca_tipo,
            "servidor": self.busca_servidor,
            "username": self.busca_username,
            "season": self.busca_season
        }
        
        indice = indices.get(campo.lower(), self.busca_nome)
        resultados = []
        
        # Realiza a busca
        for key in indice:
            if (partial_match and termo_norm in key) or (not partial_match and termo_norm == key):
                resultados.extend(indice[key])
        
        # Atualiza estatísticas
        search_time = time.time() - start_time
        with self.lock:
            self.stats['search_count'] += 1
            total_searches = self.stats['search_count']
            current_avg = self.stats['avg_search_time']
            self.stats['avg_search_time'] = (current_avg * (total_searches - 1) + search_time) / total_searches
                
        return resultados

    def buscar_avancada(self, termos: Dict[str, str], operador: str = "AND") -> List[Tuple[tuple, str]]:
        """
        Busca avançada com múltiplos critérios
        
        Args:
            termos: Dicionário com campos e termos de busca
            operador: Operador lógico ("AND" ou "OR")
            
        Returns:
            Lista de tuplas (item, fonte)
        """
        self._sync_with_database()
        
        resultados_parciais = []
        
        for campo, termo in termos.items():
            resultados_campo = self.buscar(termo, campo)
            resultados_parciais.append(set(resultados_campo))
        
        if not resultados_parciais:
            return []
        
        if operador.upper() == "AND":
            # Interseção de todos os conjuntos
            resultados_finais = set.intersection(*resultados_parciais)
        else:
            # União de todos os conjuntos
            resultados_finais = set.union(*resultados_parciais)
        
        return list(resultados_finais)

    def limpar_indices(self) -> None:
        """Limpa todos os índices de busca"""
        self.busca_nome.clear()
        self.busca_url.clear()
        self.busca_categoria.clear()
        self.busca_tipo.clear()
        self.busca_servidor.clear()
        self.busca_username.clear()
        self.busca_season.clear()
        self.cache.clear()
        
    def reindexar_dados(self, dados_m3u: List[tuple] = None, dados_db: List[tuple] = None) -> None:
        """
        Reindexar todos os dados tanto do arquivo M3U quanto do banco de dados.
        
        Args:
            dados_m3u: Lista de tuplas de dados do arquivo M3U (opcional)
            dados_db: Lista de tuplas de dados do banco de dados (opcional)
        """
        # Limpa todos os índices existentes
        self.limpar_indices()
        
        # Indexa dados do M3U se fornecidos
        if dados_m3u:
            for item in dados_m3u:
                self.indexar_item(item, "m3u")
                
        # Indexa dados do banco se fornecidos
        if dados_db:
            for item in dados_db:
                self.indexar_item(item, "db")

    def _sync_with_database(self) -> None:
        """Sincroniza os índices com o banco de dados se necessário"""
        if not self.db_manager:
            return
            
        current_time = time.time()
        if current_time - self.last_sync_time < self.sync_interval:
            return
            
        try:
            with self.lock:
                # Carrega dados do banco
                success, msg, dados_db = self.db_manager.load_database()
                if success:
                    # Reindexa apenas dados do banco
                    self.reindexar_dados(dados_db=dados_db)
                    self.last_sync_time = current_time
                    print(f"SearchEngine sincronizado com banco de dados. {len(dados_db)} registros indexados.")
                else:
                    print(f"Erro ao sincronizar com banco: {msg}")
                    
        except Exception as e:
            print(f"Erro durante sincronização: {str(e)}")

    def indexar_lote(self, items: List[tuple], fonte: str = "db") -> None:
        """
        Indexa múltiplos itens de uma vez (mais eficiente)
        
        Args:
            items: Lista de tuplas contendo os dados dos itens
            fonte: Origem dos dados ("db" ou "m3u")
        """
        for item in items:
            self.indexar_item(item, fonte)

    def get_estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas de uso do SearchEngine"""
        with self.lock:
            return self.stats.copy()

    def set_db_manager(self, db_manager) -> None:
        """Define o DatabaseManager para sincronização"""
        with self.lock:
            self.db_manager = db_manager

    def get_total_indexados(self) -> int:
        """Retorna o total de itens indexados"""
        with self.lock:
            return self.stats['total_indexed']

    def buscar_fuzzy(self, termo: str, campo: str = "nome", limite: int = 10) -> List[Tuple[tuple, str]]:
        """
        Busca fuzzy (aproximada) usando algoritmo simples de similaridade
        
        Args:
            termo: Termo de busca
            campo: Campo onde buscar
            limite: Número máximo de resultados
            
        Returns:
            Lista de tuplas (item, fonte) ordenadas por similaridade
        """
        self._sync_with_database()
        
        termo_norm = self.normalize_text(termo)
        if not termo_norm:
            return []
            
        indices = {
            "nome": self.busca_nome,
            "url": self.busca_url,
            "categoria": self.busca_categoria,
            "tipo": self.busca_tipo,
            "servidor": self.busca_servidor,
            "username": self.busca_username,
            "season": self.busca_season
        }
        
        indice = indices.get(campo.lower(), self.busca_nome)
        resultados_com_peso = []
        
        # Calcula similaridade para cada chave no índice
        for key in indice:
            similaridade = self._calcular_similaridade(termo_norm, key)
            if similaridade > 0.3:  # Threshold mínimo de similaridade
                for item in indice[key]:
                    resultados_com_peso.append((item, similaridade))
        
        # Ordena por similaridade (decrescente)
        resultados_com_peso.sort(key=lambda x: x[1], reverse=True)
        
        # Retorna apenas os itens (sem os pesos)
        return [item for item, peso in resultados_com_peso[:limite]]

    def _calcular_similaridade(self, texto1: str, texto2: str) -> float:
        """
        Calcula similaridade simples entre dois textos (0.0 a 1.0)
        Usa algoritmo básico de sobreposição de palavras
        """
        if not texto1 or not texto2:
            return 0.0
            
        palavras1 = set(texto1.split())
        palavras2 = set(texto2.split())
        
        if not palavras1 or not palavras2:
            return 0.0
            
        intersecao = palavras1.intersection(palavras2)
        uniao = palavras1.union(palavras2)
        
        return len(intersecao) / len(uniao) if uniao else 0.0
