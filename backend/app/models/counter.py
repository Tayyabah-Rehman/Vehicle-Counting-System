from ..config import config


class VehicleCounter:
    def __init__(self, frame_height):
        self.frame_height = frame_height
        self.line_y = int(frame_height * config.COUNTING_LINE_POSITION)
        self.crossed_ids = set()
        self.total_count = 0
        self.vehicle_counts = {
            "car": 0,
            "motorcycle": 0,
            "bus": 0,
            "truck": 0
        }

    def update(self, track):
        if track.track_id in self.crossed_ids:
            return False, None

        center_y = track.center[1]

        if center_y > self.line_y:
            self.crossed_ids.add(track.track_id)
            self.total_count += 1

            class_name = track.class_name
            if class_name in self.vehicle_counts:
                self.vehicle_counts[class_name] += 1

            return True, track

        return False, None

    def get_stats(self):
        return {
            "total_count": self.total_count,
            "vehicle_breakdown": self.vehicle_counts.copy(),
            "line_position": self.line_y,
            "frame_height": self.frame_height
        }

    def reset(self):
        self.crossed_ids.clear()
        self.total_count = 0
        for key in self.vehicle_counts:
            self.vehicle_counts[key] = 0