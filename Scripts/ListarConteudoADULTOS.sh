#!/bin/bash

# Diretório onde os filmes estão armazenados
FILMES="/home/del/Files/Files/VODS/FILMES"

# Arquivo de saída
OUTPUT="resultadoADULTOS.txt"

# Limpar o arquivo de saída se existir
> "$OUTPUT"

# Processar cada pasta no diretório FILMES
for pasta in "$FILMES"/*; do
    if [ -d "$pasta" ]; then
        echo "Varrendo $pasta (aguarde...)"
        find "$pasta" -type d -print0 | while IFS= read -r -d '' dir; do
            # Encontrar arquivos com extensões específicas
            arquivos=$(find "$dir" -maxdepth 1 -type f \( -iname "*.mp4" -o -iname "*.mkv" \))
            if [ -n "$arquivos" ]; then
                # Filtrar apenas os que contêm XXX ou [XXX] (case insensitive)
                echo "$arquivos" | grep -i -E "(XXX|\[XXX\])" | while IFS= read -r arquivo; do
                    echo "$arquivo" | sed 's|^'"$FILMES"'/|"|' | sed 's|$|",|' >> "$OUTPUT"
                done
            fi
        done
    fi
done

echo "Varredura concluída. Resultados salvos em $OUTPUT"
