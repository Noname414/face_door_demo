# ============================================================
# recognize_camera.py — Real-time face recognition via webcam
# ============================================================
# Usage:
#   python recognize_camera.py
#
# Controls:
#   q — quit
#
# 流程:
#   1. 開啟攝影機 + 載入 InsightFace + 載入 face_db.pkl
#   2. 開啟與 Arduino 的藍牙序列埠 (config.SERIAL_PORT)
#   3. 每一幀做臉部辨識:
#        - 認識的人 → 送 "OPEN\n" 給 Arduino (有冷卻避免重送)
#        - 陌生人  → 送 "DENY\n"
#   4. Arduino 端 (face_door.ino) 收到 OPEN 就轉動伺服馬達模擬開門
# ============================================================

import sys
import time

import cv2
import numpy as np

import config
from utils import (
    l2_normalize,
    load_face_app,
    load_face_db,
    recognize_face,
)

# ---- Display constants ----------------------------------------
COLOR_KNOWN   = (0, 255, 0)    # Green  — recognised person
COLOR_UNKNOWN = (0, 0, 255)    # Red    — unknown
FONT          = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE    = 0.7
THICKNESS     = 2


def draw_result(
    frame: np.ndarray,
    bbox,
    name: str,
    similarity: float,
) -> None:
    """Draw bounding box and identity label on *frame* in-place."""
    x1, y1, x2, y2 = [int(v) for v in bbox]
    color = COLOR_KNOWN if name != "unknown" else COLOR_UNKNOWN
    label = f"{name}  {similarity:.2f}"

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, THICKNESS)
    (tw, th), _ = cv2.getTextSize(label, FONT, FONT_SCALE, THICKNESS)
    cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
    cv2.putText(
        frame, label,
        (x1 + 2, y1 - 4),
        FONT, FONT_SCALE,
        (255, 255, 255),
        THICKNESS,
        cv2.LINE_AA,
    )


# ------------------------------------------------------------------
# Bluetooth / serial helpers
# ------------------------------------------------------------------

# HC-05 / HC-06 廠商 MAC OUI (前6碼)
_HC_OUI = {"98D331", "BCA080", "001131", "20C38F", "000000"}


def _get_bt_friendly_names() -> dict[str, str]:
    """從 Windows 登錄檔讀取已配對藍牙裝置名稱，回傳 {MAC大寫: name}。"""
    import re
    names: dict[str, str] = {}
    try:
        import winreg
        key_path = r"SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Devices"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as root:
            i = 0
            while True:
                try:
                    mac_hex = winreg.EnumKey(root, i)
                    with winreg.OpenKey(root, mac_hex) as dev:
                        try:
                            name, _ = winreg.QueryValueEx(dev, "Name")
                            if isinstance(name, (bytes, bytearray)):
                                name = name.rstrip(b"\x00").decode("utf-8", errors="ignore")
                            names[mac_hex.upper()] = name
                        except FileNotFoundError:
                            pass
                    i += 1
                except OSError:
                    break
    except Exception:
        pass
    return names


def find_bt_port() -> str | None:
    """掃描所有 COM 埠，自動回傳最可能是 HC-05/HC-06 的埠號。"""
    import re
    try:
        import serial.tools.list_ports
    except ImportError:
        return None

    bt_ports = [
        p for p in serial.tools.list_ports.comports()
        if "BTHENUM" in (p.hwid or "").upper()
    ]
    if not bt_ports:
        return None

    friendly = _get_bt_friendly_names()

    def mac_from_hwid(hwid: str) -> str | None:
        m = re.search(r"([0-9A-Fa-f]{12})_C", hwid)
        if not m:
            m = re.search(r"([0-9A-Fa-f]{12})", hwid)
        return m.group(1).upper() if m else None

    hint = getattr(config, "SERIAL_NAME_HINT", "").lower()

    # 優先 1: 裝置名稱符合 SERIAL_NAME_HINT
    if hint:
        for p in bt_ports:
            mac = mac_from_hwid(p.hwid or "")
            name = friendly.get(mac, "").lower() if mac else ""
            if hint in name:
                print(f"[BT] 依名稱 '{config.SERIAL_NAME_HINT}' 找到: {p.device}")
                return p.device

    # 優先 2: 已知 HC-05/HC-06 廠商 OUI
    for p in bt_ports:
        hwid_clean = (p.hwid or "").upper().replace(":", "").replace("_", "").replace("-", "")
        for oui in _HC_OUI:
            if oui in hwid_clean:
                return p.device

    # fallback：BTHENUM 埠號最大的通常是「傳出」埠
    bt_ports.sort(key=lambda x: int(x.device.replace("COM", "")), reverse=True)
    return bt_ports[0].device


