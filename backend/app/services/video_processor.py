import cv2
import time
import os
import subprocess
import threading
from ..config import config
from ..models.detector import VehicleDetector
from ..models.tracker import SORTTracker
from ..models.counter import VehicleCounter


class VideoProcessor:
    def __init__(self, video_path, output_path=None):
        self.video_path = video_path
        self.output_path = output_path
        self.detector = VehicleDetector()
        self.tracker = None
        self.counter = None
        self.fps_history = []

    def process(self, progress_callback=None):
        print(f"Opening video: {self.video_path}")
        cap = cv2.VideoCapture(self.video_path)

        if not cap.isOpened():
            raise Exception(f"Cannot open video file: {self.video_path}")

        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        input_fps = cap.get(cv2.CAP_PROP_FPS)

        print(f"Video info: {frame_width}x{frame_height}, {total_frames} frames, {input_fps} fps")

        if input_fps <= 0:
            input_fps = 30

        self.tracker = SORTTracker()
        self.counter = VehicleCounter(frame_height)

        out = None
        temp_avi_path = None

        if self.output_path:
            temp_avi_path = self.output_path.replace('.mp4', '_temp.avi')
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter(
                temp_avi_path,
                fourcc,
                input_fps,
                (frame_width, frame_height)
            )
            print(f"Writing temp AVI to: {temp_avi_path}")

        frame_index = 0
        last_progress = -1
        last_callback_time = time.time()

        while True:
            ret, frame = cap.read()
            if not ret:
                print(f"End of video reached. Total frames processed: {frame_index}")
                break

            if frame_index % config.SKIP_FRAMES != 0:
                frame_index += 1
                continue

            start_time = time.time()

            detections = self.detector.detect(frame)
            tracks = self.tracker.update(detections)

            for track in tracks:
                counted, vehicle = self.counter.update(track)
                self.draw_track(frame, track, counted)

            self.draw_counting_line(frame)
            self.draw_stats(frame, self.counter.get_stats())

            process_time = time.time() - start_time
            fps = 1.0 / process_time if process_time > 0 else 0
            self.fps_history.append(fps)
            self.draw_fps(frame, fps)

            if out is not None:
                out.write(frame)

            frame_index += 1

            if progress_callback:
                progress = int((frame_index / total_frames) * 100)
                current_time = time.time()

                if progress != last_progress or (current_time - last_callback_time) >= 1.0:
                    print(f"Progress: {progress}%, FPS: {fps:.1f}, Count: {self.counter.total_count}")
                    last_progress = progress
                    last_callback_time = current_time
                    try:
                        progress_callback(progress, fps, self.counter.total_count)
                    except Exception as e:
                        print(f"Callback error: {e}")

        cap.release()
        if out is not None:
            out.release()

        avg_fps = 0
        if self.fps_history:
            avg_fps = sum(self.fps_history) / len(self.fps_history)

        # Prepare result (ready immediately)
        result = {
            "total_count": self.counter.total_count,
            "vehicle_breakdown": self.counter.vehicle_counts,
            "average_fps": round(avg_fps, 2),
            "total_frames_processed": frame_index,
            "video_path": self.output_path,
            "conversion_status": "pending"
        }

        # Start conversion in background (does not block results)
        if temp_avi_path and os.path.exists(temp_avi_path):
            print(f"Starting background conversion to H.264 MP4...")
            threading.Thread(
                target=self._convert_to_h264_background,
                args=(temp_avi_path, self.output_path),
                daemon=True
            ).start()
            result["conversion_status"] = "converting_in_background"
        else:
            result["conversion_status"] = "no_conversion_needed"

        print(f"Processing complete. Total count: {self.counter.total_count}")
        print(f"Results ready. Video conversion continues in background.")

        if progress_callback:
            try:
                progress_callback(100, avg_fps, self.counter.total_count)
            except Exception as e:
                print(f"Final callback error: {e}")

        return result

    def _convert_to_h264_background(self, input_path: str, output_path: str):
        """Run FFmpeg conversion in background thread"""
        try:
            ffmpeg_path = r"C:\Users\Sunny\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe"

            result = subprocess.run(
                [
                    ffmpeg_path,
                    '-y',
                    '-i', input_path,
                    '-vcodec', 'libx264',
                    '-crf', '23',
                    '-preset', 'fast',
                    '-pix_fmt', 'yuv420p',
                    '-movflags', '+faststart',
                    '-acodec', 'copy',
                    output_path
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=300
            )

            if result.returncode == 0:
                print(f"Background H.264 conversion successful: {output_path}")
                # Mark conversion complete (you can add status tracking if needed)
            else:
                error_msg = result.stderr.decode('utf-8', errors='ignore')
                print(f"Background conversion failed: {error_msg}")

            # Remove temp file
            try:
                os.remove(input_path)
                print(f"Removed temp file: {input_path}")
            except Exception as e:
                print(f"Could not remove temp file: {e}")

        except Exception as e:
            print(f"Background conversion error: {e}")

    def draw_track(self, frame, track, counted=False):
        x1, y1, x2, y2 = track.bbox
        color = (0, 255, 0) if counted else (0, 165, 255)

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.circle(frame, track.center, 4, color, -1)

        label = f"{track.track_id}:{track.class_name}"
        if counted:
            label = f"{label} [COUNTED]"

        cv2.putText(
            frame, label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5, color, 2
        )

    def draw_counting_line(self, frame):
        line_y = self.counter.line_y
        cv2.line(frame, (0, line_y), (frame.shape[1], line_y), (255, 0, 0), 3)
        cv2.putText(
            frame, "COUNTING LINE",
            (10, line_y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6, (255, 0, 0), 2
        )

    def draw_stats(self, frame, stats):
        y_offset = 30
        cv2.putText(
            frame, f"TOTAL COUNT: {stats['total_count']}",
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7, (0, 255, 0), 2
        )

        y_offset += 30
        cv2.putText(
            frame, "Breakdown:",
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6, (255, 255, 255), 2
        )

        y_offset += 25
        for vehicle, count in stats['vehicle_breakdown'].items():
            cv2.putText(
                frame, f"  {vehicle}: {count}",
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (255, 255, 255), 1
            )
            y_offset += 22

    def draw_fps(self, frame, fps):
        cv2.putText(
            frame, f"FPS: {int(fps)}",
            (frame.shape[1] - 120, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7, (0, 255, 255), 2
        )