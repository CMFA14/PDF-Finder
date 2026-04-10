import time
import os
import io
import re
import pdfplumber
from dotenv import load_dotenv
load_dotenv()
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from PyPDF2 import PdfReader

creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/drive.readonly', 'https://www.googleapis.com/auth/drive'])
drive_service = build('drive', 'v3', credentials=creds)

query1 = "name contains 'BRASIL' and name contains '26' and name contains '02' and name contains '2026' and mimeType='application/pdf' and trashed=false"

t0 = time.time()
results1 = drive_service.files().list(q=query1, spaces='drive', fields='files(id, name)', supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
files = results1.get('files', [])
t1 = time.time()
print(f"Query execution: {t1-t0:.2f}s, Encontrou: {len(files)}")

if files:
    f = files[0]
    print(f"Downloading {f['name']}...")
    t0 = time.time()
    req = drive_service.files().get_media(fileId=f['id'], supportsAllDrives=True)
    buf = io.BytesIO()
    dl = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        _, done = dl.next_chunk()
    buf.seek(0)
    t1 = time.time()
    print(f"Download took: {t1-t0:.2f}s, Size: {len(buf.getvalue())/1024/1024:.2f} MB")
    
    print("Testing PyPDF2 extract_text...")
    t0 = time.time()
    reader = PdfReader(buf)
    total = len(reader.pages)
    for p in reader.pages:
        text = p.extract_text()
    t1 = time.time()
    print(f"PyPDF2 pure text extraction {total} pages took: {t1-t0:.2f}s")
    
    print("Testing pdfplumber extract_text...")
    t0 = time.time()
    buf.seek(0)
    with pdfplumber.open(buf) as pdf:
        for p in pdf.pages:
            text = p.extract_text()
    t1 = time.time()
    print(f"pdfplumber pure text extraction {len(pdf.pages)} pages took: {t1-t0:.2f}s")
