# backend/model.py
import torch
import torch.nn as nn
import os

class SimpleFashionNet(nn.Module):
    def __init__(self, num_classes=10):
        super().__init__()
        # Using resnet18 backbone for demo; replace with your actual model
        self.backbone = torch.hub.load('pytorch/vision:v0.13.1', 'resnet18', pretrained=False)
        self.backbone.fc = nn.Linear(self.backbone.fc.in_features, num_classes)

    def forward(self, x):
        return self.backbone(x)

def load_model(path="model.pt", device=None, num_classes=10):
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = SimpleFashionNet(num_classes=num_classes).to(device)
    if os.path.exists(path):
        state = torch.load(path, map_location=device)
        model.load_state_dict(state)
    else:
        print(f"[warning] model file {path} not found. Using randomly initialized model.")
    model.eval()
    return model, device
