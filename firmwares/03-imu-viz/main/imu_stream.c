/*
 * sMove — 03-imu-viz
 *
 * IMU streaming firmware for smove-r2-main (ESP32-C3-MINI-1-N4, U1).
 *
 * Same sensor path as 02-imu (U2, TDK InvenSense ICM-20948 behind the PCA9306),
 * but this build is a *data source* for `viz.sh`: it prints accel + gyro only,
 * as one compact machine-readable line per sample, without the ESP-IDF log
 * prefix so the host bridge can parse it with a trivial split:
 *
 *   C,20                                   <- config: sample period, milliseconds
 *   S,123456,-0.912,-0.211,+0.392,+0.05,+6.20,-3.02
 *     ^      ^                       ^
 *     |      accel X Y Z [g]         gyro X Y Z [deg/s]
 *     +-- board uptime in microseconds (esp_timer, monotonic)
 *
 * Everything else (temperature, magnetometer) is deliberately dropped: the web
 * view only needs the 6-axis stream, and a shorter line leaves more bandwidth
 * for a faster cadence (20 ms = 50 Hz by default).
 *
 * The LEDs still show the state without the web app: green = streaming,
 * red flashing = no IMU answered on the bus.
 *
 * Build / run:
 *   ./viz.sh              # flash + serve the 3D view on http://localhost:3000
 *   ./flash.sh            # build, flash, boot the new image (no web app)
 *   IMU_SAMPLE_PERIOD_MS=10 ./viz.sh     # faster cadence (compile-time)
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
#include "esp_timer.h"

#include "icm20948.h"
#include "smove_board.h"

/* Sample period in ms. Override with -DIMU_SAMPLE_PERIOD_MS=<ms> (main/CMakeLists.txt). */
#ifndef IMU_SAMPLE_PERIOD_MS
#define IMU_SAMPLE_PERIOD_MS 20
#endif

/* Consecutive read failures before the driver is detached and re-attached. */
#define IMU_MAX_CONSECUTIVE_ERRORS 20

static const char *TAG = "smove-viz";

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
 * answers (0x68 measured on this board, 0x69 as the AD0-high fallback).
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

/* One data line, written in a single fwrite so the host never sees half a
 * sample even if the reader is slow. */
static void emit_sample(int64_t t_us, const icm20948_sample_t *s)
{
    char line[112];
    const int n = snprintf(line, sizeof line,
                           "S,%lld,%.3f,%.3f,%.3f,%.2f,%.2f,%.2f\n",
                           (long long)t_us,
                           (double)s->accel_g[0], (double)s->accel_g[1], (double)s->accel_g[2],
                           (double)s->gyro_dps[0], (double)s->gyro_dps[1], (double)s->gyro_dps[2]);
    if (n > 0) {
        fwrite(line, 1, (size_t)n, stdout);
        fflush(stdout);
    }
}

void app_main(void)
{
    esp_chip_info_t chip = { 0 };
    esp_chip_info(&chip);

    /* Sampled at 50 Hz: an unbuffered stdout keeps latency at one sample instead
     * of one stdio block. */
    setvbuf(stdout, NULL, _IONBF, 0);

    ESP_LOGI(TAG, "boot: sMove 03-imu-viz, ESP32-C3 rev v%d.%d, %d core(s), reset: %s",
             chip.revision / 100, chip.revision % 100, chip.cores,
             reset_reason_name(esp_reset_reason()));
    ESP_LOGI(TAG, "IMU: ICM-20948 (U2) on SDA=GPIO%d SCL=GPIO%d @ %d kHz, "
                  "accel+gyro every %d ms",
             (int)SMOVE_IMU_SDA_GPIO, (int)SMOVE_IMU_SCL_GPIO,
             SMOVE_IMU_I2C_SPEED_HZ / 1000, IMU_SAMPLE_PERIOD_MS);

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

    /* Green = sampling. */
    led_show(SMOVE_LED_G_GPIO);

    /* Config line: the host bridge uses it for the sample-rate readout. */
    printf("C,%d\n", IMU_SAMPLE_PERIOD_MS);
    fflush(stdout);

    TickType_t next_wake = xTaskGetTickCount();
    uint32_t errors = 0;
    uint32_t consecutive_errors = 0;

    while (true) {
        icm20948_sample_t s;
        const esp_err_t err = icm20948_read(&imu, &s);

        if (err == ESP_OK) {
            consecutive_errors = 0;
            emit_sample(esp_timer_get_time(), &s);
        } else {
            errors++;
            consecutive_errors++;
            /* Rate-limit the noise: first failure, then every 25th. */
            if (consecutive_errors == 1 || consecutive_errors % 25 == 0) {
                ESP_LOGW(TAG, "read failed (%s), %u consecutive, %u total",
                         esp_err_to_name(err), (unsigned)consecutive_errors,
                         (unsigned)errors);
            }
            if (consecutive_errors >= IMU_MAX_CONSECUTIVE_ERRORS) {
                ESP_LOGW(TAG, "re-attaching the IMU after %u consecutive failures",
                         (unsigned)consecutive_errors);
                led_show(SMOVE_LED_R_GPIO);
                icm20948_deinit(&imu);
                if (imu_attach(&imu)) {
                    consecutive_errors = 0;
                    led_show(SMOVE_LED_G_GPIO);
                    printf("C,%d\n", IMU_SAMPLE_PERIOD_MS);
                    fflush(stdout);
                }
            }
        }

        vTaskDelayUntil(&next_wake, pdMS_TO_TICKS(IMU_SAMPLE_PERIOD_MS));
    }
}
