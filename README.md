# 😴 Sleep Alarm System
### Built by Haseeb Biya

A real-time drowsiness detection system using your webcam.  
When your eyes close for too long — **it wakes you up!**

---

## 🚀 Features

| Feature | Details |
|---|---|
| 👁 Real-time eye detection | OpenCV Haar Cascades |
| 📊 Live HUD | Status, FPS, drowsiness bar, stats |
| 🔊 Escalating alarm | 3 levels: soft beep → warning → loud alarm |
| 📈 Session tracking | Total drowsy events, uptime |
| ⌨️ Keyboard controls | Q to quit, R to reset stats |
| 🪞 Mirror view | Natural selfie-style view |

---

## 🛠️ Setup — Step by Step

### Step 1: Make sure Python is installed
```bash
python --version
# Should show Python 3.8 or higher
```

### Step 2: Install dependencies
```bash
pip install opencv-python numpy pygame imutils
```

### Step 3: Run the program
```bash
python sleep_alarm.py
```

---

## 🎮 Controls

| Key | Action |
|---|---|
| `Q` | Quit the program |
| `R` | Reset session stats |

---

## 🧠 How It Works

```
Webcam Feed
    ↓
Face Detection (Haar Cascade)
    ↓
Eye Detection (inside face ROI)
    ↓
Eyes Missing? → Increment closed_frames counter
    ↓
Threshold Reached? → Trigger Alarm
    ↓
Level 1 (1.5s) → Soft beep
Level 2 (3.0s) → Faster beep + Warning text
Level 3 (5.0s) → Rapid alarm + DANGER overlay
    ↓
Eyes Reopen? → Stop alarm, reset counter
```

---

## ⚙️ Customization

Edit the `CONFIG` block at the top of `sleep_alarm.py`:

```python
CONFIG = {
    "EYE_CLOSED_FRAMES_THRESHOLD": 20,  # More = less sensitive
    "LEVEL1_SECONDS": 1.5,              # When first alarm triggers
    "LEVEL2_SECONDS": 3.0,              # When warning escalates
    "LEVEL3_SECONDS": 5.0,              # When DANGER triggers
    ...
}
```

---

## 📋 Requirements

- Python 3.8+
- Webcam (built-in or USB)
- Good lighting (works best in well-lit environments)

---

## 🐛 Troubleshooting

| Problem | Solution |
|---|---|
| "Cannot open webcam" | Check camera is connected / not used by another app |
| Too many false alarms | Increase `MIN_NEIGHBORS_EYE` in CONFIG |
| Not detecting drowsiness | Decrease `EYE_CLOSED_FRAMES_THRESHOLD` |
| No sound | Install pygame: `pip install pygame` |
| Slow FPS | Lower camera resolution in `cap.set()` lines |

---

*Made with ❤️ by Haseeb Biya — CSBS Graduate, BVDU DET*
