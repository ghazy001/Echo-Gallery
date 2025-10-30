import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import os

# Path to model checkpoint (adjust if needed)
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artist_model.pth")

# Pick device (MPS for Apple Silicon, CUDA if GPU, else CPU)
if torch.backends.mps.is_available():
    DEVICE = torch.device("mps")
elif torch.cuda.is_available():
    DEVICE = torch.device("cuda")
else:
    DEVICE = torch.device("cpu")

# Preprocessing (must match your validation transforms!)
PREPROCESS = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225])
])

# Load model once (at import time)
print("Loading artist model...")

_checkpoint = torch.load(MODEL_PATH, map_location=DEVICE)
CLASS_NAMES = _checkpoint["class_names"]
NUM_CLASSES = len(CLASS_NAMES)

_model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
in_features = _model.fc.in_features
_model.fc = nn.Linear(in_features, NUM_CLASSES)
_model.load_state_dict(_checkpoint["model_state_dict"])
_model.to(DEVICE)
_model.eval()

print("Model ready. Classes:", CLASS_NAMES)

def predict_image(img_path):
    """
    img_path: absolute path to an image file on disk
    returns: dict with top guess and top3 guesses
    """
    img = Image.open(img_path).convert("RGB")
    tensor = PREPROCESS(img).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        outputs = _model(tensor)
        probs = torch.softmax(outputs, dim=1)[0]
        top_prob, top_idx = torch.max(probs, dim=0)

    top_artist = CLASS_NAMES[top_idx.item()]
    confidence = float(top_prob.item())

    # also make top3 list
    top3_prob, top3_idx = torch.topk(probs, k=3)
    top3 = []
    for p, idx in zip(top3_prob, top3_idx):
        top3.append({
            "artist": CLASS_NAMES[idx.item()],
            "confidence": float(p.item())
        })

    return {
        "artist": top_artist,
        "confidence": confidence,
        "top3": top3
    }
