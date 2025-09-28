from rapidfuzz import process
import sqlite3
import os

def load_pdf() -> list[dict]:
    """
    Load all PDFs from iMessage database.
    Returns a list of dicts: {'filename': ..., 'full_path': ...}
    """
    db_path = os.path.expanduser("out/output.db")
    conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
    cursor = conn.cursor()
    
    query = "SELECT attachment.filename, attachment.filename FROM attachment WHERE attachment.filename LIKE '%.pdf';"
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    pdfs = []
    for row in rows:
        filename = os.path.basename(row[0])
        full_path = row[0]
        pdfs.append({"filename": filename, "full_path": full_path})
    return pdfs



def find_pdf(query: str, pdf_list: list[dict]) -> dict | None:
    """
    Fuzzy match query against PDF filenames.
    Returns a dict with both 'filename' and 'full_path'.
    """
    query_clean = query.lower().replace("find ", "").strip()
    filenames_lower = [pdf["filename"].lower() for pdf in pdf_list]

    match = process.extractOne(query_clean, filenames_lower)
    if match and match[1] > 50:
        index = filenames_lower.index(match[0])
        return pdf_list[index]
    return None

