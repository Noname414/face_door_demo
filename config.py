# ============================================================
# config.py — Project-wide configuration
# ============================================================

# InsightFace model name
MODEL_NAME = "buffalo_l"

# Path to the face database (pickle file)
DB_PATH = "face_db.pkl"

# Directory containing known face sub-folders
KNOWN_FACES_DIR = "known_faces"

# Webcam device index
CAMERA_ID = 0

# Detection input size for InsightFace
DET_SIZE = (640, 640)

# Displayed frame resolution
FRAME_SIZE = (640, 480)

# Cosine-similarity threshold for identity matching
# 0.40 = loose  | 0.45 = normal  | 0.50 = strict
# For door access a stricter value (0.50) is recommended.
THRESHOLD = 0.45

# ONNX execution providers — 自動偵測 GPU，沒有則 fallback 到 CPU
# 若要強制 CPU: PROVIDERS = ["CPUExecutionProvider"]
# 若要強制 GPU: PROVIDERS = ["CUDAExecutionProvider", "CPUExecutionProvider"]
def _auto_providers():
    try:
        import onnxruntime as ort
        if "CUDAExecutionProvider" in ort.get_available_providers():
            return ["CUDAExecutionProvider", "CPUExecutionProvider"]
    except Exception:
        pass
    return ["CPUExecutionProvider"]

PROVIDERS = _auto_providers()

# ------------------------------------------------------------------
# Arduino / Bluetooth serial (for servo door control)
# ------------------------------------------------------------------
# Windows: 在「裝置管理員 → 連接埠 (COM & LPT)」找到藍牙的
#          「標準序列埠 (傳出)」, 例如 COM5
# Linux/macOS: 例如 "/dev/rfcomm0" 或 "/dev/tty.HC05-DevB"
# "AUTO" = 啟動時自動掃描藍牙 COM 埠 (推薦)
# 或直接填寫埠號，例如 "COM9"
SERIAL_PORT    = "AUTO"
SERIAL_BAUD    = 38400  # HC-06 常見出廠值; 若亂碼改試 9600 / 115200
SERIAL_ENABLED = True   # 設成 False 可關閉藍牙傳送 (純測試辨識)

# 自動偵測時優先比對的藍牙裝置名稱關鍵字 (大小寫不分)
# find_bt_port.py 顯示的「藍牙裝置名稱」欄包含此字串即優先選用
SERIAL_NAME_HINT = "FaceDoor"

# 同一個人連續被辨識時, 兩次送 OPEN 的最小間隔 (秒)
# 避免每一幀都重送指令灌爆藍牙
DOOR_COOLDOWN_SEC = 5.0

# 每隔幾幀才跑一次 InsightFace 推論 (1 = 每幀都跑，最準但最慢)
# 建議值: 3~5 (大幅提升 FPS，辨識結果在中間幀持續顯示)
INFER_EVERY_N_FRAMES = 3
