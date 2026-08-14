#include <LiquidCrystal.h>

// Define Arduino pins: (RS, EN, D4, D5, D6, D7)
LiquidCrystal lcd(12, 11, 7, 6, 5, 4);

const int potPin = A0;
int current_baud = -1;

// Timeout settings
const unsigned long TIMEOUT_MS = 1500; 
unsigned long lastRxTime = 0;
bool isConnected = false;

// Refresh rate limiter for the LCD display to prevent visual flickering
unsigned long lastDisplayUpdate = 0;
const unsigned long DISPLAY_INTERVAL = 30;

void setup() {
  lcd.begin(16, 2);
  
  // Line 1: Baud rate status
  lcd.setCursor(0, 0);
  lcd.print("Baud: Starting  ");
  
  // Line 2: Initial waiting state
  lcd.setCursor(0, 1);
  lcd.print("Waiting UART... ");
}

void loop() {
  // 1. Instantly check Potentiometer
  int baud_rate = analogRead(potPin) * 20;

  if (abs(baud_rate - current_baud) > 50) {
    current_baud = baud_rate;

    Serial.end();
    Serial.begin(current_baud);
    pinMode(0, INPUT_PULLUP); 

    // Update Line 1 immediately upon turning the knob
    lcd.setCursor(0, 0);
    lcd.print("Baud: ");
    lcd.print(current_baud);
    lcd.print("        ");
  }

  // 2. Check for incoming Serial Data
  if (Serial.available() > 0) {
    String message = Serial.readStringUntil('\n');
    message.trim();

    if (message.length() > 0) {
      lastRxTime = millis();
      if (!isConnected) {
        isConnected = true;
      }

      // Throttle LCD string updates slightly if data floods in
      if (millis() - lastDisplayUpdate >= DISPLAY_INTERVAL) {
        lastDisplayUpdate = millis();
        
        String line2 = message.substring(0, min((int)message.length(), 16));
        while (line2.length() < 16) {
          line2 += " "; // Clear trailing characters
        }

        lcd.setCursor(0, 1);
        lcd.print(line2);
      }
    }
  }

  // 3. Disconnection Watchdog Check (Reverts to Setup Screen State)
  if (isConnected && (millis() - lastRxTime > TIMEOUT_MS)) {
    isConnected = false;

    lcd.setCursor(0, 1);
    lcd.print("Waiting UART... ");
  }
}