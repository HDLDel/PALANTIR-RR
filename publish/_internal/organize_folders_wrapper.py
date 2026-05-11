#!/usr/bin/env python3
"""
Wrapper para as funções organize_folders e limpar_pastas
Permite executar essas funções de forma independente para evitar congelamento
"""

import os
import sys
import subprocess
import threading
from tkinter import messagebox

def organize_folders_wrapper(download_path, root):
    """
    Wrapper para organizar pastas com opção de execução interna ou externa
    
    Args:
        download_path: Caminho do diretório para organizar
        root: Tkinter root para mostrar diálogos
    """
    try:
        if not os.path.exists(download_path):
            messagebox.showerror("Erro", "Pasta de download inválida.")
            return

        # Pergunta se quer executar internamente ou externamente
        resposta = messagebox.askyesnocancel(
            "Escolha o modo de execução",
            "Como deseja executar a organização?\n\n"
            "Sim = Executar internamente (pode congelar)\n"
            "Não = Executar externamente (recomendado)\n"
            "Cancelar = Cancelar operação"
        )
        
        if resposta is None:  # Cancelar
            return
        elif resposta:  # Executar internamente
            organize_folders_internal(download_path, root)
        else:  # Executar externamente
            organize_folders_external(download_path, root)
            
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao organizar pastas: {e}")

def organize_folders_internal(base_dir, root):
    """Executa a organização internamente (pode congelar)"""
    try:
        # Importa o módulo
        from organize_folders_module import organize_folders
        
        # Cria uma nova janela
        from tkinter import ttk
        import tkinter as tk
        
        progress_window = tk.Toplevel(root)
        progress_window.title("Organizando Pastas")
        progress_window.geometry("1200x600")
        
        # Frame principal com split
        main_frame = ttk.Frame(progress_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Frame esquerdo para progresso
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Frame direito para terminal
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Frame para progresso
        progress_frame = ttk.LabelFrame(left_frame, text="Progresso", padding="5")
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Label de status
        status_label = ttk.Label(progress_frame, text="Iniciando organização...")
        status_label.pack(pady=10)
        
        # Barra de progresso
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100)
        progress_bar.pack(fill=tk.X, padx=10, pady=5)
        
        # Label de contagem
        count_label = ttk.Label(progress_frame, text="0/0 arquivos processados")
        count_label.pack(pady=5)
        
        # Frame para o terminal
        terminal_frame = ttk.LabelFrame(right_frame, text="Terminal", padding="5")
        terminal_frame.pack(fill=tk.BOTH, expand=True)
        
        # Terminal
        terminal_scroll = ttk.Scrollbar(terminal_frame)
        terminal_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        terminal = tk.Text(terminal_frame,
                         wrap=tk.WORD,
                         yscrollcommand=terminal_scroll.set,
                         bg='black',
                         fg='white',
                         font=('Consolas', 10),
                         height=20)
        terminal.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        terminal_scroll.config(command=terminal.yview)
        
        # Configura o terminal como somente leitura
        terminal.config(state='disabled')
        
        # Função para adicionar texto ao terminal
        def append_to_terminal(text, color='white'):
            try:
                if progress_window.winfo_exists() and terminal.winfo_exists():
                    terminal.config(state='normal')
                    terminal.tag_configure(color, foreground=color)
                    terminal.insert(tk.END, f"{text}\n", color)
                    terminal.see(tk.END)
                    terminal.config(state='disabled')
                    terminal.update_idletasks()
            except Exception as e:
                print(f"Erro ao atualizar terminal: {str(e)}")

        # Função para atualizar a interface de forma segura
        def safe_update_interface(text, progress=None):
            try:
                if progress_window.winfo_exists():
                    if text:
                        status_label.config(text=text)
                        append_to_terminal(text)
                    if progress is not None:
                        progress_var.set(progress)
                        count_label.config(text=f"{progress:.1f}%")
                    progress_window.update_idletasks()
            except Exception as e:
                print(f"Erro ao atualizar interface: {str(e)}")

        def process_organization():
            try:
                resultado = organize_folders(base_dir, safe_update_interface, append_to_terminal)
                
                if "error" in resultado:
                    append_to_terminal(f"❌ Erro: {resultado['error']}", 'red')
                    messagebox.showerror("Erro", f"Erro ao organizar pastas: {resultado['error']}")
                else:
                    append_to_terminal(f"\n✨ Organização concluída:", 'cyan')
                    append_to_terminal(f"📦 Arquivos processados: {resultado['arquivos_processados']}", 'green')
                    append_to_terminal(f"📁 Arquivos movidos: {resultado['arquivos_movidos']}", 'green')
                    append_to_terminal(f"🎥 Arquivos 4K: {resultado['arquivos_4k']}", 'green')
                    
                    messagebox.showinfo("Sucesso", 
                        f"Organização concluída com sucesso!\n\n"
                        f"Arquivos processados: {resultado['arquivos_processados']}\n"
                        f"Arquivos movidos: {resultado['arquivos_movidos']}")
                
            except Exception as e:
                append_to_terminal(f"❌ Erro ao organizar pastas: {str(e)}", 'red')
                messagebox.showerror("Erro", f"Erro ao organizar pastas: {e}")
            finally:
                progress_window.destroy()
        
        # Inicia o processamento em uma thread separada
        threading.Thread(target=process_organization).start()
        
    except ImportError:
        messagebox.showerror("Erro", "Módulo organize_folders_module.py não encontrado!")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao organizar pastas: {e}")

