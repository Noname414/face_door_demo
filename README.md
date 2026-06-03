# Face Door Demo

A university final-project demo that uses **InsightFace** and **OpenCV** to perform real-time face recognition on a USB webcam.  
The system identifies registered people and marks unknowns — a door relay controlled by Arduino will be added in a future phase.

---

## Tech Stack

| Component | Version / Notes |
|-----------|----------------|
| Python | 3.10 |
| OpenCV | `opencv-python` |
| InsightFace | `buffalo_l` model (CPU) |
| ONNX Runtime | CPU execution provider |
| NumPy | vector math |
| Pickle | local face database |

---

## Environment Setup

```bash
# 1. (Recommended) create a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows

# 2. Install dependencies
pip install -r requirements.txt
```

> The first run will automatically download the `buffalo_l` model (~300 MB) from the InsightFace model hub.

---

## Folder Structure

```
face_door_demo/
├── known_faces/          # One sub-folder per person (NOT committed)
│   ├── Leo/
│   │   ├── 1.jpg
│   │   └── 2.jpg
│   └── <other_person>/
├── face_db.pkl           # Generated face database (NOT committed)
├── config.py             # All tunable parameters
├── utils.py              # Shared helper functions
├── register_faces.py     # Build face_db.pkl from known_faces/
├── recognize_camera.py   # Real-time webcam recognition
├── requirements.txt
└── README.md
```

---

## How to Add a New Person

1. Create a sub-folder with the person's name inside `known_faces/`:
   ```
   known_faces/
   └── Alice/
       ├── 1.jpg
       ├── 2.jpg
       └── 3.jpg
   ```
2. Add **3–5 clear frontal face photos** (JPG / PNG).
3. Re-run `register_faces.py` to rebuild the database.

---

## How to Register Faces

```bash
python register_faces.py
```

Expected output:
```
Loading InsightFace model …
Model ready.

[OK] Leo: 1.jpg
[OK] Leo: 2.jpg
[OK] Alice: 1.jpg
...
Face database saved to face_db.pkl
Total registered people: 2
  - Leo
  - Alice
```

---

## How to Run Camera Recognition

```bash
python recognize_camera.py
```

The webcam window will open.  
Each detected face is surrounded by a bounding box and labelled with the matched name and cosine-similarity score:

```
Leo    similarity=0.721
Alice  similarity=0.658
unknown  similarity=0.312
```

Press **`q`** to quit.

---

## How to Adjust the Threshold

Open `config.py` and change `THRESHOLD`:

```python
THRESHOLD = 0.40   # loose   — easier to match
THRESHOLD = 0.45   # normal  (default)
THRESHOLD = 0.50   # strict  — recommended for door access
```

---

## Future Arduino Integration

> **Status:** Arduino 程式碼已完成，詳見 `arduino/face_door/face_door.ino`  
> **硬體接線指南：** [arduino/WIRING.md](arduino/WIRING.md)

### Python 端整合

在 `recognize_camera.py` 加入藍牙序列埠通訊：

```python
# 安裝依賴
pip install pyserial

# 在 Windows 裝置管理員查看藍牙 COM 埠號 (例如 COM5)
```

**程式碼修改 (在主迴圈前)：**

```python
import serial

# 開啟藍牙序列埠 (改成你的 COM 號)
bt = serial.Serial("COM5", 9600, timeout=1)
```

**在辨識迴圈中發送指令：**

```python
for face in faces:
    emb = l2_normalize(face.normed_embedding)
    name, sim = recognize_face(emb, face_db, config.THRESHOLD)
    draw_result(frame, face.bbox, name, sim)
    
    # 門禁控制邏輯
    if name != "unknown":
        bt.write(b"OPEN\n")
        print(f"[DOOR] Access GRANTED to {name}")
    else:
        bt.write(b"DENY\n")
        print("[DOOR] Access DENIED")
```

**清理資源 (在程式結束前)：**

```python
bt.close()
```

### 硬體需求

| 元件 | 規格 |
|------|------|
| Arduino Uno / Nano | 1 片 |
| HC-05 或 HC-06 藍牙模組 | 1 個 (轉接板版本推薦) |
| 5V 繼電器模組 | 1 個 |
| 電磁鎖 / 電控鎖 | 12V 2A |
| 獨立電源 | 12V 適配器 (驅動電磁鎖) |

**快速接線 (轉接板版本)：**

```
HC-05 藍牙模組:
  VCC → Arduino 5V
  GND → Arduino GND
  TXD → Arduino D5
  RXD → Arduino D6

繼電器模組:
  VCC → Arduino 5V
  GND → Arduino GND
  IN  → Arduino D8

電磁鎖:
  通過繼電器接 12V 獨立電源
```

詳細接線圖與疑難排解請參閱 **[arduino/WIRING.md](arduino/WIRING.md)**。

---

## 完整系統流程

```
┌─────────────┐
│  USB 攝影機  │
└──────┬──────┘
       │ 擷取影像
       ▼
┌─────────────────────┐
│  Python 人臉辨識     │
│  (recognize_camera)  │
└──────┬──────────────┘
       │ 辨識成功/失敗
       ▼
┌─────────────────────┐
│  藍牙序列埠傳送      │
│  OPEN / DENY        │
└──────┬──────────────┘
       │ 藍牙通訊
       ▼
┌─────────────────────┐
│  Arduino 接收指令    │
│  (face_door.ino)    │
└──────┬──────────────┘
       │ 觸發繼電器
       ▼
┌─────────────────────┐
│  電磁鎖開啟 3 秒     │
│  自動上鎖           │
└─────────────────────┘
```

---

## Privacy Notes

- `known_faces/` and `face_db.pkl` are listed in `.gitignore` and will **not** be committed to version control.
- Never hard-code personal images in source files.
