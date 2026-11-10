// ESP32_S3_Retro_Console — таргет Retro-Go
// Створено з targets/esp32-s3-devkit (те саме залізо за структурою).
// Джерело правди по пінах: ESP32_S3_Retro_Console/hardware/pins.h
//
// ПАНЕЛЬ — ST7789, а не ILI9341 (назва модуля бреше, перевірено в залізі).
// Retro-Go має один драйвер на обидва; різниця лише в RG_SCREEN_INIT():
//   - MADCTL 0x36 = 0xA8 (MY|MV|BGR) — відповідає TFT_eSPI setRotation(3);
//     devkit-івський 0x68 = rotation 1 і дає картинку догори ногами;
//   - гамма 0xE0/0xE1: СПРОБА взяти 14-параметрову версію з t-deck-plus дала
//     видимі артефакти на екрані (2026-08-22) — імовірно, зсув параметрів,
//     бо решта init-блоку (0xCF/0xED/0xE8/0xCB/0xF7/0xEA/0xC0/0xC1/0xC5/0xC7)
//     лишилась 15-параметровою, як у devkit/byteboi-rev1. Повернуто 15-парам.
//     Якщо колись знову міняти гамму — міняти РАЗОМ з усім іншим init-блоком
//     від одного й того самого таргета, а не змішувати шматки різних.
// Решту команд ST7789 ігнорує безпечно.
//
// ПОРОГИ RG_GAMEPAD_ADC_MAP зміряні на залізі (див. коментар біля мапи).
// Замінити на ЗМІРЯНІ числа зі стадії 6 hardware/BRINGUP.md, інакше
// напрямки працюватимуть неправильно. Також перевірити, чи не переплутані
// UP/DOWN та LEFT/RIGHT — знак осей залежить від орієнтації модуля.
// Target definition
#define RG_TARGET_NAME             "RETRO-CONSOLE"

// Storage
#define RG_STORAGE_ROOT             "/sd"
#define RG_STORAGE_SDSPI_HOST       SPI3_HOST
#define RG_STORAGE_SDSPI_SPEED      SDMMC_FREQ_DEFAULT
// #define RG_STORAGE_SDMMC_HOST       SDMMC_HOST_SLOT_1
// #define RG_STORAGE_SDMMC_SPEED      SDMMC_FREQ_DEFAULT
// #define RG_STORAGE_FLASH_PARTITION  "vfs"

// Audio
#define RG_AUDIO_USE_INT_DAC        0   // 0 = Disable, 1 = GPIO25, 2 = GPIO26, 3 = Both
#define RG_AUDIO_USE_EXT_DAC        1   // 0 = Disable, 1 = Enable

