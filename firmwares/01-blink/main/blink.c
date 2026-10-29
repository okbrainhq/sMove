/*
 * sMove — 01-blink
 *
 * Minimal bring-up firmware for smove-r2-main (ESP32-C3-MINI-1-N4, U1).
 * Blinks the on-board common-anode RGB LED (D1, LiteOn LTST-C19HE1WT) through
 * the 1k series resistors R11/R12/R13 on GPIO3 (red), GPIO7 (green) and
 * GPIO10 (blue). The LED is wired anode-to-3V3, so the pins sink current and
 * a LOW level lights the colour (see main/smove_board.h).
 *
 * Everything the loop does is logged over the USB Serial/JTAG console, so the
 * blink can be followed from `./monitor.sh` without looking at the board.
 *
 * Build / run:
 *   ./flash.sh        # build, flash, and boot the new image
 *   ./monitor.sh      # flash + stream this log (Ctrl+C to quit)
 */

#include <stdbool.h>
#include <stdint.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "driver/gpio.h"
#include "esp_chip_info.h"
#include "esp_log.h"
#include "esp_system.h"

#include "smove_board.h"

/* Half period of the blink, i.e. the LED is on for this long and off for the
 * same time. Override with -DBLINK_HALF_PERIOD_MS=<ms> if needed. */
#ifndef BLINK_HALF_PERIOD_MS
#define BLINK_HALF_PERIOD_MS 500
#endif

/* Keep the blink gentle: 1k series resistors give ~1 mA per colour at 3.3 V. */
#define LED_MASK ((1ULL << SMOVE_LED_R_GPIO) | \
                  (1ULL << SMOVE_LED_G_GPIO) | \
                  (1ULL << SMOVE_LED_B_GPIO))

static const char *TAG = "smove-blink";

typedef struct {
    gpio_num_t pin;
    const char *name;
} led_colour_t;

static const led_colour_t s_colours[] = {
    { SMOVE_LED_R_GPIO, "red" },
    { SMOVE_LED_G_GPIO, "green" },
    { SMOVE_LED_B_GPIO, "blue" },
};

#define COLOUR_COUNT (sizeof(s_colours) / sizeof(s_colours[0]))

/* Turn every colour off (the LED is off when all cathodes are HIGH). */
static void led_all_off(void)
{
    gpio_set_level(SMOVE_LED_R_GPIO, SMOVE_LED_OFF_LEVEL);
    gpio_set_level(SMOVE_LED_G_GPIO, SMOVE_LED_OFF_LEVEL);
    gpio_set_level(SMOVE_LED_B_GPIO, SMOVE_LED_OFF_LEVEL);
}

/* Light exactly one colour, or none when pin == GPIO_NUM_NC. */
static void led_show(gpio_num_t pin)
{
    led_all_off();
    if (pin != GPIO_NUM_NC) {
        gpio_set_level(pin, SMOVE_LED_ON_LEVEL);
    }
}

static void led_init(void)
{
    const gpio_config_t cfg = {
        .pin_bit_mask = LED_MASK,
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    ESP_ERROR_CHECK(gpio_config(&cfg));
    led_all_off();
}

/* Human-readable reset cause, so a stale `boot:0x7 DOWNLOAD` session or a panic
 * is obvious in the log. */
static const char *reset_reason_name(esp_reset_reason_t reason)
{
    switch (reason) {
    case ESP_RST_POWERON:  return "power-on";
    case ESP_RST_EXT:      return "external pin";
    case ESP_RST_SW:       return "software";
    case ESP_RST_PANIC:    return "panic";
    case ESP_RST_INT_WDT:  return "interrupt watchdog";
    case ESP_RST_TASK_WDT: return "task watchdog";
    case ESP_RST_WDT:      return "other watchdog";
    case ESP_RST_DEEPSLEEP:return "deep sleep wake";
    case ESP_RST_BROWNOUT: return "brownout";
    case ESP_RST_SDIO:     return "SDIO";
    case ESP_RST_USB:      return "USB peripheral";
    default:               return "unknown";
    }
}

void app_main(void)
{
    esp_chip_info_t chip = { 0 };
    esp_chip_info(&chip);

    ESP_LOGI(TAG, "boot: sMove 01-blink, ESP32-C3 rev v%d.%d, %d core(s), reset: %s",
             chip.revision / 100, chip.revision % 100, chip.cores,
             reset_reason_name(esp_reset_reason()));
    ESP_LOGI(TAG, "LED: red=GPIO%d green=GPIO%d blue=GPIO%d (common anode, "
                  "active low), %d ms on / %d ms off per colour",
             (int)SMOVE_LED_R_GPIO, (int)SMOVE_LED_G_GPIO, (int)SMOVE_LED_B_GPIO,
             BLINK_HALF_PERIOD_MS, BLINK_HALF_PERIOD_MS);

    led_init();

    uint32_t cycle = 1;
    size_t next = 0;
    while (true) {
        const led_colour_t *c = &s_colours[next];

        ESP_LOGI(TAG, "cycle %u: %s on", (unsigned)cycle, c->name);
        led_show(c->pin);
        vTaskDelay(pdMS_TO_TICKS(BLINK_HALF_PERIOD_MS));

        ESP_LOGD(TAG, "cycle %u: %s off", (unsigned)cycle, c->name);
        led_show(GPIO_NUM_NC);
        vTaskDelay(pdMS_TO_TICKS(BLINK_HALF_PERIOD_MS));

        next = (next + 1) % COLOUR_COUNT;
        if (next == 0) {
            ESP_LOGI(TAG, "cycle %u complete (red -> green -> blue)", (unsigned)cycle);
            cycle++;
        }
    }
}
