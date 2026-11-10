/*
 * joy_calib — діагностика й калібрування джойстика KY-023
 * ESP32_S3_Retro_Console. Тимчасовий скетч, НЕ частина прошивки Retro-Go.
 *
 * Навіщо: пороги RG_GAMEPAD_ADC_MAP треба ставити за ЗМІРЯНИМИ значеннями.
 * Прошивка з розрахунковими порогами дала випадкові натиски UP — цей скетч
 * показує, чому саме.
 *
 * Піни (з hardware/pins.h):
 *   GPIO1  — VRX (ADC1_CH0)
 *   GPIO2  — VRY (ADC1_CH1)
 *   GPIO38 — SW  (не ADC, лише цифровий)
 *
 * Вивід у UART0 (GPIO43/44) -> порт CH343. Тому в налаштуваннях плати
 * "USB CDC On Boot" має бути DISABLED, а USB-кабель — у порт UART, не native.
 *
 * ЩО ЧИТАТИ У ВИВОДІ
 *   1. Центри X і Y мають бути ОДНАКОВІ (~2000-2200 raw, ~1.65 В).
 *      Якщо центр Y помітно вищий за центр X — щось підтягує VRY до плюса.
 *   2. pp (peak-to-peak) — розмах шуму. Норма для короткого дроту < 50.
 *      Сотні означають наводку або холодну пайку.
 *   3. WIRE TEST — чи взагалі підключений дріт осі.
 */

#include <Arduino.h>

static const int PIN_VRX = 1;
static const int PIN_VRY = 2;
static const int PIN_SW  = 38;

static const int SAMPLES     = 64;    // усереднення на один рядок
static const int PRINT_MS    = 250;   // період друку

struct AxisStat {
  int last, mn, mx, avg;
};

static AxisStat statX, statY;
static bool haveRange = false;

static void resetRange() {
  statX.mn = statY.mn = 4095;
  statX.mx = statY.mx = 0;
  haveRange = false;
}

static void sampleAxis(int pin, AxisStat *st) {
  long sum = 0;
  int mn = 4095, mx = 0;
  for (int i = 0; i < SAMPLES; ++i) {
    int v = analogRead(pin);
    sum += v;
    if (v < mn) mn = v;
    if (v > mx) mx = v;
    delayMicroseconds(50);
  }
  st->last = mx;              // не використовується, лишено для ясності
  st->avg  = (int)(sum / SAMPLES);
  st->last = st->avg;
  if (mn < st->mn) st->mn = mn;
  if (mx > st->mx) st->mx = mx;
}

/*
 * Тест обриву дроту / відсутності живлення модуля.
 *
 * ВАЖЛИВО: тут НЕ можна користуватись analogRead(). У ядрі ESP32-Arduino
 * analogRead() перечіпляє пін на АЦП і при цьому ЗНІМАЄ внутрішні підтяжки,
 * тому "виміряти з підтяжкою" через АЦП неможливо — вийдуть нулі незалежно
 * від того, що на піні. Перша версія цього тесту саме так і збрехала.
 * Тому тест суто цифровий.
 *
 * Логіка: вихідний опір потенціометра 10 кОм у центрі ~2.5 кОм. Внутрішня
 * підтяжка ~45 кОм проти нього безсила — пін лишиться там, де його тримає
 * потенціометр. Якщо ж пін іде за внутрішньою підтяжкою (вгору з pullup,
 * вниз з pulldown) — значить ззовні його ніщо не тримає.
 */
static void wireTest(int pin, const char *name) {
  pinMode(pin, INPUT_PULLUP);
  delay(20);
  int up = digitalRead(pin);
  pinMode(pin, INPUT_PULLDOWN);
  delay(20);
  int dn = digitalRead(pin);
  pinMode(pin, INPUT);
  delay(20);

  Serial.printf("  %s: pullup=%d pulldown=%d -> ", name, up, dn);
  if (up == 1 && dn == 0)
    Serial.println("ВІЛЬНИЙ (обрив дроту АБО модуль без живлення)");
  else
    Serial.println("утримується ззовні -> потенціометр підключений і живиться");
}

