# 人臉辨識門禁 Demo

大學期末專題：使用 **InsightFace** + **OpenCV** 進行即時人臉辨識，  
透過藍牙將辨識結果傳送給 Arduino，控制伺服馬達模擬門鎖開關。

---

## 系統架構

```
攝影機 → Python 辨識 → 藍牙 (HC-06) → Arduino → 伺服馬達
```

---

## 技術棧

| 元件 | 說明 |
|------|------|
| Python 3.10 | 主程式語言 |
| InsightFace `buffalo_l` | 人臉辨識模型 (CPU) |
| OpenCV | 攝影機擷取 + 畫面顯示 |
| pyserial | 藍牙序列埠通訊 |
| Arduino Uno + HC-06 | 接收指令、控制伺服 |
| SG90 伺服馬達 | 模擬門鎖動作 |

---

## 一、環境安裝

### 方法 A：用 uv（推薦，快速）

```powershell
# 安裝 uv（若尚未安裝）
pip install uv

# 在專案目錄下同步依賴
cd face_door_demo
uv sync
```

### 方法 B：用 pip + venv

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows PowerShell

pip install -r requirements.txt
```

> 第一次執行會自動下載 `buffalo_l` 模型（約 300 MB），請確保網路暢通。

---

## 二、專案結構

```
face_door_demo/
├── known_faces/           ← 放人臉照片（不上傳 git）
│   └── 你的名字/
│       ├── 1.jpg
│       └── 2.jpg
├── face_db.pkl            ← 自動產生的人臉資料庫（不上傳 git）
│
├── config.py              ← 所有可調參數（COM 埠、門檻值等）
├── utils.py               ← 共用函式
├── register_faces.py      ← 步驟 1：建立人臉資料庫
├── recognize_camera.py    ← 步驟 2：即時辨識 + 送門控指令
├── find_bt_port.py        ← 工具：掃描藍牙 COM 埠
│
└── arduino/
    ├── face_door/
    │   └── face_door.ino  ← Arduino 主程式（伺服馬達控制）
    ├── WIRING.md          ← 硬體接線圖
    └── AT_Mode_HC05/      ← 藍牙模組設定工具
```

---

## 三、新增人員照片

在 `known_faces/` 建立以**姓名命名**的資料夾，放入照片：

```
known_faces/
├── Leo/
│   ├── 正面.jpg
│   ├── 左側.jpg
│   └── 右側.jpg
└── Alice/
    ├── 1.jpg
    └── 2.jpg
```

**照片要求：**
- 每人至少 1 張，建議 3～5 張（不同角度、不同光線）
- 畫面中只有一張臉（多張臉會自動取最大的）
- 格式：JPG、PNG、BMP、WebP 均可

---

## 四、步驟 1：建立人臉資料庫

```powershell
uv run python register_faces.py
# 或
python register_faces.py
```

**正確輸出範例：**

```
Loading InsightFace model …
Model ready.

[OK] Leo: 正面.jpg
[OK] Leo: 左側.jpg
[OK] Leo: 右側.jpg
[OK] Alice: 1.jpg
[OK] Alice: 2.jpg

Face database saved to face_db.pkl
Total registered people: 2
  - Leo
  - Alice
```

每次新增或刪除人員，都要重新執行此步驟。

---

## 五、步驟 2：執行即時辨識

```powershell
uv run python recognize_camera.py
# 或
python recognize_camera.py
```

**啟動訊息範例：**

```
Loading InsightFace model …
Model ready.
Loaded 2 registered identities: ['Leo', 'Alice']

[BT] 自動偵測藍牙 COM 埠…
[BT] 找到藍牙埠: COM13
[BT] Connected to COM13 @ 38400

