# server.py
from flask import Flask, request, jsonify, send_file, url_for
from datetime import datetime
from flask_cors import CORS
import os
import shutil
from searching.main import main  # Import your main() function from searching/main.py
import shutil
from searching.category import categorize_query
from searching.findmessage import search_imessages
app = Flask(__name__)
CORS(app)  # Enable CORS

# Directory to store files to serve
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route("/api/ai-response", methods=["POST"])
def ai_response():
    data = request.json
    user_message = data.get("message", "")

    try:
        # Call your main function (returns either text or file path)

        message = main(user_message)
        check_category = categorize_query(user_message)
        if check_category == 'message':
            message = search_imessages(user_message)
            return jsonify({
                "content": message,
                "timestamp": datetime.utcnow().isoformat(),
                "is_message": True
            })
        if check_category == 'pdf':
            result = main(user_message)
            if result:
                filename = result['filename']
                full_path = os.path.expanduser(result['full_path'])
                destination = os.path.join(UPLOAD_FOLDER, filename)
                if not os.path.exists(destination):
                    shutil.copy2(full_path, destination)

                file_url = url_for('serve_file', filename=filename, _external=True)

                return jsonify({
                    "content": f"I found a file: {filename}",
                    "file_url": file_url,
                    "file_name": filename,
                    "file_type": "pdf",
                    "timestamp": datetime.utcnow().isoformat(),
                    "is_message": False
                })


            
        


        

    except Exception as e:
        # Catch any backend errors
        error_message = f"Error in backend: {str(e)}"
        print("Backend error:", e)
    return jsonify({
    "content": "I found a fileA: notecard biol.pdf",
    "file_url": "http://127.0.0.1:5000/uploads/notecard%20biol.pdf",
    "file_name": "notecard biol.pdf",
    "file_type": "pdf",
    "timestamp": "2025-09-27T20:30:00"
    }
    )

@app.route("/uploads/<filename>")
def serve_file(filename):
    """Serve files from the uploads folder"""
    try:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(file_path):
            return send_file(file_path)
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
