@echo off
REM Muda para o diretorio do script
cd /d "%~dp0"

cls
echo ======================================================
echo           GIT AUTO-COMMIT - TheLordCLI
echo ======================================================
echo.

:: 1. Pergunta qual a mensagem do commit
set /p mensagem="Digite o que voce alterou hoje: "

:: Se o usuario der enter sem digitar nada, define uma mensagem padrao
if "%mensagem%"=="" set mensagem="Atualizacao de rotina"

echo.
echo [+] Removendo arquivos temporarios do Python...
if exist __pycache__ rmdir /s /q __pycache__
if exist *.pyc del /q *.pyc
if exist .pytest_cache rmdir /s /q .pytest_cache
if exist .mypy_cache rmdir /s /q .mypy_cache

echo [+] Preparando arquivos no Git...
git add .

echo [+] Criando ponto de restauracao (Commit)...
git commit -m "%mensagem%"

echo.
echo ======================================================
echo           SUCESSO! PROJETO VERSIONADO
echo ======================================================
echo.
echo Ultimos 5 registros no historico:
git log --oneline -n 5
echo.
pause
