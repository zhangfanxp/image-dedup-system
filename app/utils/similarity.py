import torch
from torchvision import models, transforms
from PIL import Image
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path

# ---------------------------
# 设备检查：MPS / CPU
# ---------------------------
device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")

# ---------------------------
# 模型加载
# ---------------------------
_model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
_model = torch.nn.Sequential(*(list(_model.children())[:-1]))  # 去掉最后FC层
_model.to(device)
_model.eval()

# ---------------------------
# 图片预处理
# ---------------------------
_preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])
])

# ---------------------------
# 特征提取
# ---------------------------
def extract_features(img_path: Path):
    img = Image.open(img_path).convert("RGB")
    tensor = _preprocess(img).unsqueeze(0).to(device)
    with torch.no_grad():
        feat = _model(tensor).squeeze().cpu().numpy()
    feat = feat / np.linalg.norm(feat)
    return feat

# ---------------------------
# CNN 相似度判断
# ---------------------------
def is_similar_cnn(img1_path: Path, img2_path: Path, threshold=0.85):
    """
    判断两张图片是否相似
    threshold: 相似度阈值，0~1，0.85以上认为相似
    """
    feat1 = extract_features(img1_path)
    feat2 = extract_features(img2_path)
    sim = cosine_similarity([feat1], [feat2])[0][0]
    return sim >= threshold, sim

