import pdfplumber

with pdfplumber.open('PDT0621_10011625253_ENERO2025.pdf') as pdf:
    for i, page in enumerate(pdf.pages):
        print(f"\n--- Página {i + 1} ---")
        print(page.extract_text())
