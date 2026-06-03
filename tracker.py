import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Dict, Any

class MultiObjectTracker:
    def __init__(self, model_path: str = "yolov8n.pt", tracker_type: str = "bytetrack.yaml", conf_threshold: float = 0.5):
        """
        Initialize YOLOv8 with built-in tracking (ByteTrack or BoTSORT).
        ByteTrack is preferred for performance.
        """
        self.model = YOLO(model_path)
        self.tracker_type = tracker_type
        self.conf_threshold = conf_threshold
        self.person_class_id = 0

    def track(self, frame: np.ndarray, persist: bool = True) -> List[Dict[str, Any]]:
        """
        Run tracking on a single frame.
        """
        # persist=True keeps tracking IDs across frames
        results = self.model.track(
            source=frame, 
            classes=[self.person_class_id], 
            tracker=self.tracker_type, 
            conf=self.conf_threshold, 
            persist=persist,
            verbose=False
        )
        
        tracked_objects = []
        for r in results:
            boxes = r.boxes
            # If no objects are tracked, boxes.id will be None
            if boxes.id is not None:
                track_ids = boxes.id.int().cpu().tolist()
                for box, track_id in zip(boxes, track_ids):
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = box.conf[0].cpu().item()
                    
                    tracked_objects.append({
                        "track_id": track_id,
                        "bbox": [int(x1), int(y1), int(x2), int(y2)],
                        "confidence": float(conf),
                        "center": (int((x1 + x2) / 2), int((y1 + y2) / 2))
                    })
        return tracked_objects
