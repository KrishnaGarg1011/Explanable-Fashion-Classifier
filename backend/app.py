# backend/app.py
import os
from flask import Flask, request, jsonify, send_from_directory, redirect
from PIL import Image
import sqlite3
import io
import base64
from datetime import datetime

from model import load_model
from gradcam_utils import preprocess_pil, make_gradcam_overlay

from torchvision import transforms
import torch
import torch.nn.functional as F

UPLOAD_FOLDER = "uploads"
DB_PATH = "database.db"
MODEL_PATH = "model.pt"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# load model
model, device = load_model(path=MODEL_PATH, device=None, num_classes=10)
# for Grad-CAM we need a target layer - adapt if model architecture differs
target_layer = model.backbone.layer4[-1]

app = Flask(__name__, static_url_path='', static_folder='../frontend')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize DB
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

# helper to save image bytes to disk
def save_image(file_storage, prefix="img"):
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    filename = f"{prefix}_{ts}.png"
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    img = Image.open(file_storage.stream).convert("RGB")
    img.save(path)
    return filename, path, img

# route: frontend files
@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/gallery')
def gallery():
    return app.send_static_file('gallery.html')

# API: upload image (inserts into DB and returns stored file name)
@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return jsonify({"error": "No image file"}), 400
    file = request.files['image']
    filename, filepath, pil_img = save_image(file, prefix="uploaded")
    # simple DB insert (no prediction yet)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO images (filename, uploaded_at) VALUES (?, ?)",
              (filename, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({"filename": filename})

# API: predict + explain for a stored or newly uploaded image
@app.route('/predict', methods=['POST'])
def predict():
    # accept either an uploaded file or filename
    if 'image' in request.files:
        file = request.files['image']
        filename, filepath, pil_img = save_image(file, prefix="predict")
    else:
        payload = request.get_json() or {}
        filename = payload.get("filename")
        if not filename:
            return jsonify({"error": "Provide 'image' file or JSON {'filename':...}"}), 400
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({"error": "file not found"}), 404
        pil_img = Image.open(filepath).convert("RGB")

    # preprocess & forward
    transform = transforms.Compose([
        transforms.Resize((224,224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])
    ])
    x = transform(pil_img).unsqueeze(0).to(device)
    with torch.no_grad():
        logits = model(x)
        probs = F.softmax(logits, dim=1)
        conf, pred_idx = torch.max(probs, dim=1)
        pred_idx = int(pred_idx.item())
        conf_val = float(conf.item())

    # textual explanation (simple template; replace with your text-generator)
    explanation = f"Model predicts class {pred_idx} with confidence {conf_val:.3f}."

    # Grad-CAM overlay
    try:
        cam_img = make_gradcam_overlay(model=model, target_layer=target_layer, pil_img=pil_img, device=device, target_category=pred_idx)
        cam_filename = f"cam_{filename}"
        cam_path = os.path.join(app.config['UPLOAD_FOLDER'], cam_filename)
        cam_img.save(cam_path)
    except Exception as e:
        print("Grad-CAM generation failed:", e)
        cam_filename = None

    # Save prediction to DB
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE images SET label=?, confidence=?, explanation=? WHERE filename=?", (str(pred_idx), conf_val, explanation, filename))
    if c.rowcount == 0:
        # if row doesn't exist, insert
        c.execute("INSERT INTO images (filename, uploaded_at, label, confidence, explanation) VALUES (?, ?, ?, ?, ?)",
                  (filename, datetime.utcnow().isoformat(), str(pred_idx), conf_val, explanation))
    conn.commit()
    conn.close()

    response = {"label": pred_idx, "confidence": conf_val, "explanation": explanation, "filename": filename}
    if cam_filename:
        response["cam_url"] = f"/uploads/{cam_filename}"
    response["image_url"] = f"/uploads/{filename}"
    return jsonify(response)

# static upload file serving
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# API: list gallery images
@app.route('/api/gallery', methods=['GET'])
def api_gallery():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, filename, uploaded_at, label, confidence, explanation FROM images ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    items = []
    for r in rows:
        items.append({
            "id": r[0],
            "filename": r[1],
            "uploaded_at": r[2],
            "label": r[3],
            "confidence": r[4],
            "explanation": r[5],
            "image_url": f"/uploads/{r[1]}",
            "cam_url": f"/uploads/cam_{r[1]}"
        })
    return jsonify(items)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
