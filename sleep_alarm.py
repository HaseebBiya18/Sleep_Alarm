"""
Sleep Alarm System - by Haseeb Biya
Detects drowsiness via webcam and triggers alarm + visual alerts
"""

import cv2
import numpy as np
import time
import threading
import sys
import pygame

# ══════════════════════════════════════════════
#  SOUND SETUP
# ══════════════════════════════════════════════
pygame.mixer.init()
ALARM_SOUND = pygame.mixer.Sound("alarm.mp3")

# ══════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════
EYE_CLOSED_THRESHOLD = 18
LEVEL1_SEC = 1.5
LEVEL2_SEC = 3.0
LEVEL3_SEC = 5.0

# ══════════════════════════════════════════════
#  ALARM ENGINE
# ══════════════════════════════════════════════
_alarm_active = False
_alarm_thread = None

def _alarm_loop(level):
    global _alarm_active
    ALARM_SOUND.play(-1)
    while _alarm_active:
        time.sleep(0.1)
    ALARM_SOUND.stop()

def start_alarm(level):
    global _alarm_active, _alarm_thread
    if _alarm_active:
        return
    _alarm_active = True
    _alarm_thread = threading.Thread(target=_alarm_loop, args=(level,), daemon=True)
    _alarm_thread.start()

def stop_alarm():
    global _alarm_active
    _alarm_active = False

# ══════════════════════════════════════════════
#  COLOR PALETTE (BGR)
# ══════════════════════════════════════════════
C_GREEN   = (80, 220, 100)
C_YELLOW  = (0,  210, 255)
C_ORANGE  = (0,  140, 255)
C_RED     = (50,  50, 230)
C_WHITE   = (240, 240, 240)
C_DARK    = (25,  25,  30)
C_ACCENT  = (200, 160,  60)

FONT      = cv2.FONT_HERSHEY_SIMPLEX
FONT_BOLD = cv2.FONT_HERSHEY_DUPLEX

# ══════════════════════════════════════════════
#  DRAWING HELPERS
# ══════════════════════════════════════════════
def alpha_rect(img, x1, y1, x2, y2, color, alpha=0.65):
    sub = img[y1:y2, x1:x2]
    rect = np.full(sub.shape, color, dtype=np.uint8)
    cv2.addWeighted(rect, alpha, sub, 1 - alpha, 0, sub)
    img[y1:y2, x1:x2] = sub

def shadow_text(img, text, pos, font, scale, color, thick=1):
    x, y = pos
    cv2.putText(img, text, (x+1, y+1), font, scale, (0,0,0), thick+1, cv2.LINE_AA)
    cv2.putText(img, text, pos,         font, scale, color,   thick,   cv2.LINE_AA)

def draw_progress_bar(img, x, y, w, h, pct, color):
    cv2.rectangle(img, (x, y), (x+w, y+h), (50,50,55), -1)
    cv2.rectangle(img, (x, y), (x+w, y+h), (80,80,85),  1)
    fill = int(pct * w)
    if fill > 0:
        cv2.rectangle(img, (x, y), (x+fill, y+h), color, -1)

