import datetime
import os
import shutil
from flask import Flask, request, jsonify, url_for, send_from_directory
from flask_cors import CORS

# --- Import your custom logic modules ---
from summarize.summarize import handle_summarize_request
from find_pdf.find_pdf import load_pdf, find_pdf
from search_message.findmessage import search_imessages

# --- INITIALIZE THE FLASK APP ---
app = Flask(__name__)
# Allow requests from your React app's origin
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

# --- CONFIGURATION ---
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# --- INTENT CLASSIFICATION UTILITY ---
def categorize_query(query: str) -> str:
    """Analyzes the user's query to determine their intent."""
    query = query.lower().strip()
    pdf_keywords = ['pdf', 'document', 'file', 'attachment']
    summarize_keywords = ['summarize', 'summary', 'tldr', 'recap']

    found = []
    if any(word in query for word in summarize_keywords):
        found.append('summarize')
    if any(word in query for word in pdf_keywords):
        found.append('pdf')

    # Default to 'message' intent if no other keywords are found
    return ','.join(found) if found else 'message'


# --- FILE SERVING ENDPOINT ---
@app.route('/files/<filename>')
def serve_file(filename):
    """Serves files from the UPLOAD_FOLDER."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# --- API ENDPOINT ---
@app.route("/api/ai-response", methods=["POST"])
def handle_ai_response():
    """
    Handles requests by categorizing the user's intent and routing to the correct logic module.
    """
    data = request.get_json()
    user_message = data.get('message')

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    print(f"Received message: '{user_message}'")
    intent = categorize_query(user_message)
    print(f"Detected intent: '{intent}'")
    
    # --- Route to the appropriate logic based on the detected intent ---
    if 'summarize' in intent:
        print("Routing to conversation summarization...")
        print(f"User message: '{user_message}'")
        
        # Use the new enhanced summarize handler
        result = handle_summarize_request(user_message, "out/output.db")
        
        # Return appropriate response based on whether there was an error
        if 'error' in result:
            return jsonify(result), 400  # Return error with 400 status
        else:
            return jsonify(result)  # Return successful summary

    elif 'pdf' in intent:
        print("Routing to PDF search...")
        all_pdfs = load_pdf()
        found_pdf_info = find_pdf(user_message, all_pdfs)
        
        print(f"Here is the pdfs{all_pdfs}")

        if found_pdf_info:
            filename = found_pdf_info.get('filename')
            full_path = found_pdf_info.get('full_path')
            
            if filename and full_path and os.path.exists(full_path):
                destination = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                shutil.copy2(full_path, destination)
                file_url = url_for('serve_file', filename=filename, _external=True)
                
                return jsonify({
                    "content": f"I found the file: {filename}",
                    "file_url": file_url,
                    "file_name": filename,
                    "file_type": "pdf",
                    "is_pdf": True,
                    "timestamp": datetime.datetime.now().isoformat()
                })
        
        return jsonify({
            "content": "Sorry, I couldn't find a PDF matching that description.",
            "is_pdf": True,
            "timestamp": datetime.datetime.now().isoformat()
        })

    else:  # Default case for 'message' intent (fuzzy search)
        print("Routing to fuzzy message search...")
        
        # Clean the query to remove common instruction words for better results
        cleaned_query = user_message.lower()
        for word in ['search for', 'search', 'find']:
            cleaned_query = cleaned_query.replace(word, '')
        cleaned_query = cleaned_query.strip()
        
        # Use the original message if cleaning results in an empty string
        final_query = cleaned_query if cleaned_query else user_message

        content = search_imessages(query=final_query, top_k=5)
        if not content:
            content = "I couldn't find any messages that matched your query."
        
        return jsonify({
            'content': content,
            'is_message': True,
            'timestamp': datetime.datetime.now().isoformat()
        })


# --- RUN THE SERVER ---
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

