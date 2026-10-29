/*
 * sMove — 02-imu
 *
 * IMU bring-up firmware for smove-r2-main (ESP32-C3-MINI-1-N4, U1).
 *
 * Reads the on-board 9-axis IMU (U2, TDK InvenSense ICM-20948) over the 1.8 V
 * I2C bus behind the PCA9306 level translator and prints one line per sample on
 * the USB Serial/JTAG console, by default every 100 ms:
 *
 *   I (1234) smove-imu: #00001 | accel[g] +0.012 -0.004 +1.002 | gyro[dps] ... |
 *                      T 31.2 C | mag[uT] +21.4 -8.9 +42.0
 *
 * The LEDs show the state without a console: green = streaming, red flashing =
 * no IMU answered on the bus.
 *
 * Build / run:
 *   ./flash.sh        # build, flash, and boot the new image
 *   ./monitor.sh      # flash + stream this log (Ctrl+C to quit)
 *   IMU_SAMPLE_PERIOD_MS=20 ./flash.sh    # faster cadence (compile-time)
 */

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "driver/gpio.h"
#include "driver/i2c_master.h"
#include "esp_chip_info.h"
#include "esp_log.h"
#include "esp_system.h"

#include "icm20948.h"
#include "smove_board.h"

/* Log cadence. Override with -DIMU_SAMPLE_PERIOD_MS=<ms> (see main/CMakeLists.txt). */
#ifndef IMU_SAMPLE_PERIOD_MS
#define IMU_SAMPLE_PERIOD_MS 100
#endif

/* Consecutive read failures before the driver is detached and re-attached. */
#define IMU_MAX_CONSECUTIVE_ERRORS 10

/* One rate summary line every N samples (10 s at the default 100 ms). */
#define IMU_RATE_REPORT_SAMPLES 100

static const char *TAG = "smove-imu";

static i2c_master_bus_handle_t s_bus;

/* ------------------------------------------------------------------- LEDs */

#define LED_MASK ((1ULL << SMOVE_LED_R_GPIO) | \
                  (1ULL << SMOVE_LED_G_GPIO) | \
                  (1ULL << SMOVE_LED_B_GPIO))

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

/* -------------------------------------------------------------- I2C / IMU */

static void imu_bus_init(void)
{
    const i2c_master_bus_config_t cfg = {
        .i2c_port = I2C_NUM_0,
        .sda_io_num = SMOVE_IMU_SDA_GPIO,
        .scl_io_num = SMOVE_IMU_SCL_GPIO,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };
    ESP_ERROR_CHECK(i2c_new_master_bus(&cfg, &s_bus));
}

/*
 * Probe the two possible ICM-20948 addresses and attach to the first one that
 * answers. 0x68 is what smove-r2-main measures (AD0 low); 0x69 is kept as a
 * fallback so an alternative strap or a reworked board still reports.
 */
static bool imu_attach(icm20948_t *imu)
{
    static const uint8_t candidates[] = { SMOVE_IMU_I2C_ADDR, SMOVE_IMU_I2C_ADDR_ALT };

    for (size_t i = 0; i < sizeof candidates / sizeof candidates[0]; i++) {
        const esp_err_t probe = i2c_master_probe(s_bus, candidates[i], 50);
        ESP_LOGI(TAG, "I2C probe 0x%02x -> %s", candidates[i], esp_err_to_name(probe));
        if (probe != ESP_OK) {
            continue;
        }
        if (icm20948_init(imu, s_bus, candidates[i]) == ESP_OK) {
            return true;
        }
    }
    return false;
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

    ESP_LOGI(TAG, "boot: sMove 02-imu, ESP32-C3 rev v%d.%d, %d core(s), reset: %s",
             chip.revision / 100, chip.revision % 100, chip.cores,
             reset_reason_name(esp_reset_reason()));
    ESP_LOGI(TAG, "IMU: ICM-20948 (U2) on SDA=GPIO%d SCL=GPIO%d @ %d kHz, "
                  "one sample every %d ms",
             (int)SMOVE_IMU_SDA_GPIO, (int)SMOVE_IMU_SCL_GPIO,
             SMOVE_IMU_I2C_SPEED_HZ / 1000, IMU_SAMPLE_PERIOD_MS);
    ESP_LOGI(TAG, "accel g | gyro deg/s | die temp °C | mag µT — board axes, +Z outward");

    led_init();
    imu_bus_init();

    icm20948_t imu = { 0 };
    while (!imu_attach(&imu)) {
        ESP_LOGE(TAG, "no IMU answered — check U2, the 1V8 rail and U3; retrying in 2 s");
        led_show(SMOVE_LED_R_GPIO);
        vTaskDelay(pdMS_TO_TICKS(200));
        led_all_off();
        vTaskDelay(pdMS_TO_TICKS(1800));
    }

    /* Green = sampling; makes a headless bring-up readable at a glance. */
    led_show(SMOVE_LED_G_GPIO);

    TickType_t next_wake = xTaskGetTickCount();
    TickType_t window_start = next_wake;
    uint32_t samples = 0;
    uint32_t errors = 0;
    uint32_t consecutive_errors = 0;
    char line[192];

    while (true) {
        icm20948_sample_t s;
        const esp_err_t err = icm20948_read(&imu, &s);

        if (err == ESP_OK) {
            consecutive_errors = 0;

            snprintf(line, sizeof line,
                     "#%05u | accel[g] %+.3f %+.3f %+.3f | gyro[dps] %+.2f %+.2f %+.2f | "
                     "T %5.1f C | mag[uT] %s%+.1f %+.1f %+.1f",
                     (unsigned)(samples + 1),
                     s.accel_g[0], s.accel_g[1], s.accel_g[2],
                     s.gyro_dps[0], s.gyro_dps[1], s.gyro_dps[2],
                     s.temp_c,
                     s.mag_valid ? "" : "~",
                     s.mag_uT[0], s.mag_uT[1], s.mag_uT[2]);
            ESP_LOGI(TAG, "%s", line);
            samples++;

            if (samples % IMU_RATE_REPORT_SAMPLES == 0) {
                const TickType_t now = xTaskGetTickCount();
                const uint32_t elapsed_ms =
                    (uint32_t)((now - window_start) * portTICK_PERIOD_MS);
                const float hz = elapsed_ms ? 1000.0f * IMU_RATE_REPORT_SAMPLES / elapsed_ms : 0.0f;
                ESP_LOGI(TAG, "-- %u samples in %u ms (%.2f Hz), %u read error(s) total",
                         (unsigned)IMU_RATE_REPORT_SAMPLES, (unsigned)elapsed_ms, hz,
                         (unsigned)errors);
                window_start = now;
            }
        } else {
            errors++;
            consecutive_errors++;
            /* Rate-limit the noise: first failure and then every 5th. */
            if (consecutive_errors == 1 || consecutive_errors % 5 == 0) {
                ESP_LOGW(TAG, "read failed (%s), %u consecutive",
                         esp_err_to_name(err), (unsigned)consecutive_errors);
            }
            if (consecutive_errors >= IMU_MAX_CONSECUTIVE_ERRORS) {
                ESP_LOGW(TAG, "re-attaching the IMU after %u consecutive failures",
                         (unsigned)consecutive_errors);
                led_show(SMOVE_LED_R_GPIO);
                icm20948_deinit(&imu);
                if (imu_attach(&imu)) {
                    consecutive_errors = 0;
                    led_show(SMOVE_LED_G_GPIO);
                }
            }
        }

        vTaskDelayUntil(&next_wake, pdMS_TO_TICKS(IMU_SAMPLE_PERIOD_MS));
    }
}
