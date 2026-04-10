# PDF Extraction Engine (Versão de Teste Local)

Uma ferramenta técnica para busca e extração de dados de arquivos PDF armazenados localmente. Esta versão foi projetada para processamento de alta performance de comprovantes e documentos através de extração de texto estruturada.

## Funcionalidades
- **Busca Local**: Escaneia qualquer diretório recursivamente em busca de PDFs que correspondam a padrões de data específicos (DD-MM).
- **Extração Profunda**: Utiliza `pdfplumber` e `PyPDF2` para extrair textos, tabelas e metadados.
- **Parsing Inteligente**: Identifica automaticamente beneficiários, valores, datas e chaves de autenticação usando padrões regex.
- **Visualização/Recorte**: Permite visualizar páginas isoladas que contêm as correspondências e salvá-las individualmente.

## Pré-requisitos
- Python 3.8+
- `pip install -r requirements.txt`

## Configuração
1. Renomeie `.env.example` para `.env`.
2. Configure o `LOCAL_PATH` com o caminho da pasta que contém seus PDFs:
   ```env
   LOCAL_PATH=C:\Caminho\Para\Seus\PDFs
   ```

## Como Usar
1. Inicie o servidor:
   ```bash
   python server.py
   ```
   *Ou use o atalho `iniciar.bat` fornecido.*
2. Abra `http://localhost:5000` no seu navegador.
3. Insira o dia/mês dos arquivos que deseja escanear.
4. Forneça uma palavra-chave (nome, CNPJ ou parte de um código) para iniciar a extração.

## Detalhes Técnicos
- **Backend**: Flask (Python)
- **Motor PDF**: `pdfplumber` para análise profunda, `PyPDF2` para indexação rápida.
- **Frontend**: Vanilla JS com streaming NDJSON para atualizações de extração em tempo real.
