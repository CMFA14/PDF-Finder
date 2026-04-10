"""Configurações gerais do projeto."""

# Escopos de acesso ao Google Drive
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# Arquivo de credenciais OAuth2 (baixado do Google Cloud Console)
CREDENTIALS_FILE = "credentials.json"

# Arquivo de token gerado após primeira autenticação
TOKEN_FILE = "token.json"

# Tipos MIME para filtrar apenas PDFs
PDF_MIME_TYPE = "application/pdf"

# Pasta temporária para download dos PDFs
TEMP_DOWNLOAD_DIR = "temp_pdfs"