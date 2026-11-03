import cv2
import numpy as np
import os
from collections import defaultdict, deque
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
import time
from typing import Dict, List, Tuple

from geo_mapper import GeoMapper
from concealment_detector import ConcealmentDetector
from visitor_detector import VisitorDetector


class ShopliftingDetector:
    def __init__(self, video_source=0):
        self.model = YOLO("yolov8n.pt")
        self.tracker = DeepSort(max_age=50)
        self.cap = cv2.VideoCapture(video_source)
        self.loitering_threshold = 3
        self.concealment_distance = 50
        self.track_history: Dict[int, List[Tuple[int, int]]] = defaultdict(list)
        self.track_start_times: Dict[int, float] = {}
        self.suspicious_tracks: Dict[int, str] = {}
        self.total_detections = 0
        self.suspicious_activities = 0
        self.model_version = "1.0.0"
        self.geo_mapper = GeoMapper(cam_lat=36.7538, cam_lon=3.0588, cam_heading=0.0, cam_fov=60.0, cam_height=3.0)
        self.concealment_detector = ConcealmentDetector()
        self.visitor_detector = VisitorDetector()
        self.visitor_cache = {}
        self.known_visitor_ids = set()

    def _create_writer(self, path, fps, size):
        try:
            import imageio_ffmpeg
            writer = imageio_ffmpeg.write_frames(
                path, size=size, fps=fps, codec='libx264',
                pix_fmt_in='bgr24', pix_fmt_out='yuv420p',
                macro_block_size=1,
            )
            writer.send(None)
            return writer, 'imageio'
        except Exception:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(path, fourcc, fps, size)
            return writer, 'cv2'

    def _write_frame(self, writer, kind, frame):
        if kind == 'imageio':
            writer.send(frame.tobytes())
        else:
            writer.write(frame)

    def _close_writer(self, writer, kind):
        if kind == 'imageio':
            writer.close()
        else:
            writer.release()

    def calculate_bbox_center(self, bbox):
        x1, y1, x2, y2 = bbox
        return (int((x1 + x2) / 2), int((y1 + y2) / 2))

    def detect_loitering(self, track_id, current_time):
        if track_id in self.track_start_times:
            if (current_time - self.track_start_times[track_id]) > self.loitering_threshold:
                return True
        return False

    def process_frame(self, frame, frame_number=0):
        results = self.model(frame)[0]
        detections = []
        for r in results.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = r
            if score > 0.3:
                detections.append(([x1, y1, x2, y2], score, int(class_id)))
        tracks = self.tracker.update_tracks(detections, frame=frame)
        current_time = time.time()
        frame_detections = []

        for track in tracks:
            if not track.is_confirmed():
                continue
            track_id = track.track_id
            bbox = track.to_tlbr()
            if track_id not in self.track_start_times:
                self.track_start_times[track_id] = current_time
            center = self.calculate_bbox_center(bbox)
            self.track_history[track_id].append(center)
            self.total_detections += 1
            is_suspicious = False
            reason = None
            if self.detect_loitering(track_id, current_time):
                self.suspicious_tracks[track_id] = "Loitering"
                is_suspicious = True
                reason = "Loitering"
            if is_suspicious:
                self.suspicious_activities += 1
            frame_detections.append({
                "track_id": int(track_id),
                "bbox": [float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])],
                "center": [int(center[0]), int(center[1])],
                "is_suspicious": is_suspicious,
                "reason": reason,
                "frame": frame_number,
                "visitor_id": None,
                "is_recurring": False,
            })
            color = (0, 0, 255) if is_suspicious else (0, 255, 0)
            cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), color, 2)
            label = f"ID: {track_id}"
            if is_suspicious:
                label += f" ({self.suspicious_tracks[track_id]})"
            cv2.putText(frame, label, (int(bbox[0]), int(bbox[1] - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            if len(self.track_history[track_id]) > 2:
                points = np.array(self.track_history[track_id], dtype=np.int32)
                cv2.polylines(frame, [points], False, color, 2)

        tracked_boxes = [{'track_id': det['track_id'], 'bbox': det['bbox']} for det in frame_detections]
        concealment_results = self.concealment_detector.analyze_frame(frame, tracked_boxes)
        for det in frame_detections:
            tid = det['track_id']
            if tid in concealment_results:
                c_res = concealment_results[tid]
                if c_res['is_suspicious']:
                    det['is_suspicious'] = True
                    det['reason'] = (det['reason'] + ' + ' if det['reason'] else '') + 'Concealment'
                    det['concealment_score'] = c_res['score']
                    det['concealment_features'] = c_res['features']

        for det in frame_detections:
            tid = det['track_id']
            if tid not in self.visitor_cache:
                vid, is_recurring = self.visitor_detector.identify(
                    frame, det['bbox'], known_ids=self.known_visitor_ids
                )
                self.visitor_cache[tid] = (vid, is_recurring)
                if is_recurring:
                    print(f"[Visitors] Recurring visitor! track={tid} visitor_id={vid}")
            det['visitor_id'], det['is_recurring'] = self.visitor_cache[tid]
            if det['is_recurring']:
                det['is_suspicious'] = True
                det['reason'] = (det['reason'] + ' + ' if det['reason'] else '') + 'Recurring'

        return frame, frame_detections

    def process_video(self, video_path):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {"error": f"Could not open video: {video_path}"}
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        frame_number = 0
        all_detections = []
        suspicious_events = []
        self.total_detections = 0
        self.suspicious_activities = 0
        self.track_history.clear()
        self.track_start_times.clear()
        self.suspicious_tracks.clear()
        self.concealment_detector.reset()
        self.visitor_cache.clear()
        self.known_visitor_ids = self.visitor_detector.get_existing_visitor_ids()

        clip_dir = "clips"
        os.makedirs(clip_dir, exist_ok=True)
        CLIP_WIDTH, CLIP_HEIGHT = 640, 360
        effective_fps = max(1.0, fps / 3.0)
        pre_frames_count = int(effective_fps * 3)
        post_frames_count = int(effective_fps * 3)
        frame_buffer = deque(maxlen=max(1, pre_frames_count))
        active_clips = {}
        clip_paths_final = {}
        video_name = os.path.splitext(os.path.basename(video_path))[0]

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            small_frame = cv2.resize(frame, (CLIP_WIDTH, CLIP_HEIGHT))
            frame_buffer.append(small_frame.copy())
            if frame_number % 3 == 0:
                _, frame_detections = self.process_frame(frame, frame_number)
                frame_h, frame_w = frame.shape[:2]
                valid = [d for d in frame_detections if 0 <= d["center"][0] <= frame_w and 0 <= d["center"][1] <= frame_h]
                all_detections.extend(valid)

                for det in valid:
                    if det["is_suspicious"]:
                        gps = self.geo_mapper.pixel_to_gps(center=det["center"], bbox=det["bbox"], frame_width=frame_w)
                        suspicious_events.append({
                            "timestamp": round(frame_number / fps, 2),
                            "track_id": det["track_id"],
                            "center": det["center"],
                            "bbox": det["bbox"],
                            "reason": det["reason"],
                            "frame": frame_number,
                            "gps": gps,
                            "concealment_score": det.get("concealment_score"),
                            "concealment_features": det.get("concealment_features"),
                            "visitor_id": det.get("visitor_id"),
                            "is_recurring": det.get("is_recurring", False),
                            "clip_path": None,
                        })
                        tid = det["track_id"]
                        if tid not in active_clips and tid not in clip_paths_final:
                            clip_name = f"{video_name}_track{tid}_frame{frame_number}.mp4"
                            clip_path = os.path.join(clip_dir, clip_name)
                            writer, kind = self._create_writer(clip_path, effective_fps, (CLIP_WIDTH, CLIP_HEIGHT))
                            for f in list(frame_buffer)[:-1]:
                                self._write_frame(writer, kind, f)
                            active_clips[tid] = {'writer': writer, 'kind': kind, 'frames_left': post_frames_count, 'path': clip_path}
                            print(f"[Clips] Started for track {tid}: {clip_path}")

                for tid, clip in list(active_clips.items()):
                    self._write_frame(clip['writer'], clip['kind'], small_frame)
                    clip['frames_left'] -= 1
                    if clip['frames_left'] <= 0:
                        self._close_writer(clip['writer'], clip['kind'])
                        clip_paths_final[tid] = clip['path']
                        size = os.path.getsize(clip['path']) if os.path.exists(clip['path']) else 0
                        print(f"[Clips] Finished track {tid}: {clip['path']} ({size} bytes)")
                        del active_clips[tid]
            frame_number += 1
        cap.release()
        for tid, clip in list(active_clips.items()):
            self._close_writer(clip['writer'], clip['kind'])
            clip_paths_final[tid] = clip['path']
            del active_clips[tid]
        for ev in suspicious_events:
            tid = ev['track_id']
            if tid in clip_paths_final:
                ev['clip_path'] = clip_paths_final[tid]
        print(f"[Clips] Total clips: {len(clip_paths_final)} | Events: {len(suspicious_events)}")
        return {
            "video": video_path,
            "total_frames": frame_number,
            "fps": fps,
            "total_detections": self.total_detections,
            "suspicious_activities": len(suspicious_events),
            "suspicious_events": suspicious_events[:100],
            "detections_sample": all_detections[:500],
            "model_version": self.model_version,
            "clips_created": len(clip_paths_final),
        }

    def train(self, video_path, annotations_path):
        return {"status": "not_implemented", "video": video_path, "annotations": annotations_path}

    def run(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            processed_frame, _ = self.process_frame(frame)
            cv2.imshow("Shoplifting Detection", processed_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        self.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    detector = ShopliftingDetector(0)
    detector.run()
