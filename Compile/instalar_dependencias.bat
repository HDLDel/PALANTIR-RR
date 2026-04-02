@echo off
setlocal EnableDelayedExpansion

REM Muda para o diretorio do script
cd /d "%~dp0"

REM Navega para a pasta raiz do projeto (pai da pasta Compile)
cd ..

REM Salva o caminho da raiz do projeto
set PROJECT_DIR=%CD%

echo ============================================================
echo          INSTALADOR DE DEPENDENCIAS - PALANTIR
echo ============================================================
echo.

:: Verifica se o Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado!
    echo.
    echo Por favor, instale o Python 3.8 ou superior:
    echo https://www.python.org/downloads/
    echo.
    echo Durante a instalacao, marque a opcao "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

:: Mostra versao do Python
for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [OK] Python detectado: %PYTHON_VERSION%
echo.

:: Verifica versao do Python (deve ser 3.8+)
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python 3.8 ou superior e necessario!
    echo Sua versao e inferior a 3.8.
    echo.
    pause
    exit /b 1
)

:: Atualiza o pip
echo [INFO] Atualizando o pip...
python -m pip install --upgrade pip --quiet
if %errorlevel% neq 0 (
    echo [AVISO] Nao foi possivel atualizar o pip, continuando...
)
echo.

:: Instala as dependencias do requirements.txt
if exist "%PROJECT_DIR%\Compile\requirements.txt" (
    echo [INFO] Instalando dependencias do requirements.txt...
    echo.
    python -m pip install -r "%PROJECT_DIR%\Compile\requirements.txt"
    if %errorlevel% neq 0 (
        echo.
        echo [ERRO] Falha ao instalar algumas dependencias!
        echo.
        pause
        exit /b 1
    )
    echo.
    echo [OK] Dependencias instaladas com sucesso!
) else (
    echo [AVISO] requirements.txt nao encontrado, instalando pacotes manualmente...
    echo.

    :: Instala cada pacote individualmente
    echo [INFO] Instalando requests...
    python -m pip install requests>=2.31.0 --quiet

    echo [INFO] Instalando aria2p...
    python -m pip install aria2p>=0.12.1 --quiet

    echo [INFO] Instalando Pillow...
    python -m pip install Pillow>=8.0.0 --quiet

    echo [INFO] Instalando customtkinter...
    python -m pip install customtkinter>=5.2.0 --quiet

    echo [INFO] Instalando unidecode...
    python -m pip install unidecode>=1.3.8 --quiet

    echo [INFO] Instalando ttkthemes...
    python -m pip install ttkthemes>=3.2.2 --quiet

    echo [INFO] Instalando psutil...
    python -m pip install psutil>=5.9.0 --quiet

    echo [INFO] Instalando urllib3...
    python -m pip install urllib3>=2.0.0 --quiet

    echo [INFO] Instalando websocket-client...
    python -m pip install websocket-client>=1.8.0 --quiet

    echo [INFO] Instalando loguru...
    python -m pip install loguru>=0.7.3 --quiet

    echo [INFO] Instalando platformdirs...
    python -m pip install platformdirs>=4.3.7 --quiet

    echo [INFO] Instalando colorama...
    python -m pip install colorama>=0.4.6 --quiet

    echo [INFO] Instalando pyinstaller...
    python -m pip install pyinstaller>=6.0.0 --quiet

    echo.
    echo [OK] Todas as dependencias instaladas!
)

echo.
echo ============================================================
echo          INSTALACAO CONCLUIDA COM SUCESSO!
echo ============================================================
echo.
echo Dependencias instaladas:
echo   - requests (requisicoes HTTP)
echo   - aria2p (gerenciamento de downloads)
echo   - Pillow (processamento de imagens)
echo   - customtkinter (interface grafica moderna)
echo   - unidecode (normalizacao de texto)
echo   - ttkthemes (temas para tkinter)
echo   - psutil (informacoes do sistema)
echo   - urllib3 (cliente HTTP)
echo   - websocket-client (conexao websocket)
echo   - loguru (logging)
echo   - platformdirs (diretorios da plataforma)
echo   - colorama (cores no terminal)
echo   - pyinstaller (compilacao para executavel)
echo.
echo Proximos passos:
echo   1. Verifique se os executaveis estao na pasta do projeto:
echo      - aria2c.exe
echo      - Players/mpv/mpv.exe
echo      - Players/VLCPortable/VLCPortable.exe
echo.
echo   2. Para compilar o programa, execute:
echo      python Compile/build_windows.py
echo      ou
echo      Compile/build.bat
echo.
echo ============================================================
pause
