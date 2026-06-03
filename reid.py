import torch
import torchvision.transforms as T
from torchvision.models import resnet50, ResNet50_Weights
import numpy as np
import cv2

class FeatureExtractor:
    def __init__(self, device: str = None):
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        # Load pre-trained ResNet50 for feature extraction (Re-ID)
        weights = ResNet50_Weights.DEFAULT
        self.model = resnet50(weights=weights)
        # Remove the final classification layer to get embeddings
        self.model = torch.nn.Sequential(*(list(self.model.children())[:-1]))
        self.model = self.model.to(self.device)
        self.model.eval()
        
        self.transform = T.Compose([
            T.ToPILImage(),
            T.Resize((256, 128)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def extract(self, image_crop: np.ndarray) -> np.ndarray:
        """
        Extract feature embeddings from a person crop.
        """
        if image_crop is None or image_crop.size == 0:
            return np.zeros(2048)
            
        try:
            # Convert BGR to RGB
            rgb_crop = cv2.cvtColor(image_crop, cv2.COLOR_BGR2RGB)
            input_tensor = self.transform(rgb_crop).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                features = self.model(input_tensor)
                
            features = features.squeeze().cpu().numpy()
            # Normalize embedding
            norm = np.linalg.norm(features)
            if norm > 0:
                features = features / norm
            return features
        except Exception as e:
            print(f"Error extracting features: {e}")
            return np.zeros(2048)

def compute_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
    """
    Compute cosine similarity between two embeddings.
    """
    return np.dot(emb1, emb2)
