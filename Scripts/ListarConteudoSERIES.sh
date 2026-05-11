#!/bin/bash

# Diretório onde os filmes estão armazenados
FILMES="/home/del/Files/Files/VODS/SERIES/"

# Arquivo de saída
OUTPUT="resultadoSERIES.txt"

# Limpar o arquivo de saída se existir
> "$OUTPUT"

# Processar cada pasta no diretório FILMES
for pasta in "$FILMES"/*; do
    if [ -d "$pasta" ]; then
        echo "Varrendo $pasta (aguarde...)"
        find "$pasta" -type d -print0 | while IFS= read -r -d '' dir; do
            arquivos=$(find "$dir" -maxdepth 1 -type f \( -iname "*.mp4" -o -iname "*.mkv" \))
            if [ -n "$arquivos" ]; then
                echo "$arquivos" | sed 's|^'"$FILMES"'/|"|' | sed 's|$|",|' >> "$OUTPUT"
            fi
        done
    fi
done

echo "Varredura concluída. Resultados salvos em $OUTPUT"
