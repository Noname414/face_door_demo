// ============================================================
// AT_Scanner.ino — 自動偵測 HC-05 AT 模式 baud rate
// ============================================================

#include <SoftwareSerial.h>

const int EN_PIN = 2;
SoftwareSerial btSerial(5, 6);

int baudRates[] = {9600, 38400, 19200, 57600, 115200};
int currentBaud = 0;

void setup() {
  pinMode(EN_PIN, OUTPUT);
  digitalWrite(EN_PIN, HIGH);
  delay(200);
  
  Serial.begin(9600);
  Serial.println("=== HC-05 Baud Rate Scanner ===");
  Serial.println("Trying different baud rates...\n");
  
  testBaud(0);
}

void loop() {
  // 藍牙 → USB
  if (btSerial.available()) {
    while (btSerial.available()) {
      char c = btSerial.read();
      Serial.write(c);
    }
  }
  
  // USB → 藍牙
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    
    // 特殊指令：切換 baud
    if (cmd == "NEXT") {
      currentBaud++;
      if (currentBaud >= 5) currentBaud = 0;
      testBaud(currentBaud);
    } else {
      // 正常 AT 指令
      btSerial.print(cmd);
      btSerial.print("\r\n");
      Serial.print(">> ");
      Serial.println(cmd);
    }
  }
}

void testBaud(int index) {
  btSerial.end();
  delay(100);
  btSerial.begin(baudRates[index]);
  delay(100);
  
  Serial.print("Testing baud: ");
  Serial.println(baudRates[index]);
  Serial.println("Type 'AT' to test, or 'NEXT' to try next baud");
  Serial.println("─────────────────────────────────");
  
  // 自動發送測試
  btSerial.print("AT\r\n");
  delay(500);
  
  if (btSerial.available()) {
    Serial.print("✓ Response: ");
    while (btSerial.available()) {
      Serial.write(btSerial.read());
    }
    Serial.println("\n✓ This baud works! You can now send AT commands.");
  } else {
    Serial.println("✗ No response. Type 'NEXT' to try another baud.\n");
  }
}
