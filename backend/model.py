# backend/model.py
import torch
import torch.nn as nn

# Example model architecture (adjust to your trained model)
class FashionNet(nn.Module):
    def __init__(self, num_classes=10):
        super(FashionNet, self).__init__()
        self.model = torch.hub.load("pytorch/vision", "resnet18", pretrained=False)
        self.model.fc = nn.Linear(self.model.fc.in_features, num_classes)

    def forward(self, x):
        return self.model(x)

# Load trained model
def load_model(path="model/model.pt", device=None, num_classes=10):
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = FashionNet(num_classes=num_classes).to(device)
    model.load_state_dict(torch.load(path, map_location=device))
    model.eval()
    return model, device
