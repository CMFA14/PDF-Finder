"""
Backend Flask — PDF Search & Data Extraction.
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import io
import re

import pdfplumber
from PyPDF2 import PdfReader, PdfWriter
from dotenv import load_dotenv

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

load_dotenv()

# CONFIGURATION

FOLDER_ID = os.getenv("FOLDER_ID")

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive",
]

CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
PDF_MIME_TYPE = "application/pdf"
FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"
TEMP_PAGES_DIR = "temp_pages"

os.makedirs(TEMP_PAGES_DIR, exist_ok=True)

app = Flask(__name__)

# Cache de PDFs baixados
pdf_cache = {}




# GOOGLE DRIVE AUTHENTICATION

def authenticate():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


def get_drive_service():
    creds = authenticate()
    return build("drive", "v3", credentials=creds)


print("Authenticating with Google Drive...")
drive_service = get_drive_service()
print("Connected to Google Drive!")


# DRIVE UTILS

def get_pdf(file_id):
    """Baixa PDF ou retorna do cache."""
    if file_id not in pdf_cache:
        req = drive_service.files().get_media(
            fileId=file_id, supportsAllDrives=True
        )
        buf = io.BytesIO()
        dl = MediaIoBaseDownload(buf, req)
        done = False
        while not done:
            _, done = dl.next_chunk()
        buf.seek(0)
        pdf_cache[file_id] = buf
    pdf_cache[file_id].seek(0)
    return pdf_cache[file_id]





# ══════════════════════════════════════════════════════════════════
#  SEARCH LOGIC
# ══════════════════════════════════════════════════════════════════

def find_pdfs_by_day_month(day, month):
    """
    Searches for PDFs using a powerful text query in Google Drive.
    """
    dd = str(day).zfill(2)
    mm = str(month).zfill(2)

    # Comprehensive search query to scan nested folders
    query = (
        f"( (name contains '{dd}' and name contains '{mm}') or name contains '{dd}{mm}' ) "
        f"and mimeType='{PDF_MIME_TYPE}' and trashed=false"
    )

    try:
        results = drive_service.files().list(
            q=query, spaces="drive",
            fields="nextPageToken, files(id, name)",
            pageToken=None, pageSize=1000,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()
        found_pdfs = results.get("files", [])
    except Exception as e:
        print("Error in refined search:", e)
        found_pdfs = []

    date_patterns = [
        f"{dd}-{mm}",
        f"{dd}/{mm}",
        f"{dd}.{mm}",
        f"{dd}_{mm}",
        f"{dd} {mm}",
        f"{dd}{mm}",
    ]

    matched = []
    seen = set()
    
    for f in found_pdfs:
        if f["id"] in seen:
            continue
            
        name_upper = f["name"].upper()
        for pattern in date_patterns:
            if pattern in name_upper:
                matched.append(f)
                seen.add(f["id"])
                break

    return matched


# RECEIPT PARSER

def parse_receipt(text):
    info = {
        "beneficiario": "",
        "cnpj_cpf": "",
        "valor": "",
        "data_pagamento": "",
        "referencia": "",
        "status": "",
        "tipo_pagamento": "",
        "codigo_autenticacao": "",
        "banco_destino": "",
        "conta": "",
    }

    patterns = {
        "beneficiario": [
            r"Benefici[aá]rio[:\s]+(.+?)(?:\n|CPF|$)",
            r"Benefici[aá]rio[:\s]+(.+)",
            r"Favorecido[:\s]+(.+?)(?:\n|$)",
            r"Nome[:\s]+(.+?)(?:\n|$)",
        ],
        "cnpj_cpf": [
            r"CPF/CNPJ\s*Benefici[aá]rio[:\s]*(\S+)",
            r"CNPJ[:\s]*(\d[\d./-]+)",
            r"CPF[:\s]*(\d[\d./-]+)",
        ],
        "valor": [
            r"Valor\s+do\s+pagamento[:\s]*([\d.,]+)",
            r"Valor\s+pago[:\s]*([\d.,]+)",
            r"Valor[:\s]*([\d.,]+)",
        ],
        "data_pagamento": [
            r"Data\s+do\s+Pagamento[:\s]*(\d{2}/\d{2}/\d{4})",
            r"Data\s+Pagamento[:\s]*(\d{2}/\d{2}/\d{4})",
            r"Data[:\s]*(\d{2}/\d{2}/\d{4})",
        ],
        "referencia": [
            r"Refer[eê]ncia[:\s]*(\S+)",
            r"C[oó]d\.?\s*barras[:\s]*(\S+)",
        ],
        "status": [
            r"Status\s+(\w+)",
        ],
        "tipo_pagamento": [
            r"Tipo\s+do\s+Pagamento[:\s]*(.+?)(?:\n|$)",
            r"Tipo[:\s]*(.+?)(?:\n|$)",
        ],
        "codigo_autenticacao": [
            r"[Cc][oó]digo\s+de\s+autentica[cç][aã]o[^:]*[:\s]*(\S+)",
            r"Autentica[cç][aã]o[:\s]*(\S+)",
        ],
    }

    for field, field_patterns in patterns.items():
        for pat in field_patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if value:
                    info[field] = value
                    break

    return info


# PDF CONTENT SEARCH

def search_code_in_pdf(pdf_bytes_original, code):
    results = []
    pattern = re.escape(code)
    
    # Copia de memoria para nao corromper a leitura
    pdf_copy = io.BytesIO(pdf_bytes_original.getvalue())
    pdf_copy2 = io.BytesIO(pdf_bytes_original.getvalue())

    # --- PASSO FAST (PyPDF2) ---
    # PyPDF2 é até 50x mais rapido que pdfplumber para ler string pura.
    # Ele filtra em milésimos de segundo exatamente qual das 100 páginas tem o código.
    reader = PdfReader(pdf_copy)
    total_pages = len(reader.pages)
    
    pages_with_code = []
    for page_num, page in enumerate(reader.pages, 1):
        try:
            text = page.extract_text() or ""
            if re.search(pattern, text, re.IGNORECASE):
                pages_with_code.append(page_num)
        except Exception:
            pages_with_code.append(page_num)  # Na duvida, pesquisa nesta pagina

    # Se PyPDF2 não achou, não abrimos o PDFPlumber pesado, pula arquivo!
    if not pages_with_code:
        return []

    # --- PASSO DEEP (pdfplumber) ---
    # Agora focamos só na página que importa (leva 0.2s)
    with pdfplumber.open(pdf_copy2) as pdf:
        for page_num in pages_with_code:
            # pdfplumber é 0-indexado
            if page_num - 1 >= len(pdf.pages):
                continue
                
            page = pdf.pages[page_num - 1]
            text = page.extract_text() or ""

            if re.search(pattern, text, re.IGNORECASE):
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        for row in table:
                            cells = [c if c else "" for c in row]
                            text += "\n" + " | ".join(cells)
                            
                receipt_info = parse_receipt(text)

                matched_line = ""
                for line in text.split("\n"):
                    if re.search(pattern, line, re.IGNORECASE):
                        matched_line = line.strip()
                        break

                results.append({
                    "page": page_num,
                    "total_pages": total_pages,
                    "matched_line": matched_line,
                    "page_text": text,
                    "receipt": receipt_info,
                })
                
    return results


def extract_pdf_page(pdf_bytes, page_number):
    pdf_copy = io.BytesIO(pdf_bytes.getvalue())
    reader = PdfReader(pdf_copy)
    writer = PdfWriter()
    writer.add_page(reader.pages[page_number - 1])
    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output


# FLASK ROUTES

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    try:
        drive_service.files().get(
            fileId=FOLDER_ID,
            supportsAllDrives=True,
            fields="id, name",
        ).execute()
        return jsonify({"connected": True})
    except Exception as e:
        return jsonify({"connected": False, "error": str(e)})


# ─── SEARCH & EXTRACTION ───

@app.route("/api/list-files", methods=["POST"])
def api_list_files():
    """Lists PDFs filtering by day/month."""
    data = request.get_json()
    day = data.get("day", "").strip()
    month = data.get("month", "").strip()

    errors = []
    if not day or not day.isdigit() or not (1 <= int(day) <= 31):
        errors.append("Invalid day")
    if not month or not month.isdigit() or not (1 <= int(month) <= 12):
        errors.append("Invalid month")
    if errors:
        return jsonify({"success": False, "error": " | ".join(errors)})

    try:
        matched = find_pdfs_by_day_month(day, month)

        if not matched:
            dd = day.zfill(2)
            mm = month.zfill(2)
            return jsonify({
                "success": False,
                "error": (
                    f"No PDF found containing {dd}-{mm} in the name"
                ),
            })

        file_list = [
            {"id": f["id"], "name": f["name"], "path": f.get("path", f["name"])}
            for f in matched
        ]

        return jsonify({
            "success": True,
            "total_files": len(file_list),
            "files": file_list,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/search-single-pdf", methods=["POST"])
def api_search_single_pdf():
    """Buscador unitário que roda no frontend arquivo por arquivo em lote visual (STREAMING NDJSON)."""
    data = request.get_json()
    code = data.get("code", "").strip()
    file_id = data.get("file_id", "").strip()
    file_name = data.get("file_name", "").strip()

    if not code:
        return jsonify({"success": False, "error": "Código obrigatório"})
    if not file_id:
        return jsonify({"success": False, "error": "ID do arquivo ausente"})

    def generate():
        try:
            pdf_bytes = get_pdf(file_id)
            pattern = re.escape(code)
            
            pdf_copy = io.BytesIO(pdf_bytes.getvalue())
            pdf_copy2 = io.BytesIO(pdf_bytes.getvalue())

            reader = PdfReader(pdf_copy)
            total_pages = len(reader.pages)
            
            with pdfplumber.open(pdf_copy2) as pdf:
                for page_num, page in enumerate(reader.pages, 1):
                    try:
                        text = page.extract_text() or ""
                        if re.search(pattern, text, re.IGNORECASE):
                            if page_num - 1 < len(pdf.pages):
                                deep_page = pdf.pages[page_num - 1]
                                deep_text = deep_page.extract_text() or ""
                                tables = deep_page.extract_tables()
                                if tables:
                                    for table in tables:
                                        for row in table:
                                            cells = [c if c else "" for c in row]
                                            deep_text += "\n" + " | ".join(cells)
                                            
                                receipt_info = parse_receipt(deep_text)

                                matched_line = ""
                                for line in deep_text.split("\n"):
                                    if re.search(pattern, line, re.IGNORECASE):
                                        matched_line = line.strip()
                                        break
                                        
                                result = {
                                    "page": page_num,
                                    "total_pages": total_pages,
                                    "matched_line": matched_line,
                                    "page_text": deep_text,
                                    "receipt": receipt_info,
                                    "file_id": file_id,
                                    "file_name": file_name
                                }
                                yield json.dumps({"success": True, "result": result}) + "\n"
                    except Exception as e:
                        print(f"Erro na pág {page_num}: {e}")
                        continue
        except Exception as e:
            print(f"Error in {file_name}: {e}")
            yield json.dumps({"success": False, "error": str(e)}) + "\n"

    return Response(generate(), mimetype='application/x-ndjson')







@app.route("/api/refresh-cache", methods=["POST"])
def api_refresh_cache():
    """Limpa o cache do sistema inteiro."""
    global pdf_cache
    pdf_cache = {}
    return jsonify({"success": True, "message": "Cache do sistema limpo com sucesso!"})


# ─── DOWNLOAD ───

@app.route("/api/download-page")
def api_download_page():
    file_id = request.args.get("file_id")
    page = request.args.get("page", type=int)
    filename = request.args.get("filename", "comprovante.pdf")
    if not file_id or not page:
        return jsonify({"error": "Parâmetros faltando"}), 400
    try:
        pdf_bytes = get_pdf(file_id)
        page_pdf = extract_pdf_page(pdf_bytes, page)
        return send_file(
            page_pdf, mimetype="application/pdf",
            as_attachment=True, download_name=filename,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/view-page")
def api_view_page():
    file_id = request.args.get("file_id")
    page = request.args.get("page", type=int)
    if not file_id or not page:
        return jsonify({"error": "Parâmetros faltando"}), 400
    try:
        pdf_bytes = get_pdf(file_id)
        page_pdf = extract_pdf_page(pdf_bytes, page)
        return send_file(
            page_pdf, mimetype="application/pdf", as_attachment=False,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# MAIN

if __name__ == "__main__":
    print("-" * 50)
    print("Server running at: http://localhost:5000")
    print("-" * 50 + "\n")
    app.run(debug=True, port=5000)