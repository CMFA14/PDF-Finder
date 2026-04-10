@echo off
chcp 65001 >nul
title Busca de Comprovantes - Google Drive

echo.
echo ══════════════════════════════════════════════════
echo   📄 Busca de Comprovantes - Google Drive
echo ══════════════════════════════════════════════════
echo.

:: Verifica se o Python existe
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python nao encontrado!
    echo Execute setup.bat primeiro.
    pause
    exit /b 1
)

:: Verifica se o Flask está instalado
python -c "import flask" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️  Dependencias nao instaladas.
    echo Executando instalacao automatica...
    echo.
    pip install -r requirements.txt
    echo.
)

:: Verifica credentials.json
if not exist "credentials.json" (
    echo ❌ credentials.json nao encontrado!
    echo Coloque o arquivo nesta pasta e tente novamente.
    pause
    exit /b 1
)

:: Verifica server.py
if not exist "server.py" (
    echo ❌ server.py nao encontrado!
    pause
    exit /b 1
)

echo ✅ Tudo pronto!
echo.
echo 🌐 Abrindo navegador em 3 segundos...
echo    http://localhost:5000
echo.
echo ⚠️  NAO FECHE ESTA JANELA enquanto estiver usando.
echo    Para parar, pressione Ctrl+C ou feche esta janela.
echo.
echo ══════════════════════════════════════════════════
echo.

:: Abre o navegador após 3 segundos
start /b cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:5000"

:: Inicia o servidor
python server.py

:: Se o servidor parar
echo.
echo ══════════════════════════════════════════════════
echo   Servidor encerrado.
echo ══════════════════════════════════════════════════
pause