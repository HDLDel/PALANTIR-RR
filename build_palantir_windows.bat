@echo off
chcp 65001 >nul 2>&1
cls

REM Muda para o diretorio do script
cd /d "%~dp0"

REM Detecta se ja esta na pasta raiz do projeto
if exist "Palantir-windows.py" (
    set PROJECT_DIR=%CD%
) else if exist "Palantir-Linux.py" (
    set PROJECT_DIR=%CD%
) else (
    cd ..
    set PROJECT_DIR=%CD%
)

echo ============================================================
echo          Palantir Windows Build Tool
echo ============================================================
echo.
echo Este script ira compilar o Palantir com todas as dependencias
echo e executaveis embutidos.
echo.
echo ============================================================
echo.

REM Verifica se Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado!
    echo.
    echo Por favor, instale o Python 3.8 ou superior de:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [OK] Python detectado
python --version
echo.

REM Executa o script de build automatico (recomendado)
echo Iniciando o processo de build...
echo.
echo [INFO] Usando build_windows.py (build automatico)
echo.

python "%PROJECT_DIR%\build_windows.py"

if %errorlevel% neq 0 (
    echo.
    echo ============================================================
    echo [ERRO] Build falhou!
    echo ============================================================
    echo.
    echo Verifique se os seguintes arquivos existem:
    echo   - aria2c.exe (na raiz ou pasta aria2c/)
    echo   - Players/mpv/mpv.exe
    echo   - Players/VLCPortable/VLCPortable.exe
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Build concluido com sucesso!
echo ============================================================
echo.
echo O programa compilado estara na pasta: dist\Palantir\
echo.
echo Estrutura gerada:
echo   dist\Palantir\
echo   +-- Palantir.exe
echo   +-- aria2c.exe
echo   +-- Players\
echo   ^|    +-- mpv\mpv.exe
echo   ^|    +-- VLCPortable\VLCPortable.exe
echo   +-- [bibliotecas]
echo.
echo Para usar:
echo   1. Navegue ate dist\Palantir\
echo   2. Execute Palantir.exe
echo.
echo Para distribuir:
echo   1. Copie toda a pasta dist\Palantir\
echo   2. Compacte em ZIP (opcional)
echo   3. Distribua
echo.
pause
