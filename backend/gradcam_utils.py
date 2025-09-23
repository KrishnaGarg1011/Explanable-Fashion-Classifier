# backend/gradcam_utils.py
import numpy as np
import torch
from torchvision import transforms
from PIL import Image
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image

# transforms to match model's training transforms
INP_TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

def preprocess_pil(pil_img):
    img = pil_img.convert("RGB")
    t = INP_TRANSFORM(img)
    return t.unsqueeze(0)  # [1,C,H,W]

def make_gradcam_overlay(model, target_layer, pil_img, device, target_category=None):
    img = np.array(pil_img.resize((224,224))).astype(np.float32) / 255.0
    input_tensor = preprocess_pil(pil_img).to(device)
    cam = GradCAM(model=model, target_layers=[target_layer], use_cuda=(device.type=="cuda"))
    # target_category can be None => highest scoring class
    grayscale_cam = cam(input_tensor=input_tensor, targets=None)[0]  # HxW
    visualization = show_cam_on_image(img, grayscale_cam, use_rgb=True)
    # return as PIL image
    return Image.fromarray(visualization)
