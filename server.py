"""
Backend Flask — Local PDF Search & Data Extraction.
"""

from flask import Flask, render_template, request, jsonify, send_file, Response
import os
import io
import re
import json
import pdfplumber
from PyPDF2 import PdfReader, PdfWriter
from dotenv import load_dotenv

load_dotenv()

# CONFIGURATION
BASE_DIR = os.getenv("LOCAL_PATH", os.getcwd())
PDF_MIME_TYPE = "application/pdf"
TEMP_PAGES_DIR = "temp_pages"

os.makedirs(TEMP_PAGES_DIR, exist_ok=True)

app = Flask(__name__)

# Cache de PDFs processados (apenas para evitar re-leitura pesada em sessões curtas)
pdf_cache = {}


# LOCAL FILE UTILS

def get_pdf(file_path):
    """Lê bytes do PDF local e retorna."""
    if file_path not in pdf_cache:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, "rb") as f:
            pdf_cache[file_path] = io.BytesIO(f.read())
            
    pdf_cache[file_path].seek(0)
    return pdf_cache[file_path]


# SEARCH LOGIC

def find_pdfs_by_day_month(day, month):
    """
    Searches for PDFs recursively in the local directory.
    """
    dd = str(day).zfill(2)
    mm = str(month).zfill(2)

    date_patterns = [
        f"{dd}-{mm}",
        f"{dd}/{mm}",
        f"{dd}.{mm}",
        f"{dd}_{mm}",
        f"{dd} {mm}",
        f"{dd}{mm}",
    ]

    matched = []
    
    # Busca recursiva no diretório local
    for root, _, files in os.walk(BASE_DIR):
        for file in files:
            if file.lower().endswith(".pdf"):
                name_upper = file.upper()
                for pattern in date_patterns:
                    if pattern in name_upper:
                        full_path = os.path.join(root, file)
                        matched.append({
                            "id": full_path,  # Usamos o path absoluto como ID
                            "name": file,
                            "path": full_path
                        })
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
    
    pdf_copy = io.BytesIO(pdf_bytes_original.getvalue())
    pdf_copy2 = io.BytesIO(pdf_bytes_original.getvalue())

    reader = PdfReader(pdf_copy)
    total_pages = len(reader.pages)
    
    pages_with_code = []
    for page_num, page in enumerate(reader.pages, 1):
        try:
            text = page.extract_text() or ""
            if re.search(pattern, text, re.IGNORECASE):
                pages_with_code.append(page_num)
        except Exception:
            pages_with_code.append(page_num)

    if not pages_with_code:
        return []

    with pdfplumber.open(pdf_copy2) as pdf:
        for page_num in pages_with_code:
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
    exists = os.path.exists(BASE_DIR)
    return jsonify({
        "connected": exists,
        "path": BASE_DIR,
        "mode": "local",
        "error": None if exists else f"Path not found: {BASE_DIR}"
    })


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
                "error": f"No PDF found containing {dd}-{mm} in the name folder: {BASE_DIR}",
            })

        return jsonify({
            "success": True,
            "total_files": len(matched),
            "files": matched,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/search-single-pdf", methods=["POST"])
def api_search_single_pdf():
    """Buscador unitário local (STREAMING NDJSON)."""
    data = request.get_json()
    code = data.get("code", "").strip()
    file_id = data.get("file_id", "").strip() # file_id is the ABSOLUTE PATH
    file_name = data.get("file_name", "").strip()

    if not code:
        return jsonify({"success": False, "error": "Código obrigatório"})
    if not file_id:
        return jsonify({"success": False, "error": "Path do arquivo ausente"})

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
                        print(f"Error on pág {page_num}: {e}")
                        continue
        except Exception as e:
            print(f"Error in {file_name}: {e}")
            yield json.dumps({"success": False, "error": str(e)}) + "\n"

    return Response(generate(), mimetype='application/x-ndjson')


@app.route("/api/refresh-cache", methods=["POST"])
def api_refresh_cache():
    global pdf_cache
    pdf_cache = {}
    return jsonify({"success": True, "message": "System cache cleared!"})


# ─── DOWNLOAD & VIEW ───

@app.route("/api/download-page")
def api_download_page():
    file_id = request.args.get("file_id") # Absolute path
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
    file_id = request.args.get("file_id") # Absolute path
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
    print("PDF Search & Extraction (LOCAL MODE) running at: http://localhost:5000")
    print(f"Monitoring Directory: {BASE_DIR}")
    print("-" * 50 + "\n")
    app.run(debug=True, port=5000)