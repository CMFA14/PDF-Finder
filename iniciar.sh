#!/bin/bash

echo ""
echo "══════════════════════════════════════════════════"
echo "  📄 Busca de Comprovantes - Google Drive"
echo "══════════════════════════════════════════════════"
echo ""

# Verifica Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado!"
    echo "Instale com: sudo apt install python3 python3-pip"
    exit 1
fi

# Verifica dependências
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Instalando dependências..."
    pip3 install -r requirements.txt
    echo ""
fi

# Verifica credentials.json
if [ ! -f "credentials.json" ]; then
    echo "❌ credentials.json não encontrado!"
    exit 1
fi

echo "✅ Tudo pronto!"
echo ""
echo "🌐 Abrindo: http://localhost:5000"
echo "⚠️  Pressione Ctrl+C para parar."
echo ""

# Abre navegador após 2 segundos
(sleep 2 && xdg-open http://localhost:5000 2>/dev/null || open http://localhost:5000 2>/dev/null) &

# Inicia servidor
python3 server.py