// Video
#define RG_SCREEN_DRIVER            0   // 0 = ILI9341/ST7789
#define RG_SCREEN_HOST              SPI2_HOST
// 26M, а не 40M: на дюпонах 40 МГц дає білий екран, тоді як тестовий скетч
// TFT_eSPI на 27 МГц з тими самими пінами працює. Підняти після переїзду на
//PCB / коротші дроти.
#define RG_SCREEN_SPEED             SPI_MASTER_FREQ_26M
#define RG_SCREEN_BACKLIGHT         1
#define RG_SCREEN_WIDTH             320
#define RG_SCREEN_HEIGHT            240
#define RG_SCREEN_ROTATE            0
#define RG_SCREEN_VISIBLE_AREA      {0, 0, 0, 0}
#define RG_SCREEN_SAFE_AREA         {0, 0, 0, 0}
// ST7789 init — ДОСЛІВНО перенесено з TFT_eSPI/TFT_Drivers/ST7789_Init.h
// (гілка #ifndef INIT_SEQUENCE_3, саме вона компілювалась у робочому скетчі).
// Попередні спроби комбінувати init-блоки з devkit/t-deck-plus/byteboi були
// приречені: ST7789 має власні регістри (0xB0/0xB2/0xB7/0xBB/0xC0/0xC2/0xC3/
// 0xC4/0xC6/0xD0), а ILI9341-послідовність шле
// 0xCF/0xED/0xE8/0xCB/0xC5/0xC7, яких ST7789 не розуміє.
//
// Драйвер Retro-Go сам робить: RESET, COLMOD 0x3A=0x55, потім цей макрос,
// потім SLPOUT(0x11) + DISPON(0x29).
//
// !!! ПОРЯДОК КОЛЬОРІВ: MADCTL = 0xA8, біт BGR (0x08) ОБОВ'ЯЗКОВИЙ (2026-08-23)
// Панель фізично BGR. Довго стояло 0xA0 (RGB), і симптом був такий: після
// зняття інверсії чорний став чорним, але цегла в іграх вийшла блакитною
// замість піщано-коричневої — тобто R і B помінялись місцями. Пурпурові
// ділянки при цьому виглядали нормально, бо magenta симетрична до заміни R<->B.
// Коментар на початку файлу весь час казав 0xA8 — розійшовся з кодом.
//
// !!! ІНВЕРСІЯ: тут 0x20 (INVOFF), а НЕ 0x21 (2026-08-23)
// Довго стояв 0x21 і здавалось, що так правильно: у лаунчері картинка
// виглядала природно. Насправді інвертована була ВСЯ панель, просто на
// темному меню це не кидається в очі. Доказ: при виході з лаунчера
// rg_system.c робить rg_display_clear(C_BLACK) (0x0000) і малює пісочний
// годинник — на фото цей екран БІЛИЙ. Чорна заливка не може віддатись білим
// інакше як через інверсію. Симптом «у меню норм, у грі інвертовано» був
// хибним слідом: ігрова графіка яскрава й контрастна, тому там негатив
// помітний одразу, а в темному меню — ні.
//
// Пауза 120 мс на початку макроса — окрема історія, НЕ фікс інверсії.
// Драйвер шле SWRESET (0x01) і чекає лише 5 мс, а ST7789 після програмного
// скидання ігнорує команди ~120 мс. Перехід лаунчер -> retro-core це
// esp_restart без знеструмлення панелі, тобто SWRESET там реально працює.
// Витримка відповідає даташиту й лишена свідомо, але інверсію вона не
// лікувала — перевірено на залізі. COLMOD дублюємо з тієї ж причини:
// драйвер відправив його у ту саму сліпу зону.

#define RG_SCREEN_INIT()                                                                                \
    rg_usleep(120 * 1000);                                                                                    \
    ILI9341_CMD(0x3A, 0x55);                                                                                  \
    ILI9341_CMD(0x13);                                                                                            \
    ILI9341_CMD(0x36, 0xA8);                                                                                  \
    ILI9341_CMD(0xB6, 0x0A, 0x82);                                                                                \
    ILI9341_CMD(0xB0, 0x00, 0xE0);                                                                                \
    ILI9341_CMD(0xB2, 0x0C, 0x0C, 0x00, 0x33, 0x33);                                                              \
    ILI9341_CMD(0xB7, 0x35);                                                                                      \
    ILI9341_CMD(0xBB, 0x28);                                                                                      \
    ILI9341_CMD(0xC0, 0x0C);                                                                                      \
    ILI9341_CMD(0xC2, 0x01, 0xFF);                                                                                \
    ILI9341_CMD(0xC3, 0x10);                                                                                      \
    ILI9341_CMD(0xC4, 0x20);                                                                                      \
    ILI9341_CMD(0xC6, 0x0F);                                                                                      \
    ILI9341_CMD(0xD0, 0xA4, 0xA1);                                                                                \
    ILI9341_CMD(0xE0, 0xD0, 0x00, 0x02, 0x07, 0x0A, 0x28, 0x32, 0x44, 0x42, 0x06, 0x0E, 0x12, 0x14, 0x17);        \
    ILI9341_CMD(0xE1, 0xD0, 0x00, 0x02, 0x07, 0x0A, 0x28, 0x31, 0x54, 0x47, 0x0E, 0x1C, 0x17, 0x1B, 0x1E);        \
    ILI9341_CMD(0x20);                                                                                        \
    rg_usleep(120 * 1000);


