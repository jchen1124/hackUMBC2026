def categorize_query(query) -> str:
    query = query.lower().strip()

    pdf_keywords = ['pdf', 'document', 'file']
    summarize_keywords = ['summarize', 'summary', 'summarization']

    found = []
    if any(word in query for word in summarize_keywords):
        found.append('summarize')
    if any(word in query for word in pdf_keywords):
        found.append('pdf')

    return ','.join(found) if found else 'message'
