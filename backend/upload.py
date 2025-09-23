from flask import Flask, request, jsonify
import os
import sqlite3
from datetime import datetime
from PIL import Image

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
DB_PATH = "database.db"

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            uploaded_at TEXT,
            label TEXT,
            confidence REAL,
            explanation TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Upload route
@app.route("/upload", methods=["POST"])
def upload_file():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    # Save file
    file.save(filepath)

    # Optional: call your trained model to predict
    # For demo, we’ll insert dummy values
    label = "T-shirt"  # Replace with your model prediction
    confidence = 0.95  # Replace with your model confidence
    explanation = "High confidence because of texture and shape"  # Replace with your explanation

    # Insert into DB
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO images (filename, uploaded_at, label, confidence, explanation)
        VALUES (?, ?, ?, ?, ?)
    ''', (filename, datetime.utcnow().isoformat(), label, confidence, explanation))
    conn.commit()
    conn.close()

    return jsonify({"message": "Image uploaded and stored", "filename": filename})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
