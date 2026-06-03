import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Dict, Any

class PersonDetector:
    def __init__(self, model_path: str = "yolov8n.pt", conf_threshold: float = 0.5):
        """
        Initialize the YOLOv8 detector for person detection.
        Using yolov8n.pt by default for real-time performance.
        """
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold
        # COCO class 0 is 'person'
        self.person_class_id = 0

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Run detection on a single frame.
        """
        results = self.model(frame, classes=[self.person_class_id], conf=self.conf_threshold, verbose=False)
        
        detections = []
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = box.conf[0].cpu().item()
                
                detections.append({
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    "confidence": float(conf),
                    "class_id": self.person_class_id
                })
        return detections
