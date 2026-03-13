/*
  Sign to Speech Sender (Arduino + 5 Flex Sensors)

  Uses 5 flex sensors and sends gesture IDs (0-9) over Serial at 9600 baud
  based on finger-combination bitmasks.

  Each loop:
    - Reads 5 analog flex sensors
    - Converts each to bent(1)/straight(0) using threshold
    - Builds a 5-bit mask (thumb->bit0 ... pinky->bit4)
    - Debounces stable masks
    - Sends mapped gesture ID when a known combination is detected

  Update thresholds/invert flags per your hardware calibration.
*/

const int FLEX_PINS[5] = {A0, A1, A2, A3, A4};

// Tune per sensor after checking Serial Plotter values.
int FLEX_THRESHOLD[5] = {620, 620, 620, 620, 620};

// If a sensor reads lower when bent, set corresponding entry to true.
bool INVERT_BENT_LOGIC[5] = {false, false, false, false, false};

const unsigned long STABLE_DEBOUNCE_MS = 120;

uint8_t lastRawMask = 0;
uint8_t stableMask = 0;
int lastGesture = -1;
unsigned long lastChangeMs = 0;

bool isFingerBent(int fingerIndex, int rawValue) {
  bool bent = rawValue >= FLEX_THRESHOLD[fingerIndex];
  if (INVERT_BENT_LOGIC[fingerIndex]) {
    bent = !bent;
  }
  return bent;
}

uint8_t readFingerMask() {
  uint8_t mask = 0;
  for (int i = 0; i < 5; i++) {
    int rawValue = analogRead(FLEX_PINS[i]);
    if (isFingerBent(i, rawValue)) {
      mask |= (1 << i);
    }
  }
  return mask;
}

int gestureFromMask(uint8_t mask) {
  // 5-finger combinations mapped to gesture IDs 0..9
  // You can change these combinations to match your glove training.
  switch (mask) {
    case 0b00001: return 0;  // Thumb
    case 0b00010: return 1;  // Index
    case 0b00100: return 2;  // Middle
    case 0b01000: return 3;  // Ring
    case 0b10000: return 4;  // Pinky
    case 0b00011: return 5;  // Thumb + Index
    case 0b00110: return 6;  // Index + Middle
    case 0b01100: return 7;  // Middle + Ring
    case 0b11000: return 8;  // Ring + Pinky
    case 0b11111: return 9;  // All fingers bent
    default: return -1;      // Unknown / not mapped
  }
}

void setup() {
  Serial.begin(9600);
  delay(500);

  lastRawMask = readFingerMask();
  stableMask = lastRawMask;
  lastChangeMs = millis();

  Serial.println("Arduino Flex Sign Sender Ready");
}

void loop() {
  uint8_t currentMask = readFingerMask();

  if (currentMask != lastRawMask) {
    lastRawMask = currentMask;
    lastChangeMs = millis();
  }

  if ((millis() - lastChangeMs) >= STABLE_DEBOUNCE_MS && stableMask != currentMask) {
    stableMask = currentMask;

    int gesture = gestureFromMask(stableMask);
    if (gesture >= 0 && gesture != lastGesture) {
      Serial.println(gesture);
      lastGesture = gesture;
    }

    // Allow repeat of same gesture after hand returns to unknown or neutral shape.
    if (gesture < 0) {
      lastGesture = -1;
    }
  }
}
