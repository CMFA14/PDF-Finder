# PDF Extraction Engine (Local Test Version)

A technical tool for searching and extracting data from PDF files stored locally. This version is designed for high-performance processing of receipts and documents using OCR-like text extraction.

## Features
- **Local Search**: Recursively scan any directory for PDFs matching specific date patterns (DD-MM).
- **Deep Extraction**: Uses `pdfplumber` and `PyPDF2` to extract text, tables, and metadata.
- **Smart Parsing**: Automatically identifies beneficiaries, values, dates, and authentication keys using regex patterns.
- **Save/Extract**: View isolated PDF pages containing matches and save them individually.

## Prerequisites
- Python 3.8+
- `pip install -r requirements.txt`

## Configuration
1. Rename `.env.example` to `.env`.
2. Set `LOCAL_PATH` to the folder containing your PDF files:
   ```env
   LOCAL_PATH=C:\Path\To\Your\PDFs
   ```

## Getting Started
1. Run the server:
   ```bash
   python server.py
   ```
   *Or use the provided `iniciar.bat` shortcut.*
2. Open `http://localhost:5000` in your browser.
3. Enter the day/month of the files you want to scan.
4. Provide a keyword (name, CNPJ, or part of a code) to start the extraction.

## Technical Details
- **Backend**: Flask (Python)
- **PDF Core**: `pdfplumber` for deep analysis, `PyPDF2` for fast indexing.
- **Frontend**: Vanilla JS with NDJSON streaming for real-time extraction updates.
