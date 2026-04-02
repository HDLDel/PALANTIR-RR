@echo off
REM Script para limpar cache de ícones e recompilar o Palantir

REM Muda para o diretorio do script
cd /d "%~dp0"

REM Navega para a pasta raiz do projeto (pai da pasta Compile)
cd ..

REM Salva o caminho da raiz do projeto
set PROJECT_DIR=%CD%

echo ============================================================
echo Limpando cache de icones do Windows
echo ============================================================

REM Para o Windows 10/11
ie4uinit.exe -ClearIconCache

REM Para versoes mais antigas
del /f /q "%localappdata%\IconCache.db"
del /f /q "%localappdata%\Microsoft\Windows\Explorer\iconcache*"

REM Reinicia o Explorer (opcional - descomente se necessario)
REM taskkill /f /im explorer.exe
REM start explorer.exe

echo.
echo ============================================================
echo Recompilando Palantir
echo ============================================================
echo.

python "%PROJECT_DIR%\Compile\build_windows.py"

echo.
echo ============================================================
echo Cache limpo e build concluido!
echo Por favor, reinicie o Windows Explorer ou faca logoff/logon
echo para ver o novo icone na barra de tarefas.
echo ============================================================

pause