static void swTest() {
  /*
   * Зовнішня підтяжка є? Вмикаємо внутрішній PULLDOWN (~45 кОм).
   * Якщо ззовні висить 10 кОм на 3.3 В — дільник 10к/45к дасть ~2.7 В,
   * тобто лишиться HIGH. Якщо зовнішньої підтяжки нема — впаде в LOW.
   */
  pinMode(PIN_SW, INPUT_PULLDOWN);
  delay(20);
  int withPulldown = digitalRead(PIN_SW);

  pinMode(PIN_SW, INPUT);
  delay(20);
  int floating = digitalRead(PIN_SW);

  Serial.printf("  SW: float=%d, з внутр. pulldown=%d -> ", floating, withPulldown);
  if (withPulldown == HIGH) Serial.println("зовнішня підтяжка Є (резистор працює)");
  else Serial.println("зовнішньої підтяжки НЕМА (або вона не на 3.3 В)");

  pinMode(PIN_SW, INPUT_PULLUP);
}

void setup() {
  Serial.begin(115200);
  delay(1500);

  analogReadResolution(12);
  analogSetPinAttenuation(PIN_VRX, ADC_11db);
  analogSetPinAttenuation(PIN_VRY, ADC_11db);

  Serial.println();
  Serial.println("=== joy_calib: KY-023 на ESP32-S3 ===");
  Serial.println("VRX=GPIO1 (ADC1_CH0), VRY=GPIO2 (ADC1_CH1), SW=GPIO38");
  Serial.println();
  Serial.println("--- WIRE TEST (не чіпай джойстик) ---");
  wireTest(PIN_VRX, "VRX");
  wireTest(PIN_VRY, "VRY");
  swTest();

  analogSetPinAttenuation(PIN_VRX, ADC_11db);
  analogSetPinAttenuation(PIN_VRY, ADC_11db);

  Serial.println();
  Serial.println("--- ЖИВІ ЗНАЧЕННЯ ---");
  Serial.println("Крок 1: НЕ ЧІПАЙ джойстик ~10 с (міряємо центр і шум).");
  Serial.println("Крок 2: повільно обведи стіком по колу до упору, кілька разів.");
  Serial.println("Крок 3: відпусти. min/max покажуть повний хід осей.");
  Serial.println("Будь-який символ у порт = скинути min/max.");
  Serial.println();

  resetRange();
}

void loop() {
  static uint32_t nextPrint = 0;

  if (Serial.available()) {
    while (Serial.available()) Serial.read();
    resetRange();
    Serial.println(">>> min/max скинуто");
  }

  sampleAxis(PIN_VRX, &statX);
  sampleAxis(PIN_VRY, &statY);

  if (millis() >= nextPrint) {
    nextPrint = millis() + PRINT_MS;

    int mvX = analogReadMilliVolts(PIN_VRX);
    int mvY = analogReadMilliVolts(PIN_VRY);
    int sw  = digitalRead(PIN_SW);

    Serial.printf("X raw=%4d (%4d mV) min=%4d max=%4d pp=%4d | "
                  "Y raw=%4d (%4d mV) min=%4d max=%4d pp=%4d | SW=%d",
                  statX.avg, mvX, statX.mn, statX.mx, statX.mx - statX.mn,
                  statY.avg, mvY, statY.mn, statY.mx, statY.mx - statY.mn,
                  sw);
    Serial.println();

    if (statX.avg == 0 && statY.avg == 0) {
      Serial.println("  ^^^ ОБИДВІ осі рівно 0 В. Потенціометри не живляться:");
      Serial.println("      перевір дріт VCC модуля (має бути 3.3 В) і GND.");
    }
  }
}
