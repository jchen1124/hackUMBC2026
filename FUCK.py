# server.py
from flask import Flask, request, jsonify, send_file, url_for
from datetime import datetime
from flask_cors import CORS
import os
import shutil
from searching.main import main # Import your main() function from searching/main.py
from searching.category import categorize_query
from searching.findmessage import search_imessages
from summarize.summarize2 import main as summarize_main

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000"]}})


# Directory to store files to serve
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route("/api/ai-response", methods=["POST"])
def ai_response():
    print("Received request at /api/recent-contacts")
    print("Request headers:", request.headers)
    print("Query parameters:", request.args)
    data = request.json
    user_message = data.get("message", "")
    
    try:
        check_category = categorize_query(user_message)
        
        if check_category == 'message':
            message = search_imessages(user_message)
            return jsonify({
                "content": message,  # Return the actual message, not category
                "timestamp": datetime.utcnow().isoformat(),
                "is_message": True
            })
            
        elif check_category == 'pdf':
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
            else:
                return jsonify({
                    "content": "No PDF file found for your query.",
                    "timestamp": datetime.utcnow().isoformat(),
                    "is_message": True
                })
                
        elif check_category == 'summarize':
            # Call summarize_main() without arguments - it doesn't need any
            message = summarize_main()
            return jsonify({
                "content": message,  # Return the actual summary, not category
                "timestamp": datetime.utcnow().isoformat(),
                "is_summarize": True
            })
            
        else:
            # Default case - call main function with the user message
            message = main(user_message)
            return jsonify({
                "content": message,  # Return the actual response, not category
                "timestamp": datetime.utcnow().isoformat(),
                "is_message": True
            })
            
    except Exception as e:
        # Return proper error response instead of fake PDF
        error_message = f"Sorry, I encountered an error while processing your request: {str(e)}"
        print("Backend error:", e)
        return jsonify({
            "content": error_message,
            "timestamp": datetime.utcnow().isoformat(),
            "is_message": True,
            "error": True
        }), 500

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
@app.route("/api/recent-contacts", methods=["GET"])
def get_recent_contacts():
    """Get recent contacts from iMessages"""
    try:
        from searching.findmessage import get_recent_conversations
        
        # Optional query params
        limit = request.args.get("limit", default=20, type=int)
        search_filter = request.args.get("filter", default="", type=str).lower()
        
        recent_contacts = get_recent_conversations()
        
        # Apply filter if provided
        if search_filter:
            recent_contacts = [
                convo for convo in recent_contacts
                if search_filter in (convo["contact"] or "").lower()
                or search_filter in (convo["last_message"] or "").lower()
            ]
        
        # Apply limit
        recent_contacts = recent_contacts[:limit]
        
        return jsonify({
            "contacts": recent_contacts,
            "count": len(recent_contacts),
            "timestamp": datetime.utcnow().isoformat(),
            "success": True
        })
        
    except Exception as e:
        print("Error fetching recent contacts:", e)
        return jsonify({
            "contacts": [],
            "error": str(e),
            "success": False
        }), 500

if __name__ == "__main__":
    app.run(debug=True)