# Windows 端設定指南

## 📋 系統需求

- Windows 10/11
- Python 3.8 或以上
- 內建或外接藍牙適配器
- USB 攝影機 (或筆電內建鏡頭)

---

## 🔧 Step 1: 安裝 Python 依賴

### 1.1 開啟 PowerShell 或命令提示字元

```powershell
cd D:\github\face_door_demo
```

### 1.2 (建議) 建立虛擬環境

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

如果出現「無法載入指令碼」錯誤，執行：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 1.3 安裝套件

```powershell
pip install -r requirements.txt
```

等待安裝完成 (InsightFace 模型約 200MB)

---

## 📡 Step 2: 藍牙配對 HC-05/HC-06

### 2.1 確認 Arduino 已上傳程式並通電

- 藍牙模組 LED 應該「快速閃爍」(未配對狀態)
- 如果不閃，檢查 VCC/GND 是否接好

### 2.2 開啟 Windows 藍牙設定

**方法 1 (Windows 11):**
```
開始 → 設定 → 藍牙與裝置 → 新增裝置 → 藍牙
```

**方法 2 (Windows 10):**
```
開始 → 設定 → 裝置 → 新增藍牙或其他裝置 → 藍牙
```

**方法 3 (快速):**
```
Win + I → 搜尋「藍牙」
```

### 2.3 搜尋並配對

1. 等待搜尋到 `HC-05` 或 `HC-06` (有些會顯示 MAC 位址)
2. 點擊裝置名稱
3. 輸入 PIN 碼：
   - 預設通常是 `1234` 或 `0000`
   - 如果都不對，試試 `000000` (六個零)
4. 配對成功後，LED 會變成「慢速閃爍」(約 2 秒閃 1 次)

### 2.4 ⚠️ 重要：找到「傳出 COM 埠」

配對成功後，**必須再做這一步**：

#### 方法 A: 裝置管理員 (推薦)

1. 按 `Win + X` → 選擇「裝置管理員」
2. 展開「**連接埠 (COM 和 LPT)**」
3. 找到類似這樣的項目：
   ```
   標準序列透過藍牙連結 (COM5)   ← 這是「傳入」，不要用
   標準序列透過藍牙連結 (COM6)   ← 這是「傳出」，用這個！
   ```
4. **記下「傳出」那個 COM 埠號** (通常較大，例如 COM5~COM10)

**如何分辨傳入/傳出？**
- 右鍵點擊 → 內容 → 詳細資料 → 裝置範例識別項
- 如果路徑包含 `&0000` = 傳入 (❌ 不要用)
- 如果路徑包含 `&0001` = 傳出 (✅ 用這個)

#### 方法 B: PowerShell 指令

```powershell
Get-WmiObject -Class Win32_PnPEntity | Where-Object { $_.Name -like "*標準序列*藍牙*" } | Select-Object Name, DeviceID
```

找包含 `&0001` 的那一筆。

#### 方法 C: 控制台

```
控制台 → 硬體和音效 → 裝置和印表機
→ 右鍵點 HC-05 → 內容 → 服務
→ 查看「序列埠 (傳出)」
```

---

## ⚙️ Step 3: 修改 config.py

用 VS Code 或記事本開啟 `config.py`，修改這幾行：

### 3.1 設定 COM 埠 (必改)

```python
# 藍牙序列埠設定
SERIAL_PORT = "COM6"  # ← 改成你剛才記下的「傳出」埠號
```

### 3.2 其他可選設定

```python
# 攝影機編號 (0 = 內建鏡頭, 1 = 外接 USB 攝影機)
CAMERA_ID = 0

# 辨識門檻 (0.40 寬鬆 ~ 0.50 嚴格)
THRESHOLD = 0.45

# 關閉藍牙傳送 (純測試辨識用)
SERIAL_ENABLED = True  # 改 False 可不連 Arduino

# 同一人防重送間隔 (秒)
DOOR_COOLDOWN_SEC = 5.0
```

---

## 📸 Step 4: 註冊人臉

### 4.1 準備照片

在 `known_faces/` 建立資料夾，例如：

