# Palantir-RR

Gerenciador desktop **multiplataforma (Windows e Linux)** para baixar, organizar e reproduzir vídeos de **listas M3U / IPTV**.

Esta é a linha **RR** do Palantir: a versão mais recente, com todos os recursos novos. As outras variantes (LTS, MTS e Tester) estão descritas em [`doc/PALANTIR-RESUMO.txt`](doc/PALANTIR-RESUMO.txt). Versão atual: **V3.5.40**.

## O que faz

- **Downloads** — baixa vários vídeos ao mesmo tempo via `aria2c`, com retomada, barra de progresso, controle de tentativas e detecção automática de `.mp4` / `.mkv`.
- **Organização** — usa a API do **TMDB** para classificar filmes e séries por gênero em mais de 25 categorias.
- **Busca** — pesquisa por nome, URL, categoria, tipo, servidor e temporada, com normalização de acentos e índice em SQLite.
- **Reprodução** — integra **MPV** (principal) e **VLC** (alternativo), incluindo AppImage no Linux.
- **M3U** — lê listas remotas, faz parse de `EXTINF`, extrai `group-title`, detecta séries `SxxExx` e identifica o servidor de origem.
- **Interface** — CustomTkinter com temas customizáveis, modo escuro e atualizações seguras entre threads.

## Tecnologias

Python 3.8+, `customtkinter`, `ttkthemes`, `Pillow`, `requests`, `aria2p`, `urllib3`, `unidecode`, `psutil`, `loguru`, `websocket-client`, `sqlite3` (nativo) e `aria2c`. Os executáveis são gerados com **PyInstaller**.

## Estrutura

```
Palantir-Linux.py        # aplicação principal (Linux)
Palantir-windows.py      # aplicação principal (Windows)
advanced_downloader.py   # motor de download
organize_folders.py      # organização por gênero
categorias.py            # categorias e normalização
modulos/                 # gerenciadores: download, banco, busca, M3U, player, config, rede
downloaders/             # geradores de categorias e download CLI
doc/                     # arquitetura e resumos do projeto
build_*.py / build_*.sh  # scripts de compilação
```

## Instalação

```bash
python3 -m venv venv
source venv/bin/activate        # Linux
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

É necessário ter o binário do **aria2c** disponível (o Windows já inclui `aria2c.exe` no repo) e os players em `Players/`.

## Configuração

O arquivo `config.json` é local e **não é versionado**. Exemplo com placeholders:

```json
{
  "default_download_path": "<CAMINHO_DE_DOWNLOADS>",
  "user_agent": "<SEU_USER_AGENT>",
  "dns_server": "1.0.0.1",
  "theme": "black",
  "m3u_base_url": "<URL_DA_SUA_LISTA_M3U>",
  "tmdb_api_key": ""
}
```

A chave da API do TMDB deve ficar na variável de ambiente, nunca no código:

```bash
export TMDB_API_KEY="<SUA_CHAVE_TMDB>"
```

Em `aria2.conf`, substitua o `rpc-secret` placeholder por um valor aleatório antes de usar o RPC.

## Executando

```bash
python3 Palantir-Linux.py       # Linux
python  Palantir-windows.py     # Windows
```

## Compilando

- Linux: `./build_palantir_linux.sh` ou `python3 build_linux.py`
- Windows: `build_palantir_windows.bat` ou `python build_windows.py`
- AppImage: `python3 build_appimage.py`

## Documentação

- [`doc/architecture.html`](doc/architecture.html) — diagrama interativo da arquitetura.
- [`doc/PALANTIR-RESUMO.txt`](doc/PALANTIR-RESUMO.txt) — visão geral, dependências e mapa de módulos.
- [`doc/RESUMO_FIX.txt`](doc/RESUMO_FIX.txt) — correção de *Bus Error* envolvendo Tkinter/ttkthemes.

## Segurança

Nunca commite credenciais, tokens, bancos de dados ou logs. O `.gitignore` já cobre `config.json`, `.env`, `*.db`, `*.log`, `.qwen/`, `publish/` e artefatos de build. Use `<PLACEHOLDER>` em código e `""` em JSON.

## Licença

MIT — veja [`LICENSE`](LICENSE).
