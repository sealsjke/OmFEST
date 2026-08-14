const int WINDOW_SIZE = 16;
const int SCROLL_DELAY_MS = 250;
const String flag = "OmFEST{UART_1s_C0oL}";


void setup() {
  Serial.begin(9600);
}

void loop() {
  if (flag.length() >= WINDOW_SIZE) {
    for (size_t i = 0; i <= flag.length() - WINDOW_SIZE; i++) {
      // substring(start, end) where end is exclusive
      String window = flag.substring(i, i + WINDOW_SIZE);
      Serial.println(window);
      Serial.print('\n');
      delay(SCROLL_DELAY_MS);
    }
  }
}
