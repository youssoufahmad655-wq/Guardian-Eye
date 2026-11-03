import sqlite3
import numpy as np
import torch
import open_clip
from PIL import Image
from datetime import datetime


class VisitorDetector:
    """Detects recurring visitors using CLIP embeddings.
    Only flags visitors that existed BEFORE the current video session."""

    def __init__(self, db_path="visitors.db", similarity_threshold=0.85):
        self.db_path = db_path
        self.similarity_threshold = similarity_threshold
        print("[Visitors] Loading CLIP model...")
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            'ViT-B-32', pretrained='laion2b_s34b_b79k'
        )
        self.model.eval()
        print("[Visitors] CLIP model loaded.")
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS visitors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    embedding BLOB,
                    first_seen TEXT,
                    last_seen TEXT,
                    visit_count INTEGER DEFAULT 1
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def get_existing_visitor_ids(self):
        """Snapshot of visitors that existed BEFORE this video started."""
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT id FROM visitors").fetchall()
            ids = {r["id"] for r in rows}
            print(f"[Visitors] Snapshot: {len(ids)} visitor(s) from previous sessions")
            return ids
        finally:
            conn.close()

    def extract_embedding(self, frame, bbox):
        x1, y1, x2, y2 = map(int, bbox)
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x2 <= x1 or y2 <= y1:
            return None
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return None
        img = Image.fromarray(crop[:, :, ::-1])
        img_tensor = self.preprocess(img).unsqueeze(0)
        with torch.no_grad():
            emb = self.model.encode_image(img_tensor)
            emb = emb / emb.norm(dim=-1, keepdim=True)
        return emb.cpu().numpy().astype(np.float32).tobytes()

    def _cosine_similarity(self, e1_bytes, e2_bytes):
        e1 = np.frombuffer(e1_bytes, dtype=np.float32)
        e2 = np.frombuffer(e2_bytes, dtype=np.float32)
        return float(np.dot(e1, e2))

    def identify(self, frame, bbox, known_ids=None):
        """
        Identify a person. Returns (visitor_id, is_recurring).
        is_recurring is True ONLY if the visitor existed before this session
        (i.e., their ID is in known_ids).
        """
        emb = self.extract_embedding(frame, bbox)
        if emb is None:
            return None, False

        conn = self._get_connection()
        try:
            now = datetime.now().isoformat()
            best_id, best_sim = None, 0.0

            if known_ids:
                placeholders = ",".join("?" * len(known_ids))
                rows = conn.execute(
                    f"SELECT id, embedding FROM visitors WHERE id IN ({placeholders})",
                    tuple(known_ids),
                ).fetchall()
                for row in rows:
                    sim = self._cosine_similarity(emb, row["embedding"])
                    if sim > best_sim:
                        best_sim, best_id = sim, row["id"]

            if best_id is not None and best_sim >= self.similarity_threshold:
                conn.execute(
                    "UPDATE visitors SET last_seen = ?, visit_count = visit_count + 1 WHERE id = ?",
                    (now, best_id),
                )
                conn.commit()
                return best_id, True

            cur = conn.execute(
                "INSERT INTO visitors (embedding, first_seen, last_seen, visit_count) VALUES (?, ?, ?, 1)",
                (emb, now, now),
            )
            conn.commit()
            return cur.lastrowid, False
        finally:
            conn.close()