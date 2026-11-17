@echo off
REM Roda o RankEdu com dados ficticios. Basta dar dois cliques neste arquivo.
REM 1a vez: cria o ambiente e instala o Flask (alguns minutos). Depois: so liga o servidor.
setlocal
cd /d "%~dp0"
title RankEdu - demonstracao

python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if errorlevel 1 (
    echo.
    echo [ERRO] Python 3.10 ou mais novo nao encontrado.
    echo Instale em https://www.python.org/downloads/ e marque "Add python.exe to PATH".
    goto fim
)

if not exist ".venv\Scripts\python.exe" (
    echo Criando o ambiente virtual .venv ...
    python -m venv .venv || goto erro
)

if not exist ".venv\instalado.ok" (
    echo Instalando as bibliotecas - pode levar alguns minutos ...
    ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt || goto erro
    echo ok> ".venv\instalado.ok"
)

echo.
echo ============================================================
echo   Abra http://localhost:5000
echo   Admin:    admin@rankedu.com   Senha: senha123
echo   Empresa:  carlos@techbr.com   Senha: senha123
echo   Para desligar, feche esta janela.
echo ============================================================
echo.
if not defined DEMO_SEM_NAVEGADOR start "" cmd /c "timeout /t 3 /nobreak >nul & start http://localhost:5000"
cd app
"..\.venv\Scripts\python.exe" app.py
goto fim

:erro
echo.
echo [ERRO] Algo deu errado no passo acima.
echo Se a mensagem fala em "Long Path" ou "No such file or directory", mova a pasta do projeto
echo para um caminho curto (ex.: C:\projetos\rankedu), apague a pasta .venv e rode de novo.

:fim
echo.
pause
