"""Módulo para interação com Google Drive API."""

import os
import io
from typing import Optional
from googleapiclient.http import MediaIoBaseDownload

from config import PDF_MIME_TYPE, TEMP_DOWNLOAD_DIR


class DriveService:
    """Gerencia operações no Google Drive."""

    def __init__(self, service):
        self.service = service
        os.makedirs(TEMP_DOWNLOAD_DIR, exist_ok=True)

    def list_pdfs(
        self,
        folder_id: Optional[str] = None,
        recursive: bool = True
    ) -> list[dict]:
        """
        Lista todos os PDFs no Drive ou em uma pasta específica.

        Args:
            folder_id: ID da pasta no Drive (None = raiz)
            recursive: se True, busca em subpastas também

        Returns:
            Lista de dicts com 'id', 'name' e 'path' dos PDFs
        """
        pdf_files = []

        if folder_id:
            self._list_pdfs_in_folder(folder_id, "", pdf_files, recursive)
        else:
            # Busca todos os PDFs no Drive
            pdf_files = self._search_all_pdfs()

        print(f"📄 {len(pdf_files)} PDF(s) encontrado(s) no Drive.")
        return pdf_files

    def _search_all_pdfs(self) -> list[dict]:
        """Busca todos os PDFs no Drive inteiro."""
        pdf_files = []
        page_token = None

        while True:
            query = (
                f"mimeType='{PDF_MIME_TYPE}' "
                f"and trashed=false"
            )

            results = self.service.files().list(
                q=query,
                spaces="drive",
                fields="nextPageToken, files(id, name, parents)",
                pageToken=page_token,
                pageSize=100
            ).execute()

            for file in results.get("files", []):
                pdf_files.append({
                    "id": file["id"],
                    "name": file["name"],
                    "path": file["name"]
                })

            page_token = results.get("nextPageToken")
            if not page_token:
                break

        return pdf_files

    def _list_pdfs_in_folder(
        self,
        folder_id: str,
        current_path: str,
        pdf_files: list,
        recursive: bool
    ):
        """Busca PDFs recursivamente dentro de uma pasta."""
        page_token = None

        while True:
            # Busca arquivos na pasta atual
            query = f"'{folder_id}' in parents and trashed=false"

            results = self.service.files().list(
                q=query,
                spaces="drive",
                fields="nextPageToken, files(id, name, mimeType)",
                pageToken=page_token,
                pageSize=100
            ).execute()

            for file in results.get("files", []):
                file_path = (
                    f"{current_path}/{file['name']}"
                    if current_path
                    else file["name"]
                )

                if file["mimeType"] == PDF_MIME_TYPE:
                    pdf_files.append({
                        "id": file["id"],
                        "name": file["name"],
                        "path": file_path
                    })
                elif (
                    file["mimeType"] == "application/vnd.google-apps.folder"
                    and recursive
                ):
                    # Entra na subpasta
                    self._list_pdfs_in_folder(
                        file["id"], file_path, pdf_files, recursive
                    )

            page_token = results.get("nextPageToken")
            if not page_token:
                break

    def download_pdf(self, file_id: str, file_name: str) -> str:
        """
        Baixa um PDF do Drive para o disco local.

        Args:
            file_id: ID do arquivo no Drive
            file_name: nome do arquivo

        Returns:
            Caminho local do arquivo baixado
        """
        local_path = os.path.join(TEMP_DOWNLOAD_DIR, f"{file_id}.pdf")

        # Se já foi baixado antes, não baixa novamente
        if os.path.exists(local_path):
            return local_path

        print(f"   ⬇️  Baixando: {file_name}...")

        request = self.service.files().get_media(fileId=file_id)
        file_handle = io.BytesIO()
        downloader = MediaIoBaseDownload(file_handle, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        with open(local_path, "wb") as f:
            f.write(file_handle.getvalue())

        return local_path

    def download_pdf_to_memory(self, file_id: str) -> io.BytesIO:
        """
        Baixa um PDF do Drive direto para memória (sem salvar em disco).

        Args:
            file_id: ID do arquivo no Drive

        Returns:
            BytesIO com o conteúdo do PDF
        """
        request = self.service.files().get_media(fileId=file_id)
        file_handle = io.BytesIO()
        downloader = MediaIoBaseDownload(file_handle, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        file_handle.seek(0)
        return file_handle

    def cleanup_temp_files(self):
        """Remove arquivos temporários baixados."""
        import shutil
        if os.path.exists(TEMP_DOWNLOAD_DIR):
            shutil.rmtree(TEMP_DOWNLOAD_DIR)
            print("🗑️  Arquivos temporários removidos.")