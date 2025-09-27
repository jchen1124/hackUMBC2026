def categorize_query(query) -> str:
    query = query.lower()

    pdf_keywords = ['pdf', 'document', 'file']

    if any(word in query for word in pdf_keywords):
        return 'pdf'
    
    #elif query has "summarize"

    #else (meaning messages)