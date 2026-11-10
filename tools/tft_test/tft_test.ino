// ESP32_S3_Retro_Console — діагностичний скетч дисплея
// Піни — з ../../pins.h (дублюються тут навмисно: скетч має бути самодостатнім
// і компілюватись без решти проєкту).
//
// Порядок такий, щоб кожен крок відповідав на одне питання:
//   1. Підсвітка як ЗВИЧАЙНИЙ GPIO (без LEDC) — чи доходить GPIO16 до LED
//   2. Ручне смикання RST/CS/DC       — чи живі керуючі лінії
//   3. TFT_eSPI: заливки й текст      — чи говорить контролер по SPI

#include <TFT_eSPI.h>

#define PIN_LCD_CS    4
#define PIN_LCD_RST   5
#define PIN_LCD_DC    6
#define PIN_LCD_MOSI  7
#define PIN_LCD_SCK  15
#define PIN_LCD_BL   16

TFT_eSPI tft = TFT_eSPI();

static void banner(const char *s) {
  Serial.println();
  Serial.print(F("=== ")); Serial.print(s); Serial.println(F(" ==="));
}

void setup() {
  Serial.begin(115200);
  delay(1500);                       // час на відкриття монітора

  Serial.println();
  Serial.println(F("################################################"));
  Serial.println(F("  ESP32_S3_Retro_Console - TFT diagnostic"));
  Serial.println(F("################################################"));
  Serial.printf("PSRAM: %u bytes\n", (unsigned)ESP.getPsramSize());
  Serial.printf("Flash: %u bytes\n", (unsigned)ESP.getFlashChipSize());
  Serial.printf("Pins: CS=%d RST=%d DC=%d MOSI=%d SCK=%d BL=%d\n",
                PIN_LCD_CS, PIN_LCD_RST, PIN_LCD_DC,
                PIN_LCD_MOSI, PIN_LCD_SCK, PIN_LCD_BL);

  // ---- КРОК 1: підсвітка звичайним GPIO, без LEDC ------------------------
  banner("STEP 1: backlight on GPIO16 (plain digital, no LEDC)");
  pinMode(PIN_LCD_BL, OUTPUT);
  for (int i = 0; i < 3; i++) {
    digitalWrite(PIN_LCD_BL, HIGH);
    Serial.println(F("  BL = HIGH  (має світитись)"));
    delay(700);
    digitalWrite(PIN_LCD_BL, LOW);
    Serial.println(F("  BL = LOW   (має гаснути)"));
    delay(700);
  }
  digitalWrite(PIN_LCD_BL, HIGH);
  Serial.println(F("  BL лишено HIGH"));
  Serial.println(F("  >> Якщо блимання НЕ видно - дріт LED не доходить до GPIO16."));

  // ---- КРОК 2: керуючі лінії ---------------------------------------------
  banner("STEP 2: control lines toggle");
  pinMode(PIN_LCD_RST, OUTPUT);
  pinMode(PIN_LCD_CS, OUTPUT);
  pinMode(PIN_LCD_DC, OUTPUT);
  digitalWrite(PIN_LCD_CS, HIGH);
  digitalWrite(PIN_LCD_DC, HIGH);
  digitalWrite(PIN_LCD_RST, LOW);  delay(50);
  digitalWrite(PIN_LCD_RST, HIGH); delay(150);
  Serial.println(F("  RST: LOW 50ms -> HIGH. CS=HIGH, DC=HIGH."));
  Serial.println(F("  >> Зміряйте зараз: RST і CS на модулі мають бути ~3.3V."));

  // ---- КРОК 3: TFT_eSPI ---------------------------------------------------
  banner("STEP 3: TFT_eSPI init");
  tft.init();
  tft.setRotation(3);              // ландшафт 320x240, повернуто на 180
  Serial.printf("  tft.width()=%d  tft.height()=%d\n", tft.width(), tft.height());

  banner("STEP 4: colour fills");
  const uint16_t cols[] = {TFT_RED, TFT_GREEN, TFT_BLUE, TFT_WHITE, TFT_BLACK};
  const char *names[]   = {"RED", "GREEN", "BLUE", "WHITE", "BLACK"};
  for (int i = 0; i < 5; i++) {
    tft.fillScreen(cols[i]);
    Serial.print(F("  fill ")); Serial.println(names[i]);
    delay(800);
  }

  banner("STEP 5: pattern + text");
  tft.fillScreen(TFT_BLACK);
  // рамка по краю - одразу видно, чи правильні межі й орієнтація
  tft.drawRect(0, 0, tft.width(), tft.height(), TFT_YELLOW);
  tft.drawRect(1, 1, tft.width() - 2, tft.height() - 2, TFT_YELLOW);
  // кольорові смуги
  int bw = tft.width() / 8;
  uint16_t bars[] = {TFT_RED, TFT_GREEN, TFT_BLUE, TFT_CYAN,
                     TFT_MAGENTA, TFT_YELLOW, TFT_WHITE, TFT_DARKGREY};
  for (int i = 0; i < 8; i++)
    tft.fillRect(i * bw, 40, bw, 60, bars[i]);

  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.setTextDatum(TL_DATUM);
  tft.drawString("RETRO CONSOLE", 10, 10, 4);
  tft.drawString("TFT test OK", 10, 115, 2);
  tft.drawString("320x240 landscape", 10, 140, 2);

  Serial.println(F("  Готово. Якщо бачите рамку, смуги й текст - дисплей живий."));
  Serial.println(F("  Якщо кольори неправильні - міняти TFT_RGB_ORDER / INVERSION."));
}

void loop() {
  // Повільний пульс підсвітки: якщо картинка є, а пульсу немає,
  // значить GPIO16 не керує LED (дріт кинутий напряму на 3V3).
  static uint32_t t = 0;
  static bool on = true;
  if (millis() - t > 3000) {
    t = millis();
    on = !on;
    digitalWrite(PIN_LCD_BL, on ? HIGH : LOW);
    Serial.print(F("BL -> ")); Serial.println(on ? F("HIGH") : F("LOW"));
  }
}