def organize_folders_external(base_dir, root):
    """Executa a organização externamente (recomendado)"""
    try:
        # Comando para executar o módulo externo
        cmd = [sys.executable, "organize_folders_module.py", base_dir]
        
        # Executa o processo externo
        processo = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Mostra mensagem informativa
        messagebox.showinfo(
            "Processo Externo",
            f"Organização iniciada em processo externo!\n\n"
            f"Diretório: {base_dir}\n"
            f"Processo ID: {processo.pid}\n\n"
            f"O processo continuará rodando mesmo se você fechar o Palantir.\n"
            f"Verifique os logs em: logs/organize_folders_*.log"
        )
        
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao iniciar processo externo: {e}")

def clean_folders_wrapper(download_path, root):
    """
    Wrapper para limpar pastas com opção de execução interna ou externa
    
    Args:
        download_path: Caminho do diretório para limpar
        root: Tkinter root para mostrar diálogos
    """
    try:
        if not os.path.exists(download_path):
            messagebox.showerror("Erro", "Pasta de download inválida.")
            return

        # Pergunta se quer executar internamente ou externamente
        resposta = messagebox.askyesnocancel(
            "Escolha o modo de execução",
            "Como deseja executar a limpeza?\n\n"
            "Sim = Executar internamente (pode congelar)\n"
            "Não = Executar externamente (recomendado)\n"
            "Cancelar = Cancelar operação"
        )
        
        if resposta is None:  # Cancelar
            return
        elif resposta:  # Executar internamente
            clean_folders_internal(download_path, root)
        else:  # Executar externamente
            clean_folders_external(download_path, root)
            
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao limpar pastas: {e}")

