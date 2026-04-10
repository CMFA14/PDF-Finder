"""Módulo de autenticação com Google Drive API."""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import SCOPES, CREDENTIALS_FILE, TOKEN_FILE


def authenticate():
    """
    Autentica o usuário com Google Drive API.
    Na primeira vez, abre o navegador para login.
    Nas próximas, usa o token salvo.
    
    Returns:
        Credentials: credenciais autenticadas
    """
    creds = None

    # Verifica se já existe um token salvo
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # Se não há credenciais válidas, faz o fluxo de autenticação
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Renovando token de acesso...")
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"❌ Arquivo '{CREDENTIALS_FILE}' não encontrado!\n"
                    "Baixe-o do Google Cloud Console:\n"
                    "https://console.cloud.google.com/apis/credentials"
                )
            print("🔐 Abrindo navegador para autenticação...")
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Salva o token para próximas execuções
        with open(TOKEN_FILE, "w") as token_file:
            token_file.write(creds.to_json())
            print("✅ Token salvo com sucesso!")

    return creds


def get_drive_service():
    """
    Retorna o serviço autenticado do Google Drive.
    
    Returns:
        Resource: serviço do Google Drive API
    """
    creds = authenticate()
    service = build("drive", "v3", credentials=creds)
    print("✅ Conectado ao Google Drive com sucesso!")
    return service