def open_serial():
    """Try to open the configured serial port. Return Serial or None."""
    if not config.SERIAL_ENABLED:
        print("[BT] SERIAL_ENABLED=False, skipping Arduino connection.")
        return None
    try:
        import serial  # pyserial
    except ImportError:
        print("[BT][WARN] pyserial not installed. Run: pip install pyserial")
        return None

    port = config.SERIAL_PORT
    if port.upper() == "AUTO":
        print("[BT] 自動偵測藍牙 COM 埠…")
        port = find_bt_port()
        if port:
            print(f"[BT] 找到藍牙埠: {port}")
        else:
            print("[BT][WARN] 找不到藍牙裝置，請確認已配對或手動設定 config.SERIAL_PORT")
            return None

    try:
        bt = serial.Serial(port, config.SERIAL_BAUD, timeout=1)
        time.sleep(2.0)  # 給 Arduino reset 一點時間
        print(f"[BT] Connected to {port} @ {config.SERIAL_BAUD}")
        return bt
    except Exception as exc:
        print(f"[BT][WARN] Cannot open {port}: {exc}")
        print("[BT][WARN] Continuing without Arduino. (辨識仍可運作)")
        return None


def send_cmd(bt, cmd: str) -> bool:
    """Send a single command line to Arduino. Returns True if actually sent."""
    if bt is None:
        return False
    try:
        bt.write((cmd + "\n").encode("ascii"))
        return True
    except Exception as exc:
        print(f"[BT][WARN] write failed: {exc}")
        return False


def main() -> None:
    # ---- Load model and database ---------------------------------
    print("Loading InsightFace model …")
    app = load_face_app()
    print("Model ready.")

    face_db = load_face_db(config.DB_PATH)
    if not face_db:
        print(
            "[ERROR] Face database is empty or missing.\n"
            "        Run  python register_faces.py  first."
        )
        sys.exit(1)
    print(f"Loaded {len(face_db)} registered identities: {list(face_db.keys())}\n")

    # ---- Open Arduino serial -------------------------------------
    bt = open_serial()

    # ---- Open webcam ---------------------------------------------
    cap = cv2.VideoCapture(config.CAMERA_ID)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open camera (ID={config.CAMERA_ID}). Aborting.")
        if bt is not None:
            bt.close()
        sys.exit(1)

    w, h = config.FRAME_SIZE
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

    print("Camera open. Press  q  to quit.\n")

    # 同一個指令在 DOOR_COOLDOWN_SEC 內只送一次, 避免每幀都重發
    last_sent_cmd: str | None = None
    last_sent_at: float = 0.0

    # ---- Main loop -----------------------------------------------
    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] Failed to grab frame, retrying …")
            continue

        faces = app.get(frame)

        # 這一幀「最有把握」的辨識結果 (用相似度最高那張臉決定要不要開門)
        frame_best_name = "unknown"
        frame_best_sim  = -1.0

        for face in faces:
            emb = l2_normalize(face.normed_embedding)
            name, sim = recognize_face(emb, face_db, config.THRESHOLD)
            draw_result(frame, face.bbox, name, sim)

            if sim > frame_best_sim:
                frame_best_sim  = sim
                frame_best_name = name

        # ---- Decide command + cooldown ---------------------------
        if faces:
            cmd = "OPEN" if frame_best_name != "unknown" else "DENY"
            now = time.time()
            if cmd != last_sent_cmd or (now - last_sent_at) >= config.DOOR_COOLDOWN_SEC:
                sent = send_cmd(bt, cmd)
                bt_status = "sent" if sent else "BT OFFLINE"
                last_sent_cmd = cmd
                last_sent_at  = now
                if cmd == "OPEN":
                    print(f"[DOOR] GRANTED → {frame_best_name} "
                          f"(sim={frame_best_sim:.3f})  → {bt_status} OPEN")
                else:
                    print(f"[DOOR] DENIED  (best sim={frame_best_sim:.3f}) "
                          f"→ {bt_status} DENY")

        # ---- (Optional) read ACK from Arduino --------------------
        if bt is not None and bt.in_waiting:
            try:
                line = bt.readline().decode("ascii", errors="ignore").strip()
                if line:
                    print(f"[BT RX] {line}")
            except Exception:
                pass

        cv2.imshow("Face Door Demo — press q to quit", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # ---- Cleanup -------------------------------------------------
    cap.release()
    cv2.destroyAllWindows()
    if bt is not None:
        send_cmd(bt, "DENY")  # 離開前先把門關起來
        time.sleep(0.1)
        bt.close()
        print("[BT] Serial closed.")
    print("Camera closed. Goodbye.")


if __name__ == "__main__":
    main()