```
known_faces/
  ├─ Leo/
  │   ├─ photo1.jpg
  │   ├─ photo2.jpg
  │   └─ photo3.jpg
  ├─ Alice/
  │   ├─ 01.png
  │   └─ 02.png
  └─ Bob/
      └─ headshot.jpg
```

**照片要求：**
- 每人至少 1 張 (建議 3~5 張不同角度)
- 正面清晰照
- 光線充足
- 只有一張臉 (多張臉會用最大那張)

### 4.2 執行註冊

```powershell
python register_faces.py
```

**正確輸出範例：**
```
Loading InsightFace model …
Model ready.

[OK] Leo: photo1.jpg
[OK] Leo: photo2.jpg
[OK] Leo: photo3.jpg
[OK] Alice: 01.png
[OK] Alice: 02.png
[OK] Bob: headshot.jpg

Face database saved to face_db.pkl
Total registered people: 3
  - Leo
  - Alice
  - Bob
```

---

## 🚀 Step 5: 執行辨識程式

### 5.1 確認硬體連接

- [ ] Arduino 已通電
- [ ] 藍牙已配對且 LED 慢閃
- [ ] 伺服馬達接在 D9
- [ ] 攝影機已連接

### 5.2 啟動程式

```powershell
python recognize_camera.py
```

**正確啟動訊息：**
```
Loading InsightFace model …
Model ready.
Loaded 3 registered identities: ['Leo', 'Alice', 'Bob']

[BT] Connected to COM6 @ 9600
Camera open. Press  q  to quit.
```

### 5.3 測試辨識

1. 對著鏡頭露臉
2. 如果是註冊過的人：
   ```
   [DOOR] GRANTED → Leo (sim=0.652)  → sent OPEN
   [BT RX] ACK:OPEN
   ```
   伺服馬達轉到 90°，3 秒後自動回 0°

3. 如果是陌生人：
   ```
   [DOOR] DENIED (best sim=0.321) → sent DENY
   ```
   伺服保持關門角度

### 5.4 結束程式

按鍵盤 **`q`** 鍵即可退出 (會自動送 DENY 關門)

---

## 🔍 疑難排解

### ❌ 問題 1: 找不到 pyserial

**錯誤訊息：**
```
[BT][WARN] pyserial not installed. Run: pip install pyserial
```

**解決方法：**
```powershell
pip install pyserial
```

---

### ❌ 問題 2: Cannot open COM5

**錯誤訊息：**
```
[BT][WARN] Cannot open COM5: PermissionError: [Errno 13] Access is denied
```

**可能原因：**
1. COM 埠被其他程式佔用 (Arduino IDE、PuTTY 等)
2. 用了「傳入」埠而非「傳出」埠
3. 藍牙未配對或斷線

**解決方法：**
1. 關閉所有序列埠監控程式
2. 重新確認是「傳出」埠 (含 `&0001`)
3. 重新配對藍牙
4. 重啟電腦 (終極大法)

---

### ❌ 問題 3: 攝影機打不開

**錯誤訊息：**
```
[ERROR] Cannot open camera (ID=0). Aborting.
```

**解決方法：**
1. 確認攝影機沒被其他程式佔用 (Teams、Zoom 等)
2. 改 `config.py` 的 `CAMERA_ID`：
   ```python
   CAMERA_ID = 1  # 試試不同數字 0, 1, 2 ...
   ```
3. Windows 隱私權設定：
   ```
   設定 → 隱私權 → 相機
   → 允許應用程式存取您的相機 (開啟)
   ```

---

### ❌ 問題 4: InsightFace 模型下載失敗

**錯誤訊息：**
```
Cannot download model from ...
```

