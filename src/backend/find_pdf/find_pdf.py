from rapidfuzz import process
import os
import sqlite3
import logging
import datetime

# Add logging to help debug issues
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def load_pdf() -> list[dict]:
    """
    Load all PDFs from iMessage database.
    Returns a list of dicts: {'filename': ..., 'full_path': ...}
    """
    db_path = os.path.expanduser("out/chat.db")
    
    # Check if database exists
    if not os.path.exists(db_path):
        logger.error(f"Database not found at: {db_path}")
        return []
    
    try:
        conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
        cursor = conn.cursor()
        
        query = "SELECT attachment.filename FROM attachment WHERE attachment.filename LIKE '%.pdf';"
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        logger.info(f"Found {len(rows)} PDF records in database")
        
        pdfs = []
        for row in rows:
            if row[0]:  # Check if filename is not None
                filename = os.path.basename(row[0])
                full_path = os.path.expanduser(row[0])  # Expand ~ here
                
                # Log each PDF found for debugging
                logger.debug(f"Found PDF: {filename} at {full_path}")
                
                pdfs.append({
                    "filename": filename, 
                    "full_path": full_path
                })
        
        logger.info(f"Processed {len(pdfs)} valid PDFs")
        return pdfs
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error loading PDFs: {e}")
        return []

def find_pdf(query: str, pdf_list: list[dict]) -> dict | None:
    """
    Fuzzy match query against PDF filenames.
    Returns a dict with both 'filename' and 'full_path'.
    """
    if not pdf_list:
        logger.warning("No PDFs available to search")
        return None
    
    if not query or not query.strip():
        logger.warning("Empty search query")
        return None
    
    # Clean the query to remove instruction words for better matching
    query_clean = query.lower().strip()
    
    # Remove common instruction words
    instruction_words = ['find', 'get', 'search for', 'search', 'pdf', 'show me', 'open', 'the', 'file']
    for word in instruction_words:
        query_clean = query_clean.replace(word, '')
    
    # Clean up extra spaces and special characters
    query_clean = ' '.join(query_clean.split())  # Remove extra whitespace
    
    if not query_clean:
        logger.warning("Query became empty after cleaning")
        return None
    
    logger.debug(f"Original query: '{query}' -> Cleaned query: '{query_clean}'")

    # Create a list of filenames (without extension) for better matching
    pdf_names_for_matching = []
    for pdf in pdf_list:
        # Remove .pdf extension and convert to lowercase for matching
        name_without_ext = os.path.splitext(pdf["filename"])[0].lower()
        pdf_names_for_matching.append(name_without_ext)
    
    logger.debug(f"PDF names for matching: {pdf_names_for_matching}")

    # Use rapidfuzz to find the best match with a confidence score
    match = process.extractOne(query_clean, pdf_names_for_matching)
    
    logger.debug(f"Best match: {match}")
    
    # Lower the threshold to 40 for more flexible matching
    if match and match[1] > 40:
        matched_name = match[0]
        confidence = match[1]
        
        # Find the original PDF dictionary using the matched name
        for pdf in pdf_list:
            pdf_name_without_ext = os.path.splitext(pdf["filename"])[0].lower()
            if pdf_name_without_ext == matched_name:
                logger.info(f"Found match: {pdf['filename']} (confidence: {confidence}%)")
                return pdf
    
    logger.warning(f"No suitable match found for query: '{query_clean}'")
    return None


# Enhanced Flask route with better error handling
def handle_pdf_search(user_message, app):
    """
    Enhanced PDF search handler with better error handling and logging
    """
    try:
        logger.info(f"Starting PDF search for: '{user_message}'")
        
        all_pdfs = load_pdf()
        logger.info(f"Loaded {len(all_pdfs)} PDFs from database")
        
        if not all_pdfs:
            return {
                "error": "No PDFs found in the database",
                "content": "I couldn't find any PDF files in your message history.",
                "timestamp": datetime.datetime.now().isoformat()
            }
        
        found_pdf_info = find_pdf(user_message, all_pdfs)
        
        if found_pdf_info:
            filename = found_pdf_info.get('filename')
            full_path = found_pdf_info.get('full_path')
            
            logger.info(f"Found PDF: {filename} at {full_path}")
            
            if filename and full_path:
                # Check if source file exists
                if not os.path.exists(full_path):
                    logger.error(f"Source file does not exist: {full_path}")
                    return {
                        "error": "File not found",
                        "content": f"The file {filename} was found in the database but the actual file doesn't exist at {full_path}",
                        "timestamp": datetime.datetime.now().isoformat()
                    }
                
                try:
                    # Ensure upload folder exists
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    
                    destination = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    shutil.copy2(full_path, destination)
                    
                    file_url = url_for('serve_file', filename=filename, _external=True)
                    
                    logger.info(f"Successfully copied and served file: {filename}")
                    
                    return {
                        "content": f"I found the file: {filename}",
                        "file_url": file_url,
                        "file_name": filename,
                        "file_type": "pdf",
                        "is_pdf": True,
                        "timestamp": datetime.datetime.now().isoformat()
                    }
                    
                except Exception as e:
                    logger.error(f"Error copying file: {e}")
                    return {
                        "error": "File copy error",
                        "content": f"Found the file {filename} but couldn't copy it: {str(e)}",
                        "timestamp": datetime.datetime.now().isoformat()
                    }
            else:
                logger.error("PDF info missing filename or full_path")
                return {
                    "error": "Invalid PDF data",
                    "content": "Found a PDF but the file information is incomplete",
                    "timestamp": datetime.datetime.now().isoformat()
                }
        else:
            logger.info("No matching PDF found")
            return {
                "content": f"I couldn't find a PDF matching '{user_message}'. Available PDFs: {[pdf['filename'] for pdf in all_pdfs[:5]]}{'...' if len(all_pdfs) > 5 else ''}",
                "timestamp": datetime.datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Unexpected error in PDF search: {e}")
        return {
            "error": "Search error",
            "content": f"An error occurred while searching for PDFs: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }