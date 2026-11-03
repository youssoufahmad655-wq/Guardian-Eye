import math


class GeoMapper:
    """
    Converts pixel coordinates from a camera frame to GPS coordinates (lat, lon).
    """

    def __init__(
        self,
        cam_lat,
        cam_lon,
        cam_heading=0.0,
        cam_fov=60.0,
        cam_height=3.0,
        person_real_height=1.7,
        assumed_distance=5.0,
    ):
        self.cam_lat = float(cam_lat)
        self.cam_lon = float(cam_lon)
        self.cam_heading = float(cam_heading) % 360
        self.cam_fov = float(cam_fov)
        self.cam_height = float(cam_height)
        self.person_real_height = float(person_real_height)
        self.assumed_distance = float(assumed_distance)

    def _estimate_distance(self, bbox, frame_width):
        x1, y1, x2, y2 = bbox
        bbox_height_px = abs(y2 - y1)
        if bbox_height_px < 10:
            return self.assumed_distance

        focal_px = (frame_width / 2.0) / math.tan(math.radians(self.cam_fov / 2.0))
        distance = (self.person_real_height * focal_px) / bbox_height_px
        return max(1.0, min(distance, 50.0))

    def pixel_to_gps(self, center, bbox, frame_width):
        cx, cy = center
        offset_ratio = (cx - frame_width / 2.0) / frame_width
        angle_offset = offset_ratio * self.cam_fov
        absolute_angle = (self.cam_heading + angle_offset) % 360

        distance_m = self._estimate_distance(bbox, frame_width)

        dlat = (distance_m * math.cos(math.radians(absolute_angle))) / 111320.0
        dlon = (
            distance_m * math.sin(math.radians(absolute_angle))
        ) / (111320.0 * math.cos(math.radians(self.cam_lat)))

        return {
            "latitude": round(self.cam_lat + dlat, 6),
            "longitude": round(self.cam_lon + dlon, 6),
            "distance_m": round(distance_m, 2),
            "angle_deg": round(absolute_angle, 2),
        }