// Input

// Recovery — тільки по MENU. За замовчуванням RG_RECOVERY_BTN = RG_KEY_ANY,
// тобто БУДЬ-ЯКА кнопка на старті кидає в recovery-меню. З непідключеними
// (або шумними) кнопками це означає нескінченний цикл перезавантажень.
#define RG_RECOVERY_BTN             RG_KEY_MENU

// Refer to rg_input.h to see all available RG_KEY_* and RG_GAMEPAD_*_MAP types
//
// ПОРОГИ ЗМІРЯНІ НА ЗАЛІЗІ 2026-08-23 (tools/joy_calib).
// Семантика: клавіша натиснута, коли min <= raw <= max
// (rg_input.c, rg_input_read_gamepad_raw) — тому діапазони не мають
// накривати центр. Читається ОДНЕ сире зчитування за опитування, без
// усереднення, отже поріг має триматись від піків шуму, а не від середнього.
//
// Зміряно (KY-023 на 3V3, ADC1 12 біт, ATTEN_DB_11):
//   центр    X 1946..1958, Y 1953..1957 (усереднене по 64) -> беремо 1950
//   центр, поодинокі викиди сирих зчитувань: 1751..2020 (+-200 від центру)
//   повний хід обох осей: 0..4095 (упирається в обидві шини)
// Мертва зона +-500 від центру = 1450..2450: 2.5x запасу над шумом і при
// цьому лишається 74% ходу як робоча зона.
//
// ІСТОРІЯ: перша спроба мала центр 3300, бо модуль був помилково під 5 В —
// центр 2.5 В потрапляв у діапазон UP і давав випадкові натиски вгору.
// Живлення джойстика ЛИШЕ 3.3 В: під 5 В на GPIO1/2/38 йде понад 3.6 В.
//
// Полярність осей ПЕРЕВІРЕНА на залізі 2026-08-23: усі чотири напрямки
// збігаються з рухом стіка, міняти місцями нічого не треба.
//
// НЕ коментувати рядки макроса через '//': вони закінчуються на бекслеш,
// що робить коментар багаторядковим -> -Werror=comment і збірка падає.
// Пороги ЗМІРЯНІ на залізі 2026-08-23 (hardware/test/button_map).
// Центр: X(GPIO1, CH0)=1937   Y(GPIO2, CH1)=1943
// Крайні: ВГОРУ=3723  ВНИЗ=1131  ВЛІВО=3095  ВПРАВО=523
// Поріг = 45% ходу В КОЖЕН БІК ОКРЕМО — стік асиметричний (вгору 1780
// відліків, вниз лише 812), тому симетричний поріг дав би або мертву
// зону вниз, або хибні спрацювання вгору.
#define RG_GAMEPAD_ADC_MAP {\
    {RG_KEY_UP,    ADC_UNIT_1, ADC_CHANNEL_1, ADC_ATTEN_DB_11, 2750, 4095},\
    {RG_KEY_DOWN,  ADC_UNIT_1, ADC_CHANNEL_1, ADC_ATTEN_DB_11,    0, 1570},\
    {RG_KEY_LEFT,  ADC_UNIT_1, ADC_CHANNEL_0, ADC_ATTEN_DB_11, 2450, 4095},\
    {RG_KEY_RIGHT, ADC_UNIT_1, ADC_CHANNEL_0, ADC_ATTEN_DB_11,    0, 1300},\
}
// НАШІ піни (9..14). Тут довго лишались devkit-івські 16/17/18/8/15/5 —
// вони збігаються з підсвіткою, I2S та SPI дисплея, і драйвер вводу
// переконфігуровував ці піни на вхід, ламаючи дисплей. НЕ повертати!
// SW джойстика (GPIO38) = ДРУГИЙ START (2026-08-23, перевірено на залізі).
// Кнопки START/SELECT на платі ще не розпаяні, а без START нічого не
// запустити. Ідея вішати SW на quick save відпала: у Retro-Go save state
// вже є в меню по MENU. Дві мапи на один RG_KEY_ — це штатно, драйвер
// робить state |= mapping->key.
// Розкладка ЗМІРЯНА на залізі 2026-08-23, не вгадана.
// Праворуч: X Y / A B   Центр: SELECT MENU OPTIONS   Стік: напрямки + START
#define RG_GAMEPAD_GPIO_MAP {\
    {RG_KEY_A,      .num = GPIO_NUM_13, .pullup = 1, .level = 0},\
    {RG_KEY_B,      .num = GPIO_NUM_14, .pullup = 1, .level = 0},\
    {RG_KEY_X,      .num = GPIO_NUM_11, .pullup = 1, .level = 0},\
    {RG_KEY_Y,      .num = GPIO_NUM_12, .pullup = 1, .level = 0},\
    {RG_KEY_SELECT, .num = GPIO_NUM_47, .pullup = 1, .level = 0},\
    {RG_KEY_MENU,   .num = GPIO_NUM_10, .pullup = 1, .level = 0},\
    {RG_KEY_OPTION, .num = GPIO_NUM_9,  .pullup = 1, .level = 0},\
    {RG_KEY_START,  .num = GPIO_NUM_38, .pullup = 1, .level = 0},\
}

