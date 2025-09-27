from rapidfuzz import process


#load in pdf
def load_pdf() -> list[str]:
    with open("pdf_files.txt", "r") as txt_file:
        pdf_list = [line.strip() for line in txt_file.readlines()]
    return pdf_list


#find pdf
def find_pdf(query: str, pdf_list: list[str]) -> str | None:
    """Find the best matching PDF filename."""
    match = process.extractOne(query, pdf_list)
    if match and match[1] > 50:  # match[1] is similarity score
        return match[0]
    return None





