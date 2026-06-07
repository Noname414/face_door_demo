// ============================================================
// face_door.ino — Face Recognition Door Controller (Relay 版)
// ============================================================
//
// ┌──────────────────────────────────────────────────────────┐
// │  藍牙模組接線 (HC-05 / HC-06)                              │
// └──────────────────────────────────────────────────────────┘
//   藍牙 VCC   →  Arduino 5V
//   藍牙 GND   →  Arduino GND
//   藍牙 TXD   →  Arduino D5      (SoftwareSerial RX)
//   藍牙 RXD   →  Arduino D6      (SoftwareSerial TX)
//
// ┌──────────────────────────────────────────────────────────┐
// │  繼電器模組接線 (Relay Module)                              │
// └──────────────────────────────────────────────────────────┘
//   VCC → Arduino 5V
//   GND → Arduino GND
//   IN  → Arduino D9
//   COM → 門鎖控制線 A
//   NO  → 門鎖控制線 B
// ============================================================

#include <SoftwareSerial.h>

// ---------- Pin definitions ----------------------------------
const int BT_RX_PIN    = 5;   
const int BT_TX_PIN    = 6;   
const int RELAY_PIN    = 9;   // 控制繼電器的腳位

// ---------- Parameters ---------------------------------------
const unsigned long TRIGGER_DURATION = 1000;  // ms, 模擬按下按鈕的「短路時間」
                                              // 很多自帶控制板的鎖只需要短路 0.5~1 秒就會自動開門並重新上鎖

// 💡 繼電器觸發邏輯設定
// 市面上的繼電器模組多為「低電平觸發」(LOW 導通)。
// 如果你的模組是「高電平觸發」(HIGH 導通)，請將下面兩個變數互換：
const int RELAY_ON  = HIGH;    // 觸發繼電器 (COM 與 NO 短路)
const int RELAY_OFF = LOW;   // 關閉繼電器 (COM 與 NO 斷開)

// ---------- Objects ------------------------------------------
SoftwareSerial btSerial(BT_RX_PIN, BT_TX_PIN);

// ---------- State --------------------------------------------
bool doorTriggered = false;
unsigned long triggeredAt = 0;

// ============================================================
void setup() {
  Serial.begin(9600);      
  btSerial.begin(38400);   

  // ⚠️ 關鍵：初始化繼電器腳位時，先寫入 OFF 狀態，再設為 OUTPUT
  // 這樣可以避免 Arduino 剛開機瞬間腳位電壓不穩，導致門鎖被意外觸發
  digitalWrite(RELAY_PIN, RELAY_OFF);
  pinMode(RELAY_PIN, OUTPUT);

  Serial.println("[BOOT] Face Door (Relay/Dry Contact) ready.");
  Serial.println("[INFO] Waiting for Bluetooth commands…");
}

// ============================================================
void loop() {
  // ---- 讀取藍牙指令 ----------------------------------------
  if (btSerial.available()) {
    String cmd = btSerial.readStringUntil('\n');
    cmd.trim();  // 去除換行符號

    Serial.print("[BT RX] \"");
    Serial.print(cmd);
    Serial.println("\"");

    if (cmd == "OPEN") {
      triggerDoor();
    } else if (cmd == "DENY") {
      Serial.println("[DOOR] Access DENIED — ignoring.");
    } else {
      Serial.print("[WARN] Unknown command: ");
      Serial.println(cmd);
    }
  }

  // ---- TRIGGER_DURATION 後停止短路 --------------------------
  if (doorTriggered && (millis() - triggeredAt >= TRIGGER_DURATION)) {
    digitalWrite(RELAY_PIN, RELAY_OFF);  // 放開短路
    doorTriggered = false;
    Serial.println("[DOOR] Trigger finished (Relay OFF).");
  }
}

// ============================================================
// Helpers
// ============================================================

void triggerDoor() {
  if (!doorTriggered) {
    digitalWrite(RELAY_PIN, RELAY_ON);  // 讓 COM 與 NO 短路
    doorTriggered = true;
    triggeredAt = millis();
    Serial.println("[DOOR] TRIGGERED (Relay ON) -> Wires shorted.");
    btSerial.println("ACK:OPEN");
  } else {
    // 已經在短路中，延長時間
    triggeredAt = millis();
    Serial.println("[DOOR] Already triggered — timer reset.");
  }
}