**解決方法：**
1. 檢查網路連線
2. 手動下載模型：
   - 到 [InsightFace GitHub](https://github.com/deepinsight/insightface/tree/master/model_zoo)
   - 下載 `buffalo_l.zip`
   - 解壓到 `~/.insightface/models/buffalo_l/`
3. 或改用較小的模型 (改 `config.py`)：
   ```python
   MODEL_NAME = "buffalo_s"  # 較小，速度快但準確度稍低
   ```

---

### ❌ 問題 5: 辨識率太低 / 太高

**狀況 A: 一直說 unknown (太嚴格)**

降低門檻值：
```python
THRESHOLD = 0.40  # 改小一點
```

**狀況 B: 陌生人也能開門 (太寬鬆)**

提高門檻值：
```python
THRESHOLD = 0.50  # 改大一點
```

**狀況 C: 光線影響大**

1. 註冊時多拍幾張不同光線的照片
2. 改善環境照明
3. 調整攝影機曝光度

---

### ❌ 問題 6: 藍牙一直斷線

**症狀：** 用一下就出現 `[BT][WARN] write failed`

**可能原因：**
1. 藍牙模組供電不穩
2. 距離太遠 (HC-05 有效距離約 10m)
3. 干擾源 (WiFi、微波爐)

**解決方法：**
1. 確認 VCC 接 5V 且電流充足
2. 縮短距離
3. 重新配對

---

### ❌ 問題 7: 伺服一直抖動

**解決方法：**
1. 用外部 5V 2A 電源供電 (GND 共接)
2. 在伺服 VCC 加去耦電容 (100μF)
3. 確認 Arduino D9 接線穩固

---

## 📊 效能調校

### CPU 太高 / 畫面卡頓

降低解析度：
```python
FRAME_SIZE = (320, 240)  # 改小一點
DET_SIZE = (320, 320)
```

### 想用 GPU 加速

改 `config.py`：
```python
PROVIDERS = ["CUDAExecutionProvider", "CPUExecutionProvider"]
```

需先安裝：
```powershell
pip install onnxruntime-gpu
```

---

## 🧪 測試藍牙通訊 (不用攝影機)

建立測試檔 `test_bluetooth.py`：

```python
import serial
import time

# 改成你的 COM 埠
bt = serial.Serial("COM6", 9600, timeout=1)
time.sleep(2)

print("發送 OPEN 指令...")
bt.write(b"OPEN\n")
time.sleep(0.5)

if bt.in_waiting:
    print("Arduino 回應:", bt.readline().decode().strip())

time.sleep(3)

print("發送 DENY 指令...")
bt.write(b"DENY\n")
time.sleep(0.5)

bt.close()
print("測試完成")
```

執行：
```powershell
python test_bluetooth.py
```

應該看到伺服動作。

---

## 🎯 完整執行流程摘要

```powershell
# 1. 安裝依賴
pip install -r requirements.txt

# 2. 配對藍牙，記下 COM 埠

# 3. 修改 config.py
# SERIAL_PORT = "COM6"  ← 改這行

# 4. 註冊人臉
python register_faces.py

# 5. 執行辨識
python recognize_camera.py

# 6. 按 q 退出
```

---

## 📱 手機藍牙測試工具 (可選)

如果想用手機先測試 Arduino：

**Android:**
- **Serial Bluetooth Terminal** (推薦)
  - 安裝後搜尋 HC-05
  - 連線，輸入 `OPEN` 送出
  - 應該看到伺服動作

**iOS:**
- HC-05/HC-06 是傳統藍牙 (SPP)，iOS 不支援
- 需改用 BLE 模組 (HM-10)

---

## 🔐 進階：修改藍牙 PIN 碼

如果想改成自訂 PIN (例如 `5678`)：

1. 參考 `arduino/AT_Mode_HC05/AT_Mode_HC05.ino`
2. 上傳 AT 模式程式
3. 按住模組按鈕重啟進入 AT 模式
4. 序列埠送 `AT+PSWD="5678"`
5. 改回正常程式 `face_door.ino`

詳見 [AT_Mode_HC05.ino](arduino/AT_Mode_HC05/AT_Mode_HC05.ino)

---

## ✅ 設定完成檢查表

- [ ] Python 依賴已安裝 (`pip list` 確認有 pyserial)
- [ ] 藍牙已配對且 LED 慢閃
- [ ] 已找到「傳出」COM 埠並寫入 `config.py`
- [ ] `face_db.pkl` 已產生 (執行過 `register_faces.py`)
- [ ] 攝影機可用 (Windows 相機 App 能開)
- [ ] Arduino 序列埠監控看到 `[BOOT] Face Door (Servo) ready.`
- [ ] 執行 `recognize_camera.py` 無錯誤訊息

全部打勾就可以開始用了！ 🎉
