// ============================================================
// face_door.ino — Face Recognition Door Controller (Servo 版)
// ============================================================
//
// ┌──────────────────────────────────────────────────────────┐
// │  藍牙模組接線 (HC-05 / HC-06)                             │
// └──────────────────────────────────────────────────────────┘
// ⚠️  HC-05/HC-06 是 3.3V 邏輯 — Arduino Uno 是 5V！
//
// 推薦接法 (轉接板版本):
//   藍牙 VCC   →  Arduino 5V
//   藍牙 GND   →  Arduino GND
//   藍牙 TXD   →  Arduino D5      (SoftwareSerial RX)
//   藍牙 RXD   →  Arduino D6      (SoftwareSerial TX，板載分壓可直連)
//   藍牙 EN    →  不接
//   藍牙 STATE →  不接 (或 Arduino D7)
//
// ┌──────────────────────────────────────────────────────────┐
// │  伺服馬達接線 (SG90 / MG90S 之類的 3 線伺服)              │
// └──────────────────────────────────────────────────────────┘
//   伺服 紅線 (VCC)   →  Arduino 5V        (小型 SG90 可以)
//                       ⚠️ 大顆伺服請用外部 5V 電源, GND 共接
//   伺服 棕/黑 (GND)  →  Arduino GND
//   伺服 橘/黃 (訊號) →  Arduino D9        (PWM)
//
// ┌──────────────────────────────────────────────────────────┐
// │  控制指令 (from Python recognize_camera.py)              │
// └──────────────────────────────────────────────────────────┘
//   "OPEN\n"  → 伺服轉到開門角度, UNLOCK_DURATION 毫秒後自動關門
//   "DENY\n"  → 立即關門 (回到關門角度)
// ============================================================

#include <SoftwareSerial.h>
#include <Servo.h>

// ---------- Pin definitions ----------------------------------
const int BT_RX_PIN    = 5;   // Arduino D5 ← BT module TXD
const int BT_TX_PIN    = 6;   // Arduino D6 → BT module RXD (需分壓!)
const int BT_STATE_PIN = 7;   // BT STATE (optional)
const int SERVO_PIN    = 9;   // 伺服馬達訊號腳 (PWM)

// ---------- Parameters ---------------------------------------
const unsigned long UNLOCK_DURATION = 3000;  // ms, 自動關門時間
const int SERVO_CLOSED_ANGLE = 0;            // 關門角度
const int SERVO_OPEN_ANGLE   = 90;           // 開門角度

// ---------- Objects ------------------------------------------
SoftwareSerial btSerial(BT_RX_PIN, BT_TX_PIN);
Servo doorServo;

// ---------- State --------------------------------------------
bool doorOpen = false;
unsigned long openedAt = 0;

// ============================================================
void setup() {
  Serial.begin(9600);      // USB debug
  btSerial.begin(38400);   // HC-06 常見出廠值; 若仍亂碼改試 9600 / 115200

  pinMode(BT_STATE_PIN, INPUT);

  doorServo.attach(SERVO_PIN);
  doorServo.write(SERVO_CLOSED_ANGLE);  // 上電就先確保關門

  Serial.println("[BOOT] Face Door (Servo) ready.");
  Serial.println("[INFO] Waiting for Bluetooth commands…");
}

// ============================================================
void loop() {
  // ---- 讀取藍牙指令 ----------------------------------------
  if (btSerial.available()) {
    String cmd = btSerial.readStringUntil('\n');
    cmd.trim();  // 去掉 \r

    Serial.print("[BT RX] \"");
    Serial.print(cmd);
    Serial.println("\"");

    if (cmd == "OPEN") {
      openDoor();
    } else if (cmd == "DENY") {
      closeDoor();
      Serial.println("[DOOR] Access DENIED — keeping closed.");
    } else {
      Serial.print("[WARN] Unknown command: ");
      Serial.println(cmd);
    }
  }

  // ---- UNLOCK_DURATION 後自動關門 --------------------------
  if (doorOpen && (millis() - openedAt >= UNLOCK_DURATION)) {
    closeDoor();
    Serial.println("[DOOR] Auto-close after timeout.");
  }
}

// ============================================================
// Helpers
// ============================================================

void openDoor() {
  if (!doorOpen) {
    doorServo.write(SERVO_OPEN_ANGLE);
    doorOpen = true;
    openedAt = millis();
    Serial.println("[DOOR] OPENED.");
    btSerial.println("ACK:OPEN");
  } else {
    // 已經開了, 重設關門計時
    openedAt = millis();
    Serial.println("[DOOR] Already open — timer reset.");
  }
}

void closeDoor() {
  doorServo.write(SERVO_CLOSED_ANGLE);
  doorOpen = false;
  Serial.println("[DOOR] CLOSED.");
}
