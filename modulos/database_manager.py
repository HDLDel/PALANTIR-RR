import sqlite3
import os
from typing import Optional, Tuple, List, Dict, Any
from tkinter import messagebox
import threading

class DatabaseManager:
    def __init__(self, db_path: str = 'videos.db'):
        """Inicializa o gerenciador de banco de dados"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.db_cache = {}
        self.db_cache_loaded = False
        self.current_data = []  # Dados atualmente carregados
        self.lock = threading.Lock()  # Lock para operações thread-safe
        
    def init_database(self) -> Tuple[bool, str]:
        """Inicializa o banco de dados e cria tabelas se necessário"""
        try:
            with self.lock:
                if self.conn is not None:
                    return True, "Banco já inicializado"

                # Cria diretório se não existir
                db_dir = os.path.dirname(os.path.abspath(self.db_path))
                if not os.path.exists(db_dir):
                    os.makedirs(db_dir)

                self.conn = sqlite3.connect(self.db_path)
                self.cursor = self.conn.cursor()
                
                # Otimizações para carregamento rápido
                self.cursor.execute("PRAGMA synchronous = OFF")
                self.cursor.execute("PRAGMA journal_mode = MEMORY")
                self.cursor.execute("PRAGMA cache_size = -5000000")  # 5GB cache
                self.cursor.execute("PRAGMA temp_store = MEMORY")
                
                # Cria tabela se não existir
                self.cursor.execute("""
                    CREATE TABLE IF NOT EXISTS videos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        url TEXT NOT NULL UNIQUE,
                        type TEXT NOT NULL,
                        season TEXT NOT NULL,
                        username TEXT,
                        category TEXT,
                        downloaded INTEGER DEFAULT 0
                    )
                """)
                self.conn.commit()
                
                return True, "Banco de dados inicializado com sucesso"
                
        except Exception as e:
            return False, f"Erro ao inicializar banco: {str(e)}"

    def conectar_banco(self) -> Tuple[bool, str]:
        """Estabelece conexão com o banco de dados"""
        try:
            with self.lock:
                if self.conn is not None:
                    return True, "Conexão já estabelecida"

                db_path = os.path.abspath(self.db_path)
                if not os.access(os.path.dirname(db_path), os.W_OK):
                    return False, f"Sem permissão de escrita no diretório: {db_path}"

                self.conn = sqlite3.connect(self.db_path)
                self.cursor = self.conn.cursor()
                
                # Otimizações para carregamento rápido
                self.cursor.execute("PRAGMA synchronous = OFF")
                self.cursor.execute("PRAGMA journal_mode = MEMORY")
                self.cursor.execute("PRAGMA cache_size = -5000000")  # 5GB cache
                self.cursor.execute("PRAGMA temp_store = MEMORY")
                
                return True, "Conexão estabelecida com sucesso"
                
        except Exception as e:
            return False, f"Erro ao conectar: {str(e)}"

    def load_database(self) -> Tuple[bool, str, List[tuple]]:
        """Carrega todos os registros do banco"""
        try:
            with self.lock:
                if not self.conn or not self.cursor:
                    success, msg = self.conectar_banco()
                    if not success:
                        return False, msg, []

                self.cursor.execute("SELECT * FROM videos ORDER BY name")
                self.current_data = self.cursor.fetchall()
                self.db_cache_loaded = True
                
                return True, f"Carregados {len(self.current_data)} registros", self.current_data

        except Exception as e:
            return False, f"Erro ao carregar banco: {str(e)}", []

    def inserir_no_banco(self, name: str, url: str, content_type: str, 
                        season: str = "-", username: Optional[str] = None, 
                        category: Optional[str] = None) -> Tuple[bool, str]:
        """Insere um novo registro no banco"""
        try:
            with self.lock:
                if not self.conn:
                    success, msg = self.conectar_banco()
                    if not success:
                        return False, msg

                self.cursor.execute("""
                    INSERT OR IGNORE INTO videos 
                    (name, url, type, season, username, category)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, url, content_type, season, username, category))
                
                self.conn.commit()
                
                # Atualiza cache
                if self.db_cache_loaded:
                    self.cursor.execute('SELECT * FROM videos WHERE name = ?', (name,))
                    record = self.cursor.fetchone()
                    if record:
                        self.db_cache[name] = record
                        
                return True, "Registro inserido com sucesso"
                
        except Exception as e:
            return False, f"Erro ao inserir: {str(e)}"

    def atualizar_no_banco(self, name: str, url: str, content_type: str, 
                          season: str = "-", username: Optional[str] = None, 
                          category: Optional[str] = None) -> Tuple[bool, str]:
        """Atualiza um registro existente no banco"""
        try:
            with self.lock:
                if not self.conn:
                    success, msg = self.conectar_banco()
                    if not success:
                        return False, msg

                self.cursor.execute("""
                    UPDATE videos 
                    SET url = ?, type = ?, season = ?, username = ?, category = ?
                    WHERE name = ?
                """, (url, content_type, season, username, category, name))
                
                self.conn.commit()
                
                # Atualiza cache
                if self.db_cache_loaded and name in self.db_cache:
                    registro_atual = self.db_cache[name]
                    novo_registro = (registro_atual[0], name, url, content_type, season, username, category, registro_atual[7])
                    self.db_cache[name] = novo_registro
                    
                return True, "Registro atualizado com sucesso"
                
        except Exception as e:
            return False, f"Erro ao atualizar: {str(e)}"

    def deletar_do_banco(self, name: str) -> Tuple[bool, str]:
        """Remove um registro do banco"""
        try:
            with self.lock:
                if not self.conn:
                    success, msg = self.conectar_banco()
                    if not success:
                        return False, msg

                self.cursor.execute('DELETE FROM videos WHERE name = ?', (name,))
                self.conn.commit()
                
                # Remove do cache
                if name in self.db_cache:
                    del self.db_cache[name]
                    
                return True, "Registro removido com sucesso"
                
        except Exception as e:
            return False, f"Erro ao remover: {str(e)}"

    def atualizar_cache(self, name: str, dados: tuple):
        """Atualiza o cache em memória com novos dados"""
        with self.lock:
            if self.db_cache_loaded:
                self.db_cache[name] = dados

    def remover_do_cache(self, name: str):
        """Remove um item do cache em memória"""
        with self.lock:
            if self.db_cache_loaded and name in self.db_cache:
                del self.db_cache[name]

    def search(self, term: str, search_in_categories: bool = False) -> List[tuple]:
        """Busca registros no banco"""
        try:
            with self.lock:
                if not self.conn:
                    self.conectar_banco()
                    
                if search_in_categories:
                    self.cursor.execute("""
                        SELECT * FROM videos 
                        WHERE name LIKE ? OR category LIKE ? 
                        ORDER BY name
                    """, (f"%{term}%", f"%{term}%"))
                else:
                    self.cursor.execute(
                        "SELECT * FROM videos WHERE name LIKE ? ORDER BY name",
                        (f"%{term}%",)
                    )
                    
                return self.cursor.fetchall()
                
        except Exception as e:
            print(f"Erro na busca: {str(e)}")
            return []

    def update_url(self, old_url: str, new_url: str) -> Tuple[bool, str, int]:
        """Atualiza URLs no banco"""
        try:
            with self.lock:
                if not self.conn:
                    success, msg = self.conectar_banco()
                    if not success:
                        return False, msg, 0

                self.cursor.execute("""
                    UPDATE videos 
                    SET url = REPLACE(url, ?, ?)
                    WHERE url LIKE ?
                """, (old_url, new_url, f"%{old_url}%"))
                
                rows_affected = self.cursor.rowcount
                self.conn.commit()
                
                return True, "URLs atualizadas com sucesso", rows_affected
                
        except Exception as e:
            return False, f"Erro ao atualizar URLs: {str(e)}", 0

    def clear_cache(self):
        """Limpa o cache em memória"""
        with self.lock:
            self.db_cache.clear()
            self.db_cache_loaded = False
            self.current_data = []

    def close(self):
        """Fecha a conexão com o banco"""
        try:
            with self.lock:
                if self.conn:
                    self.conn.close()
                    self.conn = None
                    self.cursor = None
                    self.clear_cache()
        except Exception as e:
            print(f"Erro ao fechar conexão: {str(e)}")

    def get_connection_status(self) -> bool:
        """Retorna o status da conexão com o banco"""
        with self.lock:
            return self.conn is not None and self.cursor is not None

    def get_total_records(self) -> int:
        """Retorna o total de registros no banco"""
        try:
            with self.lock:
                if not self.conn:
                    success, msg = self.conectar_banco()
                    if not success:
                        return 0

                self.cursor.execute("SELECT COUNT(*) FROM videos")
                return self.cursor.fetchone()[0]
                
        except Exception as e:
            print(f"Erro ao contar registros: {str(e)}")
            return 0

    def get_categories(self) -> List[str]:
        """Retorna lista de categorias únicas"""
        try:
            with self.lock:
                if not self.conn:
                    success, msg = self.conectar_banco()
                    if not success:
                        return []

                self.cursor.execute("SELECT DISTINCT category FROM videos WHERE category IS NOT NULL AND category != '' ORDER BY category")
                return [row[0] for row in self.cursor.fetchall()]
                
        except Exception as e:
            print(f"Erro ao obter categorias: {str(e)}")
            return []

    def get_types(self) -> List[str]:
        """Retorna lista de tipos únicos"""
        try:
            with self.lock:
                if not self.conn:
                    success, msg = self.conectar_banco()
                    if not success:
                        return []

                self.cursor.execute("SELECT DISTINCT type FROM videos ORDER BY type")
                return [row[0] for row in self.cursor.fetchall()]
                
        except Exception as e:
            print(f"Erro ao obter tipos: {str(e)}")
            return []

    def get_sources(self) -> List[str]:
        """Retorna lista de fontes (usernames) únicas"""
        try:
            with self.lock:
                if not self.conn:
                    success, msg = self.conectar_banco()
                    if not success:
                        return []

                self.cursor.execute("SELECT DISTINCT username FROM videos WHERE username IS NOT NULL AND username != '' ORDER BY username")
                return [row[0] for row in self.cursor.fetchall()]
                
        except Exception as e:
            print(f"Erro ao obter fontes: {str(e)}")
            return []

    def bulk_insert_m3u_data(self, batch_data: List[tuple]) -> Tuple[bool, str, int]:
        """Insere dados M3U em lote no banco de dados"""
        try:
            with self.lock:
                if not self.conn:
                    success, msg = self.conectar_banco()
                    if not success:
                        return False, msg, 0

                # Query de inserção
                insert_query = '''
                    INSERT OR IGNORE INTO videos (name, url, type, season, username, category)
                    VALUES (?, ?, ?, ?, ?, ?)
                '''
                
                # Desabilita temporariamente as restrições para melhor performance
                self.cursor.execute("PRAGMA foreign_keys=OFF")
                self.cursor.execute("PRAGMA synchronous=OFF")
                self.cursor.execute("PRAGMA journal_mode=MEMORY")
                
                # Insere os dados em lote
                self.cursor.executemany(insert_query, batch_data)
                rows_inserted = self.cursor.rowcount
                
                # Reativa as restrições
                self.cursor.execute("PRAGMA foreign_keys=ON")
                self.cursor.execute("PRAGMA synchronous=NORMAL")
                self.cursor.execute("PRAGMA journal_mode=DELETE")
                
                self.conn.commit()
                
                return True, f"{rows_inserted} registros inseridos com sucesso", rows_inserted
                
        except Exception as e:
            # Reativa as restrições em caso de erro
            try:
                self.cursor.execute("PRAGMA foreign_keys=ON")
                self.cursor.execute("PRAGMA synchronous=NORMAL")
                self.cursor.execute("PRAGMA journal_mode=DELETE")
            except:
                pass
            return False, f"Erro ao inserir dados em lote: {str(e)}", 0

    def edit_urls_ui(self, parent=None):
        """Interface para editar URLs no banco de dados"""
        try:
            if not self.get_connection_status():
                messagebox.showerror("Erro", "Banco de dados não está conectado. Tente carregar o banco primeiro.")
                return

            # Importa módulos necessários para a UI
            import customtkinter as ctk
            from tkinter import messagebox

            # Cria janela de edição
            edit_window = ctk.CTkToplevel(parent) if parent else ctk.CTkToplevel()
            edit_window.title("Editor de URLs - Banco de Dados")
            edit_window.geometry("600x400")
            edit_window.resizable(True, True)
            
            # Frame para os widgets
            frame = ctk.CTkFrame(edit_window)
            frame.pack(padx=10, pady=10, fill="both", expand=True)
            
            # Labels e entradas
            ctk.CTkLabel(frame, text="URL Antiga:").pack(pady=5)
            old_url = ctk.CTkEntry(frame, width=400)
            old_url.pack(pady=5)
            
            ctk.CTkLabel(frame, text="Nova URL:").pack(pady=5)
            new_url = ctk.CTkEntry(frame, width=400)
            new_url.pack(pady=5)
            
            def update_urls():
                old = old_url.get().strip()
                new = new_url.get().strip()
                
                if not old or not new:
                    messagebox.showerror("Erro", "Por favor preencha ambas as URLs")
                    return
                    
                success, msg, count = self.update_url(old, new)
                
                if success:
                    messagebox.showinfo("Sucesso", f"{count} URLs atualizadas com sucesso")
                    edit_window.destroy()
                else:
                    messagebox.showerror("Erro", msg)
            
            # Botões
            btn_frame = ctk.CTkFrame(frame)
            btn_frame.pack(pady=20)
            
            ctk.CTkButton(
                btn_frame, 
                text="Atualizar", 
                command=update_urls
            ).pack(side="left", padx=5)
            
            ctk.CTkButton(
                btn_frame,
                text="Cancelar",
                command=edit_window.destroy
            ).pack(side="left", padx=5)
            
            # Tornar janela modal
            edit_window.transient(parent) if parent else None
            edit_window.grab_set()
            edit_window.focus_set()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir editor: {str(e)}")

    def __del__(self):
        """Destrutor - garante que a conexão seja fechada"""
        self.close()


# Teste básico da classe
if __name__ == "__main__":
    db = DatabaseManager()
    
    # Teste de inicialização
    success, msg = db.init_database()
    print(f"Inicialização: {success} - {msg}")
    
    # Teste de conexão
    success, msg = db.conectar_banco()
    print(f"Conexão: {success} - {msg}")
    
    # Teste de inserção
    success, msg = db.inserir_no_banco(
        "Teste Video", 
        "https://example.com/video.mp4", 
        "Filme", 
        "-", 
        "testuser", 
        "Teste"
    )
    print(f"Inserção: {success} - {msg}")
    
    # Teste de busca
    resultados = db.search("Teste")
    print(f"Resultados da busca: {len(resultados)} encontrados")
    
    # Teste de contagem
    total = db.get_total_records()
    print(f"Total de registros: {total}")
    
    # Fechar conexão
    db.close()
    print("Conexão fechada")
