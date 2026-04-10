@echo off
chcp 65001 >nul
title Instalacao - Busca de Comprovantes

echo ══════════════════════════════════════════════════
echo   INSTALACAO - Busca de Comprovantes
echo ══════════════════════════════════════════════════
echo.

echo [1/3] Verificando Python...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Python nao encontrado!
    echo Baixe em: https://www.python.org/downloads/
    echo Marque "Add Python to PATH" na instalacao.
    pause
    exit /b 1
)

echo.
echo [2/3] Instalando dependencias...
pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Erro ao instalar dependencias!
    pause
    exit /b 1
)

echo.
echo [3/3] Verificando credentials.json...
if not exist "credentials.json" (
    echo.
    echo ⚠️  ATENCAO: arquivo credentials.json nao encontrado!
    echo Baixe-o do Google Cloud Console e coloque nesta pasta.
    echo.
)

echo.
echo ══════════════════════════════════════════════════
echo   ✅ INSTALACAO CONCLUIDA!
echo   Agora execute: iniciar.bat
echo ══════════════════════════════════════════════════
echo.
pause