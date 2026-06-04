import cv2
import numpy as np
from ultralytics import YOLO
from ..config import config


class VehicleDetector:
    def __init__(self):
        print("Loading YOLO model from:", config.MODEL_PATH)
        self.model = YOLO(config.MODEL_PATH)

        if config.USE_GPU:
            self.model.to(config.DEVICE)
            print("Using GPU for detection")
        else:
            print("Using CPU for detection")

        self.confidence_threshold = config.CONFIDENCE_THRESHOLD
        self.vehicle_classes = config.VEHICLE_CLASSES
        self.vehicle_names = config.VEHICLE_NAMES

    def detect(self, frame):
        results = self.model(frame, verbose=False, conf=self.confidence_threshold)[0]
        detections = []

        if results.boxes is not None:
            for box in results.boxes:
                class_id = int(box.cls[0])

                if class_id not in self.vehicle_classes:
                    continue

                confidence = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2

                detection = {
                    "class_id": class_id,
                    "class_name": self.vehicle_names[class_id],
                    "confidence": confidence,
                    "bbox": [x1, y1, x2, y2],
                    "center": (center_x, center_y)
                }
                detections.append(detection)

        return detections