from typing import Dict, List, Tuple, Optional
from datetime import datetime
import numpy as np

class PolygonZone:
    def __init__(self, name: str, points: List[Tuple[int, int]]):
        """
        Initialize a zone with a list of (x, y) coordinates forming a polygon.
        """
        import cv2
        self.name = name
        self.points = np.array(points, dtype=np.int32)
        # Precompute bounding box for quick filtering
        self.bbox = cv2.boundingRect(self.points)

    def contains(self, point: Tuple[int, int]) -> bool:
        """
        Check if a given point is inside the zone polygon.
        """
        import cv2
        x, y = point
        # Quick bounding box check
        bx, by, bw, bh = self.bbox
        if x < bx or x > bx + bw or y < by or y > by + bh:
            return False
            
        # Precise polygon check
        dist = cv2.pointPolygonTest(self.points, (x, y), False)
        return dist >= 0

class ZoneManager:
    def __init__(self):
        self.zones: Dict[str, PolygonZone] = {}
        # Track entry/exit times per person per zone
        # track_id -> {zone_name: {"enter_time": datetime, "total_dwell": float}}
        self.state: Dict[int, Dict[str, Dict]] = {}

    def add_zone(self, name: str, points: List[Tuple[int, int]]):
        self.zones[name] = PolygonZone(name, points)

    def update(self, track_id: int, center: Tuple[int, int], timestamp: datetime) -> List[Dict]:
        """
        Update zone states for a tracked object and generate zone events.
        """
        events = []
        if track_id not in self.state:
            self.state[track_id] = {}

        person_state = self.state[track_id]

        for zone_name, zone in self.zones.items():
            in_zone = zone.contains(center)
            was_in_zone = zone_name in person_state

            if in_zone and not was_in_zone:
                # ZONE_ENTER
                person_state[zone_name] = {"enter_time": timestamp, "total_dwell": 0.0}
                events.append({
                    "type": "ZONE_ENTER",
                    "zone": zone_name,
                    "track_id": track_id,
                    "timestamp": timestamp
                })
            
            elif not in_zone and was_in_zone:
                # ZONE_EXIT
                enter_time = person_state[zone_name]["enter_time"]
                dwell_time = (timestamp - enter_time).total_seconds()
                events.append({
                    "type": "ZONE_EXIT",
                    "zone": zone_name,
                    "track_id": track_id,
                    "timestamp": timestamp,
                    "dwell_time": dwell_time
                })
                # Add ZONE_DWELL event upon exit
                events.append({
                    "type": "ZONE_DWELL",
                    "zone": zone_name,
                    "track_id": track_id,
                    "timestamp": timestamp,
                    "dwell_time": dwell_time
                })
                del person_state[zone_name]

        return events
