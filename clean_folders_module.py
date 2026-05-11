#!/usr/bin/env python3
"""
Módulo independente para limpar pastas de vídeos
Move arquivos dos subdiretórios para o diretório pai e remove subdiretórios vazios
Pode ser executado separadamente para evitar congelamento do programa principal
"""

import os
import shutil
import time
import sys

def setup_logging(log_dir="logs"):
    """Configura o sistema de logging"""
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, f"clean_folders_{time.strftime('%Y%m%d_%H%M%S')}.log")
    
    def log_message(message, level="INFO"):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
        except Exception as e:
            print(f"Erro ao escrever no log: {e}")
    
    return log_message

def clean_folders(path, progress_callback=None, log_callback=None):
    """
    Move arquivos dos subdiretórios para o diretório pai e remove subdiretórios vazios
    
    Args:
        path: Diretório base para limpeza
        progress_callback: Função para atualizar progresso (opcional)
        log_callback: Função para logging (opcional)
    
    Returns:
        dict: Estatísticas da limpeza
    """
    # Configura logging
    log_func = log_callback if log_callback else setup_logging()
    
    try:
        log_func(f"🧹 Iniciando limpeza em: {path}")
        
        if not os.path.exists(path):
            log_func(f"❌ Diretório não encontrado: {path}")
            return {"error": "Diretório não encontrado"}
        
        # Obtém todos os subdiretórios
        subdirs = [f.path for f in os.scandir(path) if f.is_dir()]
        total_dirs = len(subdirs)
        
        if total_dirs == 0:
            log_func("ℹ️ Não há subdiretórios para processar.")
            return {"arquivos_movidos": 0, "pastas_removidas": 0, "pastas_ignoradas": 0}
        
        log_func(f"📁 Encontrados {total_dirs} subdiretórios para processar")
        
        arquivos_movidos = 0
        pastas_removidas = 0
        pastas_ignoradas = 0
        
        for i, subdir in enumerate(subdirs):
            try:
                # Atualiza progresso se callback fornecido
                if progress_callback:
                    progress = (i + 1) / total_dirs * 100
                    progress_callback(f"Processando: {os.path.basename(subdir)}", progress)
                
                log_func(f"\n📂 Processando diretório: {os.path.basename(subdir)}")
                
                # Verifica se o diretório contém outros diretórios
                tem_subdirs = any(os.path.isdir(os.path.join(subdir, item)) for item in os.listdir(subdir))
                if tem_subdirs:
                    log_func(f"⚠️ Ignorando diretório {os.path.basename(subdir)} pois contém outras pastas")
                    pastas_ignoradas += 1
                    continue
                
                # Move todos os arquivos do subdiretório para o diretório pai
                for arquivo in os.listdir(subdir):
                    origem = os.path.join(subdir, arquivo)
                    destino = os.path.join(path, arquivo)
                    
                    # Se já existe um arquivo com o mesmo nome, adiciona um sufixo
                    if os.path.exists(destino):
                        nome, ext = os.path.splitext(arquivo)
                        i = 1
                        while os.path.exists(destino):
                            novo_nome = f"{nome}_{i}{ext}"
                            destino = os.path.join(path, novo_nome)
                            i += 1
                    
                    try:
                        shutil.move(origem, destino)
                        log_func(f"✅ Movido: {arquivo} → {os.path.basename(destino)}")
                        arquivos_movidos += 1
                    except Exception as e:
                        log_func(f"❌ Erro ao mover {arquivo}: {str(e)}")
                    
                # Remove o subdiretório vazio
                try:
                    os.rmdir(subdir)
                    log_func(f"🗑️ Removido diretório vazio: {os.path.basename(subdir)}")
                    pastas_removidas += 1
                except Exception as e:
                    log_func(f"❌ Erro ao remover diretório {os.path.basename(subdir)}: {str(e)}")
                    
            except Exception as e:
                log_func(f"❌ Erro ao processar diretório {os.path.basename(subdir)}: {str(e)}")
                continue
        
        # Mostra resumo
        log_func(f"\n✨ Limpeza concluída:")
        log_func(f"📦 Arquivos movidos: {arquivos_movidos}")
        log_func(f"🗑️ Pastas removidas: {pastas_removidas}")
        log_func(f"⚠️ Pastas ignoradas: {pastas_ignoradas}")
        
        return {
            "arquivos_movidos": arquivos_movidos,
            "pastas_removidas": pastas_removidas,
            "pastas_ignoradas": pastas_ignoradas
        }
        
    except Exception as e:
        log_func(f"❌ Erro ao processar diretórios: {str(e)}")
        return {"error": str(e)}

def main():
    """Função principal para execução independente"""
    if len(sys.argv) != 2:
        print("Uso: python clean_folders_module.py <diretório>")
        sys.exit(1)
    
    path = sys.argv[1]
    
    if not os.path.exists(path):
        print(f"Erro: Diretório '{path}' não encontrado.")
        sys.exit(1)
    
    print(f"🧹 Iniciando limpeza de pastas em: {path}")
    print("=" * 50)
    
    def progress_callback(message, progress):
        print(f"[{progress:.1f}%] {message}")
    
    def log_callback(message):
        print(message)
    
    resultado = clean_folders(path, progress_callback, log_callback)
    
    if "error" in resultado:
        print(f"❌ Erro: {resultado['error']}")
        sys.exit(1)
    else:
        print("\n" + "=" * 50)
        print("✅ Limpeza concluída com sucesso!")
        print(f"📦 Arquivos movidos: {resultado['arquivos_movidos']}")
        print(f"🗑️ Pastas removidas: {resultado['pastas_removidas']}")
        print(f"⚠️ Pastas ignoradas: {resultado['pastas_ignoradas']}")

if __name__ == "__main__":
    main() 