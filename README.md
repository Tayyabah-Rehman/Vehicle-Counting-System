# 🚗 Vehicle Counting System

Real-time vehicle detection, classification, and per-lane counting system using **YOLOv8 + SORT tracking** with GPU acceleration. Upload any traffic video and get instant vehicle counts by type and lane.

---

## 📹 Demo

### Watch the Demo Video
👉 [Click here to watch the demo on Kaggle]([PASTE YOUR KAGGLE DEMO VIDEO LINK HERE])

### Download Demo Dataset (Input + Output Videos)
📦 [Click here to download the demo dataset on Kaggle]([PASTE YOUR KAGGLE DATASET LINK HERE])

The Kaggle dataset includes:
- Sample input traffic video
- Processed output video with bounding boxes and lane lines
- Per-lane counting demonstration

---

## ✨ Features

- 🛣️ **Automatic lane detection** — detects 1–6 lanes automatically, no manual config needed
- 🎯 **Real-time vehicle detection** using YOLOv8
- 🔄 **Multi-object tracking** with SORT algorithm (unique ID per vehicle)
- 🚌 **Vehicle classification** — Cars, Two-Wheelers, Buses, Trucks
- ↕️ **Directional counting** — counts vehicles moving in each direction
- 📊 **Per-lane statistics** — separate count for every lane
- 🌐 **Web interface** — upload video, view live progress, download processed output
- ⚡ **GPU acceleration** — 50+ FPS on NVIDIA GPU with CUDA

---

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| Python 3.10 | Backend language |
| YOLOv8 | Vehicle detection |
| SORT | Multi-object tracking |
| FastAPI | Web framework & REST API |
| OpenCV | Video processing |
| PyTorch | Deep learning backend |
| FFmpeg | Video encoding |

---

## 🚀 Installation

### Prerequisites

- Python 3.10+
- NVIDIA GPU with CUDA 12.4 *(recommended — CPU also works, slower)*
- FFmpeg installed and added to PATH

### Setup Steps

**1. Clone the repository**
```bash
git clone https://github.com/Tayyabah-Rehman/vehicle-counting-system.git
cd vehicle-counting-system
```

**2. Create and activate virtual environment**
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac / Linux
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Run the application**
```bash
python run.py
```

**5. Open your browser and go to:**
```
http://localhost:8000
```

---

## 📖 Usage

1. Click **"Upload"** and select a traffic video (MP4, AVI, MOV, MKV)
2. Click **"Process Video"**
3. Watch real-time processing progress
4. View results:
   - Total vehicle count
   - Per-lane breakdown
   - Vehicle type breakdown (Cars, Two-Wheelers, Buses, Trucks)
5. **Download** or watch the processed output video

---

## ⚙️ How It Works

```
Upload Video → YOLO Detection → SORT Tracking → Lane Detection → Counting → Results
```

1. **YOLOv8** detects vehicles in every frame
2. **SORT algorithm** tracks vehicles across frames and assigns unique IDs
3. **Lane detector** automatically identifies road lanes from video geometry
4. **Counter** increments when a tracked vehicle crosses a lane boundary line
5. **Results** display counts per lane, per direction, and per vehicle type

---

## 📁 Project Structure

```
vehicle-counting-system/
├── backend/
│   ├── app/
│   │   ├── models/          # YOLO, SORT, Counter classes
│   │   ├── services/        # Video processor service
│   │   ├── api/             # FastAPI route handlers
│   │   ├── utils/           # Lane detector utilities
│   │   └── config.py        # Configuration settings
├── frontend/
│   └── public/              # HTML, CSS, JavaScript
├── data/                    # Uploads & processed videos (git ignored)
├── run.py                   # Application entry point
├── requirements.txt         # Python dependencies
└── README.md
```

---

## 📊 Example Output

After processing a video you will see:

```
TOTAL VEHICLES: 127

Cars:          98
Two-Wheelers:  29
Buses:          0
Trucks:         0
```

---

## 💻 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 8 GB | 16 GB |
| GPU | GTX 1060 | RTX 3060+ |
| Storage | 5 GB | 10 GB SSD |
| OS | Windows 10/11 | Windows 10/11 |

---

## ⚠️ Known Limitations

- First-time video processing takes extra time for FFmpeg conversion
- Auto lane detection works best on roads with clear lane markings
- Very low-resolution videos may reduce detection accuracy

---

## 🔮 Future Improvements

- [ ] Support for night-time videos
- [ ] Improved lane detection for curved roads
- [ ] Real-time CCTV / IP camera feed support
- [ ] Export reports as PDF or Excel

---

## 📄 License

MIT License — free to use and modify.

---

## 👩‍💻 Author

**Tayyabah Rehman**  
GitHub: [@Tayyabah-Rehman](https://github.com/Tayyabah-Rehman)

*Built with Python, YOLOv8, and FastAPI*