// Battery
// УВАГА (2026-08-23): дільник 100k/100k на GPIO3 ФІЗИЧНО ЩЕ НЕ ЗІБРАНИЙ.
// Пін висить у повітрі, тому індикатор заряду показує випадкове число.
// Це лише косметика: у rg_system.c батарея крутить тільки прапорець
// RG_INDICATOR_POWER_LOW, автовимкнення по низькому заряду немає.
// Після монтажу дільника перевірити RG_BATTERY_CALC_* на реальному АКБ.
#define RG_BATTERY_DRIVER           1
#define RG_BATTERY_ADC_UNIT         ADC_UNIT_1
#define RG_BATTERY_ADC_CHANNEL      ADC_CHANNEL_2   // GPIO3
#define RG_BATTERY_CALC_PERCENT(raw) (((raw) * 2.f - 3500.f) / (4200.f - 3500.f) * 100.f)
#define RG_BATTERY_CALC_VOLTAGE(raw) ((raw) * 2.f * 0.001f)


// Status LED
#define RG_GPIO_LED                 GPIO_NUM_48   // WS2812B на платі YD

// SPI Display (back up working)
#define RG_GPIO_LCD_MISO            GPIO_NUM_NC
#define RG_GPIO_LCD_MOSI            GPIO_NUM_7
#define RG_GPIO_LCD_CLK             GPIO_NUM_15
#define RG_GPIO_LCD_CS              GPIO_NUM_4
#define RG_GPIO_LCD_DC              GPIO_NUM_6
#define RG_GPIO_LCD_BCKL            GPIO_NUM_16
#define RG_GPIO_LCD_RST             GPIO_NUM_5

#define RG_GPIO_SDSPI_MISO          GPIO_NUM_41
#define RG_GPIO_SDSPI_MOSI          GPIO_NUM_40
#define RG_GPIO_SDSPI_CLK           GPIO_NUM_39
#define RG_GPIO_SDSPI_CS            GPIO_NUM_42

// External I2S DAC
#define RG_GPIO_SND_I2S_BCK         17
#define RG_GPIO_SND_I2S_WS          18
#define RG_GPIO_SND_I2S_DATA        8
// #define RG_GPIO_SND_AMP_ENABLE      18