# ══════════════════════════════════════════════
#  HUD
# ══════════════════════════════════════════════
def draw_hud(frame, state):
    h, w = frame.shape[:2]

    # Top bar
    alpha_rect(frame, 0, 0, w, 52, C_DARK, alpha=0.82)
    cv2.line(frame, (0, 52), (w, 52), C_ACCENT, 1)
    shadow_text(frame, "SLEEP", (12, 34),  FONT_BOLD, 0.85, C_ACCENT, 2)
    shadow_text(frame, "ALARM", (80, 34),  FONT_BOLD, 0.85, C_WHITE,  2)
    shadow_text(frame, "SYSTEM", (155, 34), FONT_BOLD, 0.62, (160,160,160), 1)
    shadow_text(frame, "by Haseeb Biya", (260, 30), FONT, 0.42, (130,130,140), 1)

    # FPS
    alpha_rect(frame, w-90, 12, w-10, 40, (40,40,45), alpha=0.9)
    cv2.rectangle(frame, (w-90,12), (w-10,40), (70,70,75), 1)
    shadow_text(frame, f"FPS {state['fps']:.0f}", (w-82, 33), FONT, 0.48, C_WHITE, 1)

    # Right side panel
    px = w - 200
    alpha_rect(frame, px, 60, w, h-60, C_DARK, alpha=0.72)
    cv2.line(frame, (px, 60), (px, h-60), C_ACCENT, 1)

    # Status badge
    status = state["status"]
    status_color = C_GREEN  if status == "AWAKE"   else \
                   C_YELLOW if status == "DROWSY"  else \
                   C_ORANGE if status == "WARNING" else \
                   C_RED    if status == "DANGER"  else (150,150,150)

    alpha_rect(frame, px+10, 70, w-10, 108, status_color, alpha=0.25)
    cv2.rectangle(frame, (px+10,70), (w-10,108), status_color, 1)
    tw = cv2.getTextSize(status, FONT_BOLD, 0.72, 2)[0][0]
    cx = px + 10 + ((w-20-px) - tw) // 2
    shadow_text(frame, status, (cx, 97), FONT_BOLD, 0.72, status_color, 2)

    # Drowsiness bar
    shadow_text(frame, "DROWSINESS", (px+10, 128), FONT, 0.4, (160,160,160), 1)
    pct = min(state["closed_frames"] / EYE_CLOSED_THRESHOLD, 1.0)
    bar_color = C_GREEN if pct < 0.4 else C_YELLOW if pct < 0.7 else C_RED
    draw_progress_bar(frame, px+10, 133, w-px-20, 14, pct, bar_color)
    shadow_text(frame, f"{int(pct*100)}%", (w-42, 145), FONT, 0.38, bar_color, 1)

    cv2.line(frame, (px+10, 158), (w-10, 158), (60,60,65), 1)

    # Stats
    stats = [
        ("EYES",   f"{state['eyes_found']} found",  C_WHITE),
        ("ALARM",  f"Level {state['alarm_level']}", C_YELLOW if state['alarm_level'] > 0 else C_WHITE),
        ("EVENTS", str(state['total_events']),       C_WHITE),
        ("UPTIME", f"{int(state['uptime'])}s",       C_WHITE),
    ]
    sy = 175
    for label, val, vc in stats:
        shadow_text(frame, label, (px+12, sy),    FONT, 0.38, (130,130,140), 1)
        shadow_text(frame, val,   (px+12, sy+16), FONT, 0.5,  vc, 1)
        sy += 44

    # Alarm level dots
    lv = state["alarm_level"]
    shadow_text(frame, "ALARM LEVEL", (px+10, sy+10), FONT, 0.38, (130,130,140), 1)
    dot_colors = [(80,80,85), (80,80,85), (80,80,85)]
    if lv >= 1: dot_colors[0] = C_YELLOW
    if lv >= 2: dot_colors[1] = C_ORANGE
    if lv >= 3: dot_colors[2] = C_RED
    for i, dc in enumerate(dot_colors):
        cx2 = px + 20 + i * 30
        cv2.circle(frame, (cx2, sy+28), 10, dc, -1)
        cv2.circle(frame, (cx2, sy+28), 10, (100,100,105), 1)

    # Bottom bar
    alpha_rect(frame, 0, h-55, w, h, C_DARK, alpha=0.82)
    cv2.line(frame, (0, h-55), (w, h-55), (60,60,65), 1)
    shadow_text(frame, "[Q] Quit", (12, h-28), FONT, 0.45, (160,160,160), 1)
    shadow_text(frame, "[R] Reset Stats", (100, h-28), FONT, 0.45, (160,160,160), 1)

    if not _alarm_active:
        shadow_text(frame, "System Active - Monitoring...", (w//2 - 140, h-28), FONT, 0.45, C_GREEN, 1)
    else:
        if int(time.time() * 3) % 2 == 0:
            shadow_text(frame, "ALARM ACTIVE!", (w//2 - 80, h-28), FONT_BOLD, 0.6, C_RED, 2)

    # Center flashing overlay
    if lv >= 2:
        msgs = {
            2: ("WAKE UP!", C_ORANGE),
            3: ("WAKE UP! WAKE UP NOW!", C_RED),
        }
        msg, mc = msgs[lv]
        if int(time.time() * 2) % 2 == 0:
            tw2 = cv2.getTextSize(msg, FONT_BOLD, 1.2, 3)[0][0]
            bx = (px - tw2) // 2
            alpha_rect(frame, bx-20, h//2-50, bx+tw2+20, h//2+20, mc, alpha=0.15)
            cv2.rectangle(frame, (bx-20, h//2-50), (bx+tw2+20, h//2+20), mc, 2)
            shadow_text(frame, msg, (bx, h//2+10), FONT_BOLD, 1.2, mc, 3)

# ══════════════════════════════════════════════
#  DETECTION ENGINE
# ══════════════════════════════════════════════
class SleepDetector:
    def __init__(self):
        self.face_cas = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.eye_cas  = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")
        self.closed_frames = 0
        self.alarm_level   = 0
        self.total_events  = 0
        self.drowsy_start  = None
        self.start_time    = time.time()
        self._event_logged = False
        self._fps_time     = time.time()
        self._fps_count    = 0
        self.fps           = 0.0

    def reset(self):
        self.closed_frames = 0
        self.alarm_level   = 0
        self.total_events  = 0
        self.drowsy_start  = None
        self._event_logged = False
        stop_alarm()

    def run(self, frame):
        self._fps_count += 1
        now = time.time()
        if now - self._fps_time >= 1.0:
            self.fps = self._fps_count / (now - self._fps_time)
            self._fps_count = 0
            self._fps_time  = now

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        faces = self.face_cas.detectMultiScale(gray, 1.1, 5, minSize=(90,90))
        eyes_found = 0

        for (fx, fy, fw, fh) in faces:
            color = C_GREEN if self.alarm_level == 0 else C_RED
            cv2.rectangle(frame, (fx,fy), (fx+fw,fy+fh), color, 2)
            cl = 18
            for (cx2,cy2,dx,dy) in [(fx,fy,1,1),(fx+fw,fy,-1,1),(fx,fy+fh,1,-1),(fx+fw,fy+fh,-1,-1)]:
                cv2.line(frame, (cx2,cy2), (cx2+dx*cl,cy2), C_ACCENT, 2)
                cv2.line(frame, (cx2,cy2), (cx2,cy2+dy*cl), C_ACCENT, 2)

            roi_g = gray [fy:fy+fh//2, fx:fx+fw]
            roi_c = frame[fy:fy+fh//2, fx:fx+fw]
            eyes = self.eye_cas.detectMultiScale(roi_g, 1.05, 8, minSize=(22,22), maxSize=(80,80))

            for (ex, ey, ew, eh) in eyes:
                ecx, ecy = ex+ew//2, ey+eh//2
                cv2.ellipse(roi_c, (ecx,ecy), (ew//2,eh//2), 0, 0, 360, C_GREEN, 2)
                cv2.circle(roi_c, (ecx,ecy), 3, C_ACCENT, -1)
                eyes_found += 1

        face_detected = len(faces) > 0

        if face_detected and eyes_found == 0:
            self.closed_frames += 1
            if self.drowsy_start is None:
                self.drowsy_start = time.time()
            if not self._event_logged:
                self.total_events += 1
                self._event_logged = True
        elif eyes_found >= 1:
            self.closed_frames = max(0, self.closed_frames - 4)
            if self.closed_frames == 0:
                if self.alarm_level > 0:
                    stop_alarm()
                self.alarm_level   = 0
                self.drowsy_start  = None
                self._event_logged = False

        drowsy_secs = (time.time() - self.drowsy_start) if self.drowsy_start else 0
        if self.closed_frames >= EYE_CLOSED_THRESHOLD:
            new_level = 1
            if drowsy_secs >= LEVEL3_SEC:   new_level = 3
            elif drowsy_secs >= LEVEL2_SEC: new_level = 2
            if new_level != self.alarm_level:
                stop_alarm()
                time.sleep(0.05)
                self.alarm_level = new_level
                start_alarm(new_level)
        else:
            if self.alarm_level > 0:
                stop_alarm()
                self.alarm_level = 0

        if not face_detected:       status = "NO FACE"
        elif self.alarm_level == 3: status = "DANGER"
        elif self.alarm_level == 2: status = "WARNING"
        elif self.alarm_level == 1: status = "DROWSY"
        else:                       status = "AWAKE"

        state = {
            "status":        status,
            "closed_frames": self.closed_frames,
            "alarm_level":   self.alarm_level,
            "eyes_found":    eyes_found,
            "total_events":  self.total_events,
            "uptime":        time.time() - self.start_time,
            "fps":           self.fps,
        }
        draw_hud(frame, state)
        return frame

# ══════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════
def main():
    print("=" * 50)
    print("    SLEEP ALARM SYSTEM — Haseeb Biya")
    print("=" * 50)
    print("  Controls : Q = Quit  |  R = Reset")
    print("=" * 50 + "\n")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Cannot open webcam!")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  900)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 560)
    cap.set(cv2.CAP_PROP_FPS, 30)

    detector = SleepDetector()
    print("[INFO] System running. Stay awake!")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        frame = detector.run(frame)
        cv2.imshow("Sleep Alarm System — Haseeb Biya", frame)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), ord('Q'), 27):
            break
        elif key in (ord('r'), ord('R')):
            detector.reset()
            print("[INFO] Stats reset.")

    stop_alarm()
    cap.release()
    cv2.destroyAllWindows()
    print("\n[INFO] Session ended. Stay alert always!")

if __name__ == "__main__":
    main()