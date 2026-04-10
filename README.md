# 📄 ComprovanteFinder — PDF Search & Data Extraction

A high-performance Flask application designed for automated searching and data extraction from PDF receipts stored in Google Drive. 

## Overview

ComprovanteFinder streamlines the process of locating specific financial documents within large, nested directories in Google Drive. It leverages the Google Drive API for efficient file discovery and specialized Python libraries for granular text extraction and pattern matching within PDF pages.

## Key Features

- **Granular PDF Search**: Recursive scanning of Google Drive folders to find PDFs based on naming conventions (dia/mês).
- **Intense Data Extraction**: Automatically extracts critical receipt information including:
  - Beneficiary Name
  - CPF/CNPJ
  - Payment Value
  - Transaction Date
  - Authentication Codes
- **Deep Content Indexing**: Fast multi-stage search strategy using `PyPDF2` for rapid filtering and `pdfplumber` for precise data extraction.
- **On-Demand PDF Rendering**: Download and view individual pages from multi-page PDF documents.
- **Smart Caching**: In-memory PDF caching to minimize API latency and redundant downloads.
- **Modern Responsive UI**: Premium slate/indigo interface for desktop and mobile efficiency.

## Technical Architecture

- **Backend**: Python / Flask
- **Integration**: Google Drive API v3 (OAuth 2.0)
- **PDF Engine**:
  - `pdfplumber`: Robust table and text extraction.
  - `PyPDF2`: High-speed text indexing and page slicing.
- **Frontend**: Vanilla HTML5/CSS3 with modern design principles (CSS Variables, Flexbox/Grid, Inter Typography).

## Configuration

### Prerequisites

1. **Google Cloud Project**: Set up a project in the [Google Cloud Console](https://console.cloud.google.com/).
2. **Drive API**: Enable the Google Drive API.
3. **Credentials**: Download the `credentials.json` Oauth2 Client ID file and place it in the root directory.
4. **Environment**: Create a `.env` file with your `FOLDER_ID` (the root directory where the app should start searching).

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your FOLDER_ID
```

## Usage

### Execution

**Windows:**
```bash
iniciar.bat
```

**Linux/macOS:**
```bash
./iniciar.sh
```

**Manual:**
```bash
python server.py
```

Access the dashboard at: `http://localhost:5000`

---
*Developed for efficient financial document management and automated reconciliation workflows.*
