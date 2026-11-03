import numpy as np
from ultralytics import YOLO
from collections import defaultdict


class ConcealmentDetector:
    """
    Detects concealment behavior using YOLOv8-Pose keypoints.
    Based on geometric features: wrist-to-hip, wrist-to-nose distances.
    """

    def __init__(self, model_path="yolov8n-pose.pt", distance_threshold=50, angle_threshold=45):
        self.model = YOLO(model_path)
        self.distance_threshold = distance_threshold
        self.angle_threshold = angle_threshold

        self.history = defaultdict(list)
        self.history_size = 5

    def _calculate_distance(self, p1, p2):
        return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    def _calculate_angle(self, p1, p2, p3):
        v1 = np.array([p1[0] - p2[0], p1[1] - p2[1]])
        v2 = np.array([p3[0] - p2[0], p3[1] - p2[1]])
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
        return np.degrees(np.arccos(np.clip(cos_angle, -1, 1)))

    def analyze_frame(self, frame, tracked_boxes):
        results = self.model(frame, verbose=False)[0]
        keypoints_data = results.keypoints

        if keypoints_data is None or len(keypoints_data) == 0:
            return {}

        detections = {}
        for kp_set, box in zip(keypoints_data.xy, results.boxes.xyxy):
            bx1, by1, bx2, by2 = box.tolist()
            center = ((bx1 + bx2) / 2, (by1 + by2) / 2)

            best_track = None
            best_dist = float('inf')
            for tb in tracked_boxes:
                tx1, ty1, tx2, ty2 = tb['bbox']
                t_center = ((tx1 + tx2) / 2, (ty1 + ty2) / 2)
                d = self._calculate_distance(center, t_center)
                if d < best_dist:
                    best_dist = d
                    best_track = tb['track_id']

            if best_track is None or best_dist > 100:
                continue

            try:
                kps = kp_set.cpu().numpy()
                if len(kps) < 13:
                    continue

                nose = kps[0]
                l_wrist = kps[9]
                r_wrist = kps[10]
                l_hip = kps[11]
                r_hip = kps[12]

                d_l_hip = self._calculate_distance(l_wrist, l_hip)
                d_r_hip = self._calculate_distance(r_wrist, r_hip)
                min_hip_dist = min(d_l_hip, d_r_hip)

                d_l_nose = self._calculate_distance(l_wrist, nose)
                d_r_nose = self._calculate_distance(r_wrist, nose)
                min_nose_dist = min(d_l_nose, d_r_nose)

                score = 0.0
                reasons = []

                if min_hip_dist < self.distance_threshold:
                    score += 0.6
                    reasons.append(f"Wrist near hip ({min_hip_dist:.0f}px)")

                if min_nose_dist < self.distance_threshold * 0.8:
                    score += 0.3
                    reasons.append(f"Wrist near nose ({min_nose_dist:.0f}px)")

                self.history[best_track].append(score)
                if len(self.history[best_track]) > self.history_size:
                    self.history[best_track].pop(0)
                smoothed_score = np.mean(self.history[best_track])

                is_suspicious = smoothed_score > 0.5

                detections[best_track] = {
                    'is_suspicious': is_suspicious,
                    'reason': ' + '.join(reasons) if reasons else 'Normal',
                    'score': float(smoothed_score),
                    'features': {
                        'wrist_hip_dist': float(min_hip_dist),
                        'wrist_nose_dist': float(min_nose_dist)
                    }
                }
            except Exception as e:
                print(f"[Concealment] Error processing keypoints: {e}")
                continue

        return detections

    def reset(self):
        self.history.clear()