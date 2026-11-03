import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional


class EventDatabase:
    def __init__(self, db_path="events.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_source TEXT,
                    timestamp REAL,
                    track_id INTEGER,
                    center_x INTEGER,
                    center_y INTEGER,
                    bbox TEXT,
                    reason TEXT,
                    frame INTEGER,
                    gps_latitude REAL,
                    gps_longitude REAL,
                    gps_distance_m REAL,
                    gps_angle_deg REAL,
                    created_at TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_track ON events(track_id)")
            for col, ctype in [("clip_path", "TEXT"), ("visitor_id", "INTEGER"), ("is_recurring", "INTEGER")]:
                try:
                    conn.execute(f"ALTER TABLE events ADD COLUMN {col} {ctype}")
                except sqlite3.OperationalError:
                    pass
            conn.commit()
        finally:
            conn.close()

    def insert_event(self, event: Dict, video_source: str = "") -> int:
        conn = self._get_connection()
        try:
            gps = event.get("gps") or {}
            center = event.get("center") or [None, None]
            cursor = conn.execute("""
                INSERT INTO events (
                    video_source, timestamp, track_id, center_x, center_y,
                    bbox, reason, frame, gps_latitude, gps_longitude,
                    gps_distance_m, gps_angle_deg, created_at, clip_path,
                    visitor_id, is_recurring
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                video_source,
                event.get("timestamp"),
                event.get("track_id"),
                center[0],
                center[1],
                json.dumps(event.get("bbox", [])),
                event.get("reason"),
                event.get("frame"),
                gps.get("latitude"),
                gps.get("longitude"),
                gps.get("distance_m"),
                gps.get("angle_deg"),
                datetime.now().isoformat(),
                event.get("clip_path"),
                event.get("visitor_id"),
                1 if event.get("is_recurring") else 0,
            ))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def insert_events(self, events: List[Dict], video_source: str = "") -> int:
        count = 0
        for event in events:
            try:
                self.insert_event(event, video_source)
                count += 1
            except Exception as e:
                print(f"[DB] Failed to insert event: {e}")
        return count

    def get_events(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM events ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset)
            )
            return [self._row_to_dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_event(self, event_id: int) -> Optional[Dict]:
        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,))
            row = cursor.fetchone()
            return self._row_to_dict(row) if row else None
        finally:
            conn.close()

    def get_events_count(self) -> int:
        conn = self._get_connection()
        try:
            return conn.execute("SELECT COUNT(*) as count FROM events").fetchone()["count"]
        finally:
            conn.close()

    def clear_events(self):
        conn = self._get_connection()
        try:
            conn.execute("DELETE FROM events")
            conn.commit()
        finally:
            conn.close()

    def _row_to_dict(self, row) -> Dict:
        d = dict(row)
        if d.get("bbox"):
            try:
                d["bbox"] = json.loads(d["bbox"])
            except (json.JSONDecodeError, TypeError):
                pass
        return d