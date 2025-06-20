#define LEFT_VRx A0
#define LEFT_VRy A1
#define LEFT_SW 2

#define RIGHT_VRx A2
#define RIGHT_VRy A3
#define RIGHT_SW 3

void setup() {
  Serial.begin(9600);
  pinMode(LEFT_SW, INPUT_PULLUP);  // 加內部 Pull-up
  pinMode(RIGHT_SW, INPUT_PULLUP); // 加內部 Pull-up
}

void loop() {
  unsigned long currentTime = millis();

  int lx = analogRead(LEFT_VRx);
  int ly = analogRead(LEFT_VRy);
  int lsw = digitalRead(LEFT_SW);
  int rsw = digitalRead(RIGHT_SW);  // <--- 這邊是右搖桿的按鈕值

  // 方向控制 (每300ms)
  static unsigned long lastMoveTime = 0;
  if (currentTime - lastMoveTime > 300) {
    if (lx < 300) {
      Serial.println("LEFT");
      lastMoveTime = currentTime;
    } else if (lx > 700) {
      Serial.println("RIGHT");
      lastMoveTime = currentTime;
    }

    if (ly < 300) {
      Serial.println("UP");
      lastMoveTime = currentTime;
    } else if (ly > 700) {
      Serial.println("DOWN");
      lastMoveTime = currentTime;
    }
  }

  // 按鈕控制 (每500ms)
  static unsigned long lastClickTime = 0;
  if (lsw == LOW && currentTime - lastClickTime > 500) {
    Serial.println("CONFIRM");
    lastClickTime = currentTime;
  }

  if (rsw == LOW && currentTime - lastClickTime > 500) {
    Serial.println("REJECT");
    lastClickTime = currentTime;
  }
}
