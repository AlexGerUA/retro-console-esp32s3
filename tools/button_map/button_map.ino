// ESP32_S3_Retro_Console — інтерактивне визначення розкладки кнопок.
//
// Просить натиснути кнопку за кнопкою і друкує, ЩО саме спрацювало:
//   - цифрова кнопка  -> номер GPIO
//   - вісь джойстика  -> GPIO осі + напрямок + зміряні межі ADC
//
// Наприкінці друкує зведення, з якого напряму робиться RG_GAMEPAD_GPIO_MAP
// і RG_GAMEPAD_ADC_MAP у targets/retro-console/config.h
//
// Монітор: 115200

// --- цифрові входи (8 шт) --------------------------------------------------
const int DIG[] = { 9, 10, 11, 12, 13, 14, 38, 47 };
const int NDIG  = sizeof(DIG) / sizeof(DIG[0]);

// --- осі джойстика (ADC1) --------------------------------------------------
const int JOY_X = 1;   // ADC1_CH0
const int JOY_Y = 2;   // ADC1_CH1

// відхилення від центру, за яким вважаємо що стік відхилено
const int ADC_THRESHOLD = 700;

// --- що просимо натиснути, у порядку ---------------------------------------
const char *PROMPTS[] = {
  "A", "B", "Y", "X",
  "SELECT", "MENU", "OPTIONS",
  "ВГОРУ", "ВНИЗ", "ВЛІВО", "ВПРАВО",
  "START"
};
const int NPROMPT = sizeof(PROMPTS) / sizeof(PROMPTS[0]);

// --- результати ------------------------------------------------------------
struct Result {
  bool isAdc;
  int  gpio;       // GPIO кнопки, або GPIO осі
  int  extreme;    // для ADC: досягнуте крайнє значення
  bool highSide;   // для ADC: відхилення вгору від центру?
};
Result results[NPROMPT];

int centerX = 2048, centerY = 2048;

// ---------------------------------------------------------------------------
static bool allIdle() {
  for (int i = 0; i < NDIG; i++)
    if (digitalRead(DIG[i]) == LOW) return false;
  int x = analogRead(JOY_X), y = analogRead(JOY_Y);
  if (abs(x - centerX) > ADC_THRESHOLD) return false;
  if (abs(y - centerY) > ADC_THRESHOLD) return false;
  return true;
}

static void waitIdle() {
  uint32_t stable = millis();
  while (millis() - stable < 150) {
    if (!allIdle()) stable = millis();
    delay(5);
  }
}

// чекає подію, заповнює r
static void waitEvent(Result &r) {
  for (;;) {
    // цифрові
    for (int i = 0; i < NDIG; i++) {
      if (digitalRead(DIG[i]) == LOW) {
        delay(30);                                  // антидребезг
        if (digitalRead(DIG[i]) != LOW) continue;
        r.isAdc = false; r.gpio = DIG[i];
        r.extreme = 0; r.highSide = false;
        return;
      }
    }
    // осі
    int x = analogRead(JOY_X), y = analogRead(JOY_Y);
    if (abs(x - centerX) > ADC_THRESHOLD || abs(y - centerY) > ADC_THRESHOLD) {
      bool isX = abs(x - centerX) >= abs(y - centerY);
      int  pin = isX ? JOY_X : JOY_Y;
      int  cen = isX ? centerX : centerY;
      int  ext = isX ? x : y;
      // 400мс тримаємо і ловимо крайнє значення
      uint32_t t0 = millis();
      while (millis() - t0 < 400) {
        int v = analogRead(pin);
        if (abs(v - cen) > abs(ext - cen)) ext = v;
        delay(5);
      }
      r.isAdc = true; r.gpio = pin;
      r.extreme = ext; r.highSide = (ext > cen);
      return;
    }
    delay(5);
  }
}

// ---------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(1500);

  for (int i = 0; i < NDIG; i++) pinMode(DIG[i], INPUT_PULLUP);
  analogReadResolution(12);

  Serial.println();
  Serial.println(F("################################################"));
  Serial.println(F("  RETRO CONSOLE - визначення розкладки кнопок"));
  Serial.println(F("################################################"));
  Serial.print(F("Цифрові піни: "));
  for (int i = 0; i < NDIG; i++) { Serial.print(DIG[i]); Serial.print(' '); }
  Serial.println();
  Serial.printf("Осі джойстика: X=GPIO%d  Y=GPIO%d\n", JOY_X, JOY_Y);

  // ---- калібрування центру ------------------------------------------------
  Serial.println(F("\n>>> НЕ ЧІПАЙТЕ джойстик - міряю центр..."));
  delay(1200);
  long sx = 0, sy = 0;
  for (int i = 0; i < 64; i++) { sx += analogRead(JOY_X); sy += analogRead(JOY_Y); delay(5); }
  centerX = sx / 64; centerY = sy / 64;
  Serial.printf("Центр: X=%d  Y=%d\n", centerX, centerY);

  // ---- опитування ---------------------------------------------------------
  Serial.println(F("\nНатискайте те, що просять. Одна кнопка за раз.\n"));

  for (int i = 0; i < NPROMPT; i++) {
    waitIdle();
    Serial.printf("[%2d/%d]  Натисни: %-8s ... ", i + 1, NPROMPT, PROMPTS[i]);
    Serial.flush();

    waitEvent(results[i]);

    if (results[i].isAdc) {
      Serial.printf("вісь GPIO%d, %s, крайнє=%d (центр=%d)\n",
                    results[i].gpio,
                    results[i].highSide ? "БІЛЬШЕ центру" : "МЕНШЕ центру",
                    results[i].extreme,
                    results[i].gpio == JOY_X ? centerX : centerY);
    } else {
      Serial.printf("GPIO%d\n", results[i].gpio);
    }
    delay(150);
  }

  // ---- зведення -----------------------------------------------------------
  Serial.println(F("\n\n================ ЗВЕДЕННЯ ================"));
  Serial.printf("Центр джойстика: X(GPIO%d)=%d   Y(GPIO%d)=%d\n\n",
                JOY_X, centerX, JOY_Y, centerY);
  for (int i = 0; i < NPROMPT; i++) {
    Serial.printf("%-8s -> ", PROMPTS[i]);
    if (results[i].isAdc)
      Serial.printf("ADC GPIO%d  %s  extreme=%d\n", results[i].gpio,
                    results[i].highSide ? "HIGH" : "LOW", results[i].extreme);
    else
      Serial.printf("GPIO%d\n", results[i].gpio);
  }
  Serial.println(F("=========================================="));
  Serial.println(F("Скопіюйте все зведення і надішліть."));
  Serial.println(F("RESET на платі - щоб пройти ще раз."));
}

void loop() {
  // живий моніторинг: показує будь-яке натискання, зручно для перевірки
  static uint32_t t = 0;
  if (millis() - t > 250) {
    t = millis();
    for (int i = 0; i < NDIG; i++)
      if (digitalRead(DIG[i]) == LOW) { Serial.printf("[live] GPIO%d\n", DIG[i]); delay(200); }
    int x = analogRead(JOY_X), y = analogRead(JOY_Y);
    if (abs(x - centerX) > ADC_THRESHOLD) Serial.printf("[live] X(GPIO%d)=%d\n", JOY_X, x);
    if (abs(y - centerY) > ADC_THRESHOLD) Serial.printf("[live] Y(GPIO%d)=%d\n", JOY_Y, y);
  }
}