def clean_folders_internal(path, root):
    """Executa a limpeza internamente (pode congelar)"""
    try:
        # Importa o módulo
        from clean_folders_module import clean_folders
        
        # Cria uma nova janela
        from tkinter import ttk
        import tkinter as tk
        
        progress_window = tk.Toplevel(root)
        progress_window.title("Limpando Pastas")
        progress_window.geometry("1200x600")
        
        # Frame principal com split
        main_frame = ttk.Frame(progress_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Frame esquerdo para progresso
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Frame direito para terminal
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Frame para progresso
        progress_frame = ttk.LabelFrame(left_frame, text="Progresso", padding="5")
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Label de status
        status_label = ttk.Label(progress_frame, text="Iniciando limpeza...")
        status_label.pack(pady=10)
        
        # Barra de progresso
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100)
        progress_bar.pack(fill=tk.X, padx=10, pady=5)
        
        # Label de contagem
        count_label = ttk.Label(progress_frame, text="0/0 itens processados")
        count_label.pack(pady=5)
        
        # Frame para o terminal
        terminal_frame = ttk.LabelFrame(right_frame, text="Terminal", padding="5")
        terminal_frame.pack(fill=tk.BOTH, expand=True)
        
        # Terminal
        terminal_scroll = ttk.Scrollbar(terminal_frame)
        terminal_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        terminal = tk.Text(terminal_frame,
                         wrap=tk.WORD,
                         yscrollcommand=terminal_scroll.set,
                         bg='black',
                         fg='white',
                         font=('Consolas', 10),
                         height=20)
        terminal.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        terminal_scroll.config(command=terminal.yview)
        
        # Configura o terminal como somente leitura
        terminal.config(state='disabled')
        
        # Função para adicionar texto ao terminal
        def append_to_terminal(text, color='white'):
            try:
                if progress_window.winfo_exists() and terminal.winfo_exists():
                    terminal.config(state='normal')
                    terminal.tag_configure(color, foreground=color)
                    terminal.insert(tk.END, f"{text}\n", color)
                    terminal.see(tk.END)
                    terminal.config(state='disabled')
                    terminal.update_idletasks()
            except Exception as e:
                print(f"Erro ao atualizar terminal: {str(e)}")

        # Função para atualizar a interface de forma segura
        def safe_update_interface(text, progress=None):
            try:
                if progress_window.winfo_exists():
                    if text:
                        status_label.config(text=text)
                        append_to_terminal(text)
                    if progress is not None:
                        progress_var.set(progress)
                        count_label.config(text=f"{progress:.1f}%")
                    progress_window.update_idletasks()
            except Exception as e:
                print(f"Erro ao atualizar interface: {str(e)}")

        def process_cleaning():
            try:
                resultado = clean_folders(path, safe_update_interface, append_to_terminal)
                
                if "error" in resultado:
                    append_to_terminal(f"❌ Erro: {resultado['error']}", 'red')
                    messagebox.showerror("Erro", f"Erro ao limpar pastas: {resultado['error']}")
                else:
                    append_to_terminal(f"\n✨ Limpeza concluída:", 'cyan')
                    append_to_terminal(f"📦 Arquivos movidos: {resultado['arquivos_movidos']}", 'green')
                    append_to_terminal(f"🗑️ Pastas removidas: {resultado['pastas_removidas']}", 'green')
                    append_to_terminal(f"⚠️ Pastas ignoradas: {resultado['pastas_ignoradas']}", 'yellow')
                    
                    messagebox.showinfo("Sucesso", 
                        f"Limpeza concluída com sucesso!\n\n"
                        f"Arquivos movidos: {resultado['arquivos_movidos']}\n"
                        f"Pastas removidas: {resultado['pastas_removidas']}")
                
            except Exception as e:
                append_to_terminal(f"❌ Erro ao limpar pastas: {str(e)}", 'red')
                messagebox.showerror("Erro", f"Erro ao limpar pastas: {e}")
            finally:
                progress_window.destroy()
        
        # Inicia o processamento em uma thread separada
        threading.Thread(target=process_cleaning).start()
        
    except ImportError:
        messagebox.showerror("Erro", "Módulo clean_folders_module.py não encontrado!")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao limpar pastas: {e}")

def clean_folders_external(path, root):
    """Executa a limpeza externamente (recomendado)"""
    try:
        # Comando para executar o módulo externo
        cmd = [sys.executable, "clean_folders_module.py", path]
        
        # Executa o processo externo
        processo = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Mostra mensagem informativa
        messagebox.showinfo(
            "Processo Externo",
            f"Limpeza iniciada em processo externo!\n\n"
            f"Diretório: {path}\n"
            f"Processo ID: {processo.pid}\n\n"
            f"O processo continuará rodando mesmo se você fechar o Palantir.\n"
            f"Verifique os logs em: logs/clean_folders_*.log"
        )
        
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao iniciar processo externo: {e}")

if __name__ == "__main__":
    print("Este módulo deve ser importado, não executado diretamente.")
    print("Use as funções:")
    print("- organize_folders_wrapper(download_path, root)")
    print("- clean_folders_wrapper(download_path, root)") 