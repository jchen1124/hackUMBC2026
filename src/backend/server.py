import datetime
import os
import shutil
from flask import Flask, request, jsonify, url_for, send_from_directory
from flask_cors import CORS

# --- Import your custom logic modules ---
from summarize.summarize import main as get_conversation_summary
from find_pdf.find_pdf import load_pdf, find_pdf
from search_message.findmessage import search_imessages

# --- INITIALIZE THE FLASK APP AND CONFIGURATION ---
app = Flask(__name__)
# Allow requests from your React app's origin
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

# Define the folder where found PDFs will be copied to be served publicly.
# This path is relative to the project root.
UPLOAD_FOLDER = os.path.join('src', 'backend', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Ensure the upload folder exists.
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


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
    return ','.join(found) if found else 'message'


# --- NEW ENDPOINT TO SERVE THE COPIED FILES ---
@app.route('/uploads/<path:filename>')
def serve_file(filename):
    """
    This endpoint serves files from the UPLOAD_FOLDER, making them accessible to the frontend.
    """
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# --- MAIN API ENDPOINT ---
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
        content = get_conversation_summary()
        return jsonify({
            'content': content,
            'is_summarize': True,
            'is_message': False,
            'timestamp': datetime.datetime.now().isoformat()
        })

    elif 'pdf' in intent:
        print("Routing to PDF search and file serving...")
        all_pdfs = load_pdf()
        found_pdf_info = find_pdf(user_message, all_pdfs)
        
        if found_pdf_info:
            filename = found_pdf_info.get('filename')
            # The full_path from the DB (e.g., '~/Library/...') needs the ~ expanded.
            original_path = os.path.expanduser(found_pdf_info.get('full_path'))
            destination_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            try:
                # Copy the file to the public 'uploads' folder if it's not already there.
                if not os.path.exists(destination_path):
                    shutil.copy2(original_path, destination_path)
                
                # Generate a public URL for the copied file.
                file_url = url_for('serve_file', filename=filename, _external=True)
                
                return jsonify({
                    "content": f"I found the file you asked for: {filename}",
                    "file_url": file_url,
                    "file_name": filename,
                    "file_type": "pdf",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "is_message": False,
                    "is_pdf": True
                })
            except FileNotFoundError:
                return jsonify({
                    "content": f"I located the PDF file '{filename}' in the database, but couldn't access it on your computer at the path: {original_path}",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "is_message": True
                })
        else:
            return jsonify({
                "content": "Sorry, I couldn't find a PDF matching that description.",
                "timestamp": datetime.datetime.now().isoformat(),
                "is_message": True
            })

    else:  # Default case for 'message' intent
        print("Routing to semantic message search...")
        content = search_imessages(query=user_message, top_k=5)
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