Camera open. Press  q  to quit.
```

**辨識中的 log：**

```
[DOOR] GRANTED → Leo (sim=0.651)  → sent OPEN    ← 認識的人，伺服開門
[DOOR] DENIED  (best sim=0.312)   → sent DENY    ← 陌生人，保持關閉
[BT RX] ACK:OPEN                                  ← Arduino 回應確認
```

按鍵盤 **`q`** 結束程式（會自動送 DENY 關門）。

---

## 六、設定參數（config.py）

開啟 `config.py` 修改：

```python
# ── 藍牙設定 ──────────────────────────────────────────
SERIAL_PORT    = "AUTO"   # "AUTO" = 自動偵測（推薦）
                          # 或填寫固定埠號，例如 "COM13"
SERIAL_BAUD    = 38400    # HC-06 常見出廠值；若亂碼改試 9600
SERIAL_ENABLED = True     # 改 False = 只跑辨識，不連 Arduino

DOOR_COOLDOWN_SEC = 5.0   # 同一人 5 秒內只送一次 OPEN（防重送）

# ── 辨識門檻 ──────────────────────────────────────────
THRESHOLD = 0.45   # 0.40 寬鬆 | 0.45 正常 | 0.50 嚴格

# ── 攝影機 ────────────────────────────────────────────
CAMERA_ID  = 0     # 0 = 內建鏡頭，1 = 第一支外接 USB 攝影機
```

---

## 七、找藍牙 COM 埠

如果藍牙自動偵測失敗，執行：

```powershell
uv run python find_bt_port.py
```

輸出範例：

```
共找到 7 個 COM 埠：

埠號       裝置描述                          HWID
COM11    Arduino Uno (COM11)              USB VID:PID=2341:0043
COM13    透過藍牙連結的標準序列 (COM13)     BTHENUM\...98D331...  ← 這個
```

找到後填入 `config.py`：

```python
SERIAL_PORT = "COM13"
```

---

## 八、Arduino 硬體

詳細接線圖請看 **[arduino/WIRING.md](arduino/WIRING.md)**

**快速接線摘要：**

```
HC-06 藍牙模組（轉接板版）:
  VCC → Arduino 5V
  GND → Arduino GND
  TXD → Arduino D5
  RXD → Arduino D6

SG90 伺服馬達:
  紅線 → Arduino 5V
  棕線 → Arduino GND
  橘線 → Arduino D9（PWM）
```

**Arduino 指令說明：**

| Python 送出 | Arduino 動作 |
|------------|------------|
| `OPEN\n` | 伺服轉到 90°（開門），3 秒後自動回 0° |
| `DENY\n` | 伺服維持或回到 0°（關門） |

---

## 九、完整執行流程

```
1. 準備照片
   known_faces/你的名字/1.jpg  2.jpg  3.jpg

2. 建立資料庫
   python register_faces.py

3. 上傳 Arduino 程式
   arduino/face_door/face_door.ino
   （上傳前先拔 D5/D6 藍牙線）

4. 設定 COM 埠（可跳過，預設 AUTO）
   config.py → SERIAL_PORT = "AUTO"

5. 啟動辨識
   python recognize_camera.py

6. 對著鏡頭 → 辨識到已註冊人員 → 伺服開門 3 秒
```

---

## 十、常見問題

| 問題 | 原因 | 解法 |
|------|------|------|
| `BT OFFLINE` | 藍牙未配對或埠號錯 | 執行 `find_bt_port.py` 確認 |
| Arduino 收到亂碼 | baud rate 不符 | 改 `SERIAL_BAUD = 9600` 或 `115200` |
| 一直顯示 unknown | 門檻太高或照片太少 | 調低 `THRESHOLD` 或多加照片 |
| 攝影機打不開 | 被其他程式佔用 | 關閉 Teams/Zoom，改 `CAMERA_ID = 1` |
| 伺服抖動 | 供電不穩 | 用外部 5V 2A 電源，GND 共接 |

---

## 隱私說明

- `known_faces/` 與 `face_db.pkl` 已加入 `.gitignore`，**不會上傳到 git**
- 請勿將個人照片直接寫死在程式碼中
