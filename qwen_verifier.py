import os
import subprocess
import tempfile
import time
import cv2
import numpy as np

LLAMA_CLI = r"C:\llama.cpp\llama-mtmd-cli.exe"
MODEL = "bartowski/Qwen2-VL-2B-Instruct-GGUF:Q4_K_M"
UPLOAD_DIR = "uploads"
VERIFY_TIMEOUT = 400

PROMPT = "أنت خبير أمني. افحص اللقطات الثلاث لشخص. أجب بسطر واحد فقط: النتيجة: [مشبوه أو طبيعي] - السبب: [جملة قصيرة]"


class QwenVerifier:
    def __init__(self):
        print(f"[Qwen] CLI: {LLAMA_CLI}")
        if not os.path.exists(LLAMA_CLI):
            raise FileNotFoundError(f"llama-mtmd-cli.exe not found at {LLAMA_CLI}")

    def _extract_3_frames_montage(self, event, out_path):
        video_source = event.get("video_source") or ""
        video_path = os.path.join(UPLOAD_DIR, os.path.basename(video_source))
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {video_path}")

        target_frame = int(event.get("frame") or 0)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        offset = int(fps * 0.5)

        bbox = event.get("bbox") or []
        if not bbox or len(bbox) != 4:
            raise ValueError("Invalid bbox")

        x1, y1, x2, y2 = [float(v) for v in bbox]
        pad_x = (x2 - x1) * 0.02
        pad_y = (y2 - y1) * 0.02

        crops = []
        for frame_idx in [target_frame - offset, target_frame, target_frame + offset]:
            frame_idx = max(0, frame_idx)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                continue
            h, w = frame.shape[:2]
            fx1 = max(0, int(x1 - pad_x))
            fy1 = max(0, int(y1 - pad_y))
            fx2 = min(w, int(x2 + pad_x))
            fy2 = min(h, int(y2 + pad_y))
            if fx2 <= fx1 or fy2 <= fy1:
                continue
            crop = frame[fy1:fy2, fx1:fx2]
            crops.append(crop)

        cap.release()

        if not crops:
            raise RuntimeError("No valid crops extracted")

        target_h = 336
        resized = []
        for c in crops:
            h_c, w_c = c.shape[:2]
            scale = target_h / h_c
            new_w = int(w_c * scale)
            resized.append(cv2.resize(c, (new_w, target_h), interpolation=cv2.INTER_AREA))

        total_w = sum(r.shape[1] for r in resized) + 20 * (len(resized) - 1)
        montage = np.full((target_h, total_w, 3), 255, dtype=np.uint8)
        x_offset = 0
        for r in resized:
            montage[:, x_offset:x_offset + r.shape[1]] = r
            x_offset += r.shape[1] + 20

        cv2.imwrite(out_path, montage)

    def verify_event(self, event):
        print(f"[Qwen] Verifying event {event.get('id')} (track {event.get('track_id')})...")
        start = time.time()

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False, dir=os.getcwd()) as tmp:
            tmp_path = tmp.name

        try:
            self._extract_3_frames_montage(event, tmp_path)
            print(f"[Qwen] Montage saved: {tmp_path}")

            cmd = [
                LLAMA_CLI,
                "-hf", MODEL,
                "--image", tmp_path,
                "--image-min-tokens", "768",
                "-p", PROMPT,
                "-n", "200",
                "--temp", "0.3",
            ]
            print(f"[Qwen] Running with simplified prompt...")

            result = subprocess.run(
                cmd, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=VERIFY_TIMEOUT,
            )

            with open("qwen_debug.log", "w", encoding="utf-8") as f:
                f.write("=== STDOUT ===\n")
                f.write(result.stdout or "")
                f.write("\n\n=== STDERR ===\n")
                f.write(result.stderr or "")

            answer = self._parse_output(result.stdout or "")
            elapsed = time.time() - start
            print(f"[Qwen] Done in {elapsed:.1f}s. Answer: {answer[:300]}")
            return answer if answer else "لم يتم الحصول على إجابة."

        except subprocess.TimeoutExpired:
            return f"انتهت المهلة ({VERIFY_TIMEOUT} ثانية)."
        except Exception as e:
            return f"خطأ: {str(e)}"
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    def _parse_output(self, output):
        markers = ["assistant\n", "assistant\r\n", "assistant "]
        text = output
        for m in markers:
            if m in text:
                text = text.rsplit(m, 1)[-1]
                break

        lines = []
        for line in text.splitlines():
            s = line.strip()
            if not s:
                continue
            if s.startswith(("llama_", "main:", "encoding", "image ", "decoding", "load_", "clip_", "common_", "mtmd_", "print_info")):
                continue
            lines.append(s)

        result = ""
        for line in lines:
            if "النتيجة" in line or "نتيجة" in line:
                result = line
                break

        if not result:
            result = " ".join(lines).strip()

        for end_marker in ["[end of text]", "<|im_end|>", "<|endoftext|>"]:
            result = result.replace(end_marker, "")

        return result.strip()[:1000]

_verifier = None

def get_verifier():
    global _verifier
    if _verifier is None:
        _verifier = QwenVerifier()
    return _verifier
