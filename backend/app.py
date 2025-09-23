from flask import Flask, request, jsonify
import os
from database import insert_image  # import our database helper
from model import load_model       # your trained model loader
from torchvision import transforms
from PIL import Image
import torch

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load trained model
model, device = load_model("model/model.pt")

# Image transforms
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

@app.route("/upload", methods=["POST"])
def upload():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    filename = file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # Run model prediction
    img = Image.open(filepath).convert("RGB")
    x = transform(img).unsqueeze(0).to(device)
    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1)
        pred_idx = int(probs.argmax().item())
        confidence = float(probs[0][pred_idx].item())

    explanation = f"Predicted class {pred_idx} with confidence {confidence:.2f}"

    # Insert into database
    insert_image(filename, str(pred_idx), confidence, explanation)

    return jsonify({
        "message": "Image uploaded and stored in database",
        "filename": filename,
        "label": pred_idx,
        "confidence": confidence,
        "explanation": explanation
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
