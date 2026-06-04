import os


class Config:
    APP_NAME = "Vehicle Counting System"
    VERSION = "1.0.0"

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    UPLOAD_DIR = os.path.join(BASE_DIR, "data", "uploads")
    PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
    MODEL_PATH = os.path.join(BASE_DIR, "yolov8n.pt")

    for dir_path in [UPLOAD_DIR, PROCESSED_DIR]:
        os.makedirs(dir_path, exist_ok=True)

    YOLO_MODEL = "yolov8n.pt"

    # Lowered confidence threshold to catch smaller objects like motorcycles
    CONFIDENCE_THRESHOLD = 0.25

    # Added bicycle (class 1) because motorcycles are sometimes detected as bicycle
    VEHICLE_CLASSES = [1, 2, 3, 5, 7]
    VEHICLE_NAMES = {
        1: "bicycle",
        2: "car",
        3: "motorcycle",
        5: "bus",
        7: "truck"
    }

    MAX_AGE = 30
    MIN_HITS = 3
    TRACKING_IOU = 0.3

    COUNTING_LINE_POSITION = 0.4

    USE_GPU = True
    DEVICE = "cuda:0" if USE_GPU else "cpu"

    SKIP_FRAMES = 1
    MAX_VIDEO_SIZE = 500 * 1024 * 1024
    ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}


config = Config()