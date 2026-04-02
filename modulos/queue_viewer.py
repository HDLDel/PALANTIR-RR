import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import threading
import os

class QueueViewer:
    def __init__(self, root, download_queue, is_downloading):
        self.root = root
        self.download_queue = download_queue
        self.is_downloading = is_downloading

    def remover_item(self, posicao):
        """Remove um item específico da fila"""
        try:
            # Ajusta posição (interface começa em 1, lista em 0)
            index = posicao - 1
            if 0 <= index < len(self.download_queue):
                self.download_queue.pop(index)
                return True
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao remover item: {str(e)}")
        return False

    def show_queue(self):
        """Mostra a fila de downloads atual"""
        try:
            # Cria janela de visualização
            queue_window = ctk.CTkToplevel()
            queue_window.title("Fila de Downloads - Palantir")
            queue_window.geometry("800x500")
            queue_window.resizable(True, True)
            
            # Configura a janela como modal de forma mais segura
            queue_window.transient(self.root)
            queue_window.focus_set()
            
            # Tenta fazer a janela modal de forma segura
            try:
                queue_window.grab_set()
            except tk.TclError:
                # Se falhar, apenas foca na janela
                queue_window.focus_set()
            
            # Frame principal
            main_frame = ctk.CTkFrame(queue_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Título
            title_label = ctk.CTkLabel(main_frame, text="Fila de Downloads", 
                                     font=ctk.CTkFont(size=16, weight="bold"))
            title_label.pack(pady=(0, 20))
            
            # Frame para informações gerais
            info_frame = ctk.CTkFrame(main_frame)
            info_frame.pack(fill=tk.X, padx=10, pady=10)
            
            # Informações da fila
            total_items = len(self.download_queue)
            status = "Processando" if self.is_downloading else "Aguardando"
            
            info_text = f"Total de itens na fila: {total_items}\\nStatus: {status}"
            info_label = ctk.CTkLabel(info_frame, text=info_text, font=ctk.CTkFont(size=12))
            info_label.pack(pady=10)
            
            # Frame para a lista de downloads
            list_frame = ctk.CTkFrame(main_frame)
            list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Título da lista
            ctk.CTkLabel(list_frame, text="Downloads na Fila:", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor=tk.W, padx=10, pady=(10, 5))
            
            # Treeview para mostrar a fila
            queue_tree = ttk.Treeview(list_frame, columns=("posicao", "nome", "url", "pasta", "remover"), show="headings", height=15)
            queue_tree.heading("posicao", text="Posição")
            queue_tree.heading("nome", text="Nome do Vídeo")
            queue_tree.heading("url", text="URL")
            queue_tree.heading("pasta", text="Pasta de Destino")
            queue_tree.heading("remover", text="")  # Coluna para botão X
            
            queue_tree.column("posicao", width=80)
            queue_tree.column("nome", width=300)
            queue_tree.column("url", width=250)
            queue_tree.column("pasta", width=150)
            queue_tree.column("remover", width=50, anchor="center")  # Coluna estreita para o X
            
            # Scrollbar para o treeview
            queue_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=queue_tree.yview)
            queue_tree.configure(yscrollcommand=queue_scrollbar.set)
            
            queue_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
            queue_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
            
            # Adiciona os itens da fila ao treeview
            for i, (nome, url, pasta) in enumerate(self.download_queue, 1):
                # Trunca a URL se for muito longa
                url_display = url[:50] + "..." if len(url) > 50 else url
                # Trunca o nome se for muito longo
                nome_display = nome[:40] + "..." if len(nome) > 40 else nome
                # Trunca o caminho se for muito longo
                pasta_display = os.path.basename(pasta) if len(pasta) > 20 else pasta
                
                queue_tree.insert("", tk.END, values=(i, nome_display, url_display, pasta_display))
            
            # Frame para botões
            button_frame = ctk.CTkFrame(main_frame)
            button_frame.pack(fill=tk.X, padx=10, pady=10)
            
            def atualizar_fila():
                """Atualiza a visualização da fila"""
                # Limpa o treeview
                for item in queue_tree.get_children():
                    queue_tree.delete(item)
                
                # Atualiza informações
                total_items = len(self.download_queue)
                status = "Processando" if self.is_downloading else "Aguardando"
                info_text = f"Total de itens na fila: {total_items}\\nStatus: {status}"
                info_label.configure(text=info_text)
                
                # Adiciona os itens atualizados
                for i, (nome, url, pasta) in enumerate(self.download_queue, 1):
                    url_display = url[:50] + "..." if len(url) > 50 else url
                    nome_display = nome[:40] + "..." if len(nome) > 40 else nome
                    pasta_display = os.path.basename(pasta) if len(pasta) > 20 else pasta
                    
                    queue_tree.insert("", tk.END, values=(i, nome_display, url_display, pasta_display, "❌"))
            
            # Botão para atualizar
            atualizar_button = ctk.CTkButton(
                button_frame, 
                text="Atualizar", 
                command=atualizar_fila,
                fg_color="#3498db",
                hover_color="#2980b9"
            )
            atualizar_button.pack(side=tk.LEFT, padx=5)
            
            # Botão para fechar
            fechar_button = ctk.CTkButton(
                button_frame, 
                text="Fechar", 
                command=queue_window.destroy
            )
            fechar_button.pack(side=tk.RIGHT, padx=5)
            
            # Função para lidar com clique no botão X
            def on_remove_click(event):
                item = queue_tree.identify_row(event.y)
                if item:
                    valores = queue_tree.item(item)['values']
                    if valores:
                        posicao = valores[0]  # Primeira coluna é a posição
                        if self.remover_item(posicao):
                            atualizar_fila()

            # Bind click event na coluna do X
            queue_tree.bind('<ButtonRelease-1>', lambda e: on_remove_click(e) if queue_tree.identify_column(e.x) == '#5' else None)

            # Auto-atualização a cada 2 segundos
            def auto_atualizar():
                if queue_window.winfo_exists():
                    atualizar_fila()
                    queue_window.after(2000, auto_atualizar)
            
            # Inicia auto-atualização
            queue_window.after(2000, auto_atualizar)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir visualizador de fila: {str(e)}")