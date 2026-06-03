import cv2
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Any
from app.cv.tracker import MultiObjectTracker
from app.cv.reid import FeatureExtractor
from app.cv.zone_manager import ZoneManager
from app.services.session import SessionManager
from app.schemas.event import StoreEvent, EventType, CameraType

class CameraPipeline:
    def __init__(self, camera_id: str, camera_type: CameraType):
        self.camera_id = camera_id
        self.camera_type = camera_type
        
        self.tracker = MultiObjectTracker(conf_threshold=0.4)
        self.extractor = FeatureExtractor()
        self.zone_manager = ZoneManager()
        
        # Local mapping of track_id to crop/embedding (for passing to session manager)
        self.last_embeddings = {}

    def setup_zones(self, zones_config: Dict[str, List[Tuple[int, int]]]):
        """
        Configure zones for this camera.
        zones_config: {"entry_zone": [(x,y), ...], "billing_queue": [...]}
        """
        for name, points in zones_config.items():
            self.zone_manager.add_zone(name, points)

    def process_frame(self, frame: np.ndarray, timestamp: datetime, session_manager: SessionManager) -> List[StoreEvent]:
        """
        Process a single frame from the camera, generating StoreEvents.
        """
        events: List[StoreEvent] = []
        
        # 1. Track objects
        tracked_objects = self.tracker.track(frame)
        
        for obj in tracked_objects:
            track_id = obj["track_id"]
            bbox = obj["bbox"]
            center = obj["center"]
            conf = obj["confidence"]
            
            # 2. Extract features if we don't have a recent one or occasionally
            if track_id not in self.last_embeddings:
                x1, y1, x2, y2 = bbox
                # Ensure valid crop
                h, w = frame.shape[:2]
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                crop = frame[y1:y2, x1:x2]
                
                emb = self.extractor.extract(crop)
                self.last_embeddings[track_id] = emb
            else:
                emb = self.last_embeddings[track_id]
                
            # 3. Session Management (Re-ID)
            session, is_new = session_manager.match_or_create(self.camera_id, track_id, emb, timestamp)
            
            # Re-entry detection
            if not is_new and not session.in_store and self.camera_type == CameraType.ENTRY_CAMERA:
                session.in_store = True
                events.append(StoreEvent(
                    visitor_id=session.visitor_id,
                    event_type=EventType.REENTRY,
                    timestamp=timestamp,
                    camera_id=self.camera_id,
                    camera_type=self.camera_type,
                    confidence=conf,
                    metadata={"is_staff": session.is_staff}
                ))

            if is_new and self.camera_type == CameraType.ENTRY_CAMERA:
                events.append(StoreEvent(
                    visitor_id=session.visitor_id,
                    event_type=EventType.ENTRY,
                    timestamp=timestamp,
                    camera_id=self.camera_id,
                    camera_type=self.camera_type,
                    confidence=conf,
                    metadata={"is_staff": session.is_staff}
                ))
            elif is_new and self.camera_type != CameraType.ENTRY_CAMERA:
                # Person appeared first time but not on entry camera -> deduplication failure or initial startup
                # We can log this internally
                pass

            # 4. Zone Updates
            zone_events = self.zone_manager.update(track_id, center, timestamp)
            
            for ze in zone_events:
                z_type = ze["type"]
                z_name = ze["zone"]
                
                # Map internal zone events to StoreEvent schema
                e_type = None
                if z_type == "ZONE_ENTER":
                    if "queue" in z_name.lower():
                        e_type = EventType.BILLING_QUEUE_JOIN
                    else:
                        e_type = EventType.ZONE_ENTER
                elif z_type == "ZONE_EXIT":
                    if "queue" in z_name.lower():
                        e_type = EventType.BILLING_QUEUE_ABANDON
                    else:
                        e_type = EventType.ZONE_EXIT
                elif z_type == "ZONE_DWELL":
                    e_type = EventType.ZONE_DWELL
                    
                if e_type:
                    events.append(StoreEvent(
                        visitor_id=session.visitor_id,
                        event_type=e_type,
                        timestamp=timestamp,
                        camera_id=self.camera_id,
                        camera_type=self.camera_type,
                        confidence=conf,
                        metadata={"zone": z_name, "dwell_time": ze.get("dwell_time", 0.0)}
                    ))
                    
                # Handle Exit Logic (Assume 'exit_zone' triggers EXIT)
                if z_type == "ZONE_ENTER" and z_name == "exit_zone":
                    session_manager.mark_exit(session.visitor_id)
                    events.append(StoreEvent(
                        visitor_id=session.visitor_id,
                        event_type=EventType.EXIT,
                        timestamp=timestamp,
                        camera_id=self.camera_id,
                        camera_type=self.camera_type,
                        confidence=conf
                    ))

        return events
