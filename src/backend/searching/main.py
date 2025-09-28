from .category import categorize_query
from .find_pdf import load_pdf, find_pdf

def main(query: str) -> dict | None:
    """
    Returns a dict with:
      - 'filename': just the PDF name
      - 'full_path': full path to the PDF
    """
    category = categorize_query(query)

    if category == 'pdf':
        pdf_list = load_pdf()  # returns list of dicts with filename & full_path
        result = find_pdf(query, pdf_list)  # returns the matching dict
        if result:
            return {
                "filename": result["filename"],
                "full_path": result["full_path"]
            }
        else:
            return None
    elif category == 'message':
        return None
