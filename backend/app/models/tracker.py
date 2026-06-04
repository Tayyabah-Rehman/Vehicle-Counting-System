import numpy as np
from scipy.optimize import linear_sum_assignment
from ..config import config


class Track:
    def __init__(self, track_id, detection):
        self.track_id = track_id
        self.class_id = detection["class_id"]
        self.class_name = detection["class_name"]
        self.bbox = detection["bbox"]
        self.center = detection["center"]
        self.age = 0
        self.hits = 1
        self.time_since_update = 0

    def predict(self):
        self.age += 1
        self.time_since_update += 1

    def update(self, detection):
        self.bbox = detection["bbox"]
        self.center = detection["center"]
        self.hits += 1
        self.time_since_update = 0
        self.age = 0


class SORTTracker:
    def __init__(self):
        self.max_age = config.MAX_AGE
        self.min_hits = config.MIN_HITS
        self.iou_threshold = config.TRACKING_IOU
        self.tracks = []
        self.next_id = 1

    def iou(self, box1, box2):
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])

        intersection = max(0, x2 - x1) * max(0, y2 - y1)

        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - intersection

        if union <= 0:
            return 0.0

        return intersection / union

    def get_boxes(self, tracks_or_detections, is_track=True):
        boxes = []
        for item in tracks_or_detections:
            if is_track:
                boxes.append(item.bbox)
            else:
                boxes.append(item["bbox"])
        return np.array(boxes) if boxes else np.empty((0, 4))

    def update(self, detections):
        if not detections:
            for track in self.tracks:
                track.predict()

            self.tracks = [t for t in self.tracks if t.time_since_update < self.max_age]
            return []

        # Convert tracks to boxes for matching
        track_boxes = self.get_boxes(self.tracks, is_track=True)
        det_boxes = self.get_boxes(detections, is_track=False)

        matched_tracks = []

        if len(self.tracks) == 0:
            # No existing tracks, create new ones
            for det in detections:
                new_track = Track(self.next_id, det)
                self.tracks.append(new_track)
                matched_tracks.append(new_track)
                self.next_id += 1
            return matched_tracks

        # Calculate IoU matrix
        iou_matrix = np.zeros((len(self.tracks), len(detections)))
        for i, track in enumerate(self.tracks):
            for j, det in enumerate(detections):
                iou_matrix[i, j] = self.iou(track.bbox, det["bbox"])

        # Hungarian algorithm for optimal assignment
        row_indices, col_indices = linear_sum_assignment(-iou_matrix)

        unmatched_tracks = list(range(len(self.tracks)))
        unmatched_detections = list(range(len(detections)))

        # Match tracks to detections
        for i, j in zip(row_indices, col_indices):
            if iou_matrix[i, j] > self.iou_threshold:
                # Update existing track
                self.tracks[i].update(detections[j])
                matched_tracks.append(self.tracks[i])
                if i in unmatched_tracks:
                    unmatched_tracks.remove(i)
                if j in unmatched_detections:
                    unmatched_detections.remove(j)

        # Handle unmatched tracks (predict forward)
        for i in unmatched_tracks:
            self.tracks[i].predict()
            if self.tracks[i].time_since_update < self.max_age:
                matched_tracks.append(self.tracks[i])

        # Handle unmatched detections (create new tracks)
        for j in unmatched_detections:
            new_track = Track(self.next_id, detections[j])
            self.tracks.append(new_track)
            matched_tracks.append(new_track)
            self.next_id += 1

        # Remove old tracks
        self.tracks = [t for t in self.tracks if t.time_since_update < self.max_age]

        # Return only tracks with enough hits
        result = [t for t in matched_tracks if t.hits >= self.min_hits]

        return result