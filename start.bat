@echo off
:: Painel TRL Delta — Script de inicialização (Windows)
:: -----------------------------------------------------------
:: Ativa o venv, instala dependências e inicia o servidor
:: na porta 8051.  Acesse via http://inovacao.delta.local
:: (configure o nginx + hosts antes de usar o domínio).
:: -----------------------------------------------------------

cd /d "%~dp0"

echo [1/4] Verificando ambiente virtual...
if not exist ".venv\Scripts\activate.bat" (
    echo     Criando venv...
    python -m venv .venv
    if errorlevel 1 (
        echo ERRO: `python` nao encontrado. Instale o Python 3.11+.
        pause
        exit /b 1
    )
)

call .venv\Scripts\activate.bat

echo [2/4] Instalando / atualizando dependencias...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

echo [3/4] Inicializando banco de dados...
python -c "from app import server; from database import db; db.create_all(app=server.app_context().__enter__())" 2>nul
:: A inicializacao real ocorre dentro do app.py (seed_database)

echo [4/4] Iniciando servidor na porta 8051...
echo     URL local:  http://127.0.0.1:8051
echo     URL nginx:  http://inovacao.delta.local
echo.
python app.py

pause
