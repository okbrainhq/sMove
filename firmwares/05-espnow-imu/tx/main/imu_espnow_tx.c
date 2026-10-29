/*
 * sMove — 05-espnow-imu, transmitter (sMove side)
 *
 * Reads the ICM-20948 (U2) over I2C every IMU_SAMPLE_PERIOD_MS (100 ms = 10 Hz,
 * the default) and pushes one packed frame per sample out over ESP-NOW:
 *
 *   tx (this firmware, ESP32-C3 on smove-r2-main)  --ESP-NOW-->  rx (ESP32 devkit)
 *
 * Pairing is automatic: the receiver broadcasts a HELLO once a second with its
 * own MAC; the first HELLO pins it as a unicast peer, which is what makes the
 * send callback meaningful (broadcast is always reported as "success"). If the
 * unicast path stops being acked for ~2.5 s the peer is dropped again and the
 * firmware falls back to broadcasting, so pulling the receiver out of range
 * never leaves a silently deaf link.
 *
 * Why a fixed channel instead of joining an AP: ESP-NOW rides on whatever
 * channel the interface is parked on. Both ends are unassociated STAs pinned to
 * SMOVE_ESPNOW_CHANNEL (1), with power save off so the radio is not dozing in
 * the 100 ms gaps.
 *
 * LEDs (active low, see smove_board.h):
 *   green  = streaming, paired with the receiver (unicast, ACKs arriving)
 *   blue   = streaming, nobody answered yet (broadcast in flight)
 *   red    = no IMU on the bus
 */
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "driver/gpio.h"
#include "driver/i2c_master.h"
#include "esp_chip_info.h"
#include "esp_event.h"
#include "esp_log.h"
#include "esp_mac.h"
#include "esp_netif.h"
#include "esp_now.h"
#include "esp_system.h"
#include "esp_timer.h"
#include "esp_wifi.h"
#include "nvs_flash.h"

#include "espnow_proto.h"
#include "icm20948.h"
#include "smove_board.h"

/* Sample period in ms. Override with -DIMU_SAMPLE_PERIOD_MS=<ms>
 * (main/CMakeLists.txt, or IMU_SAMPLE_PERIOD_MS=<ms> ./flash-tx.sh). */
#ifndef IMU_SAMPLE_PERIOD_MS
#define IMU_SAMPLE_PERIOD_MS 100
#endif

/* Consecutive read failures before the driver is detached and re-attached. */
#define IMU_MAX_CONSECUTIVE_ERRORS 10

/* Unacked unicast frames in a row before giving up on the paired peer. */
#define ESPNOW_FAIL_STREAK_TO_UNPAIR 25

static const char *TAG = "smove-now-tx";

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

/* Probe 0x68 (this board) then 0x69 (AD0 high / reworked board). */
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

/* -------------------------------------------------------------- ESP-NOW */

static const uint8_t k_broadcast[6] = { 0xff, 0xff, 0xff, 0xff, 0xff, 0xff };

/* Written by the Wi-Fi task (callbacks), read by the sampling loop. */
static uint8_t s_peer_mac[6];
static volatile bool s_paired;
static volatile uint32_t s_stat_sent;
static volatile uint32_t s_stat_acked;
static volatile uint32_t s_stat_nacked;
static volatile uint32_t s_stat_send_err;
static volatile uint32_t s_fail_streak;
static bool s_led_paired;

static bool peer_add(const uint8_t mac[6])
{
    esp_now_peer_info_t peer = { 0 };
    memcpy(peer.peer_addr, mac, ESP_NOW_ETH_ALEN);
    peer.channel = SMOVE_ESPNOW_CHANNEL;
    peer.ifidx = WIFI_IF_STA;
    peer.encrypt = false;

    const esp_err_t err = esp_now_add_peer(&peer);
    if (err == ESP_OK || err == ESP_ERR_ESPNOW_EXIST) {
        return true;
    }
    ESP_LOGE(TAG, "esp_now_add_peer(" MACSTR ") failed: %s",
             MAC2STR(mac), esp_err_to_name(err));
    return false;
}

/*
 * Runs in the Wi-Fi task. A broadcast send is always reported as success, so
 * only unicast results say anything about the state of the link.
 */
static void on_send_done(const esp_now_send_info_t *info, esp_now_send_status_t status)
{
    const bool unicast = info != NULL && info->des_addr != NULL &&
                         memcmp(info->des_addr, k_broadcast, ESP_NOW_ETH_ALEN) != 0;

    if (status == ESP_NOW_SEND_SUCCESS) {
        s_stat_acked++;
        if (unicast) {
            s_fail_streak = 0;
        }
        return;
    }

    s_stat_nacked++;
    if (unicast && ++s_fail_streak >= ESPNOW_FAIL_STREAK_TO_UNPAIR) {
        ESP_LOGW(TAG, "no ACK from " MACSTR " — dropping the peer, broadcasting until it says hello again",
                 MAC2STR(s_peer_mac));
        s_fail_streak = 0;
        s_paired = false;
    }
}

static void on_recv(const esp_now_recv_info_t *info, const uint8_t *data, int len)
{
    if (info == NULL || info->src_addr == NULL || len != (int)sizeof(smove_espnow_hello_t)) {
        return;
    }

    smove_espnow_hello_t hello;
    memcpy(&hello, data, sizeof hello);
    if (hello.magic != SMOVE_ESPNOW_MAGIC ||
        hello.version != SMOVE_ESPNOW_VERSION ||
        hello.type != SMOVE_ESPNOW_MSG_HELLO) {
        return;
    }

    if (s_paired && memcmp(info->src_addr, s_peer_mac, ESP_NOW_ETH_ALEN) == 0) {
        return; /* same receiver, nothing to do */
    }

    if (!peer_add(info->src_addr)) {
        return;
    }
    memcpy(s_peer_mac, info->src_addr, ESP_NOW_ETH_ALEN);
    s_fail_streak = 0;
    s_paired = true;
    ESP_LOGI(TAG, "receiver paired: " MACSTR " (up %u s), switching to unicast",
             MAC2STR(s_peer_mac), (unsigned)hello.uptime_s);
}

static void espnow_init(void)
{
    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        err = nvs_flash_init();
    }
    ESP_ERROR_CHECK(err);

    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());

    const wifi_init_config_t wifi_cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&wifi_cfg));
    ESP_ERROR_CHECK(esp_wifi_set_storage(WIFI_STORAGE_RAM));
    /* Unassociated STA: gives us the radio without touching the user's network. */
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_start());
    /* No modem sleep: the radio must stay on to catch the HELLOs and ACK. */
    ESP_ERROR_CHECK(esp_wifi_set_ps(WIFI_PS_NONE));
    ESP_ERROR_CHECK(esp_wifi_set_channel(SMOVE_ESPNOW_CHANNEL, WIFI_SECOND_CHAN_NONE));

    ESP_ERROR_CHECK(esp_now_init());
    ESP_ERROR_CHECK(esp_now_register_send_cb(on_send_done));
    ESP_ERROR_CHECK(esp_now_register_recv_cb(on_recv));

    /* Broadcast is the bootstrap path: it works before any HELLO arrives. */
    if (!peer_add(k_broadcast)) {
        ESP_LOGE(TAG, "cannot register the broadcast peer — ESP-NOW will not transmit");
    }

    uint8_t own_mac[6] = { 0 };
    esp_read_mac(own_mac, ESP_MAC_WIFI_STA);
    ESP_LOGI(TAG, "ESP-NOW up on channel %d, tx MAC " MACSTR,
             SMOVE_ESPNOW_CHANNEL, MAC2STR(own_mac));
}

/* --------------------------------------------------------------- sampling */

static void send_sample(uint16_t seq, int64_t t_us, const icm20948_sample_t *s)
{
    smove_espnow_imu_t pkt;
    memset(&pkt, 0, sizeof pkt);
    pkt.magic   = SMOVE_ESPNOW_MAGIC;
    pkt.version = SMOVE_ESPNOW_VERSION;
    pkt.type    = SMOVE_ESPNOW_MSG_IMU;
    pkt.seq     = seq;
    pkt.t_us    = (uint32_t)t_us;
    pkt.ax = s->accel_g[0];
    pkt.ay = s->accel_g[1];
    pkt.az = s->accel_g[2];
    pkt.gx = s->gyro_dps[0];
    pkt.gy = s->gyro_dps[1];
    pkt.gz = s->gyro_dps[2];

    const bool paired = s_paired;
    const uint8_t *dst = paired ? s_peer_mac : k_broadcast;

    const esp_err_t err = esp_now_send(dst, (const uint8_t *)&pkt, sizeof pkt);
    if (err == ESP_OK) {
        s_stat_sent++;
        return;
    }

    s_stat_send_err++;
    if (paired) {
        /* Never drop a sample just because the pinned peer went away. */
        esp_now_send(k_broadcast, (const uint8_t *)&pkt, sizeof pkt);
    }
}

void app_main(void)
{
    esp_chip_info_t chip = { 0 };
    esp_chip_info(&chip);

    /* Unbuffered stdout: the log lines are diagnostics, not the data path. */
    setvbuf(stdout, NULL, _IONBF, 0);

    ESP_LOGI(TAG, "boot: sMove 05-espnow-imu/tx, ESP32-C3 rev v%d.%d, %d core(s)",
             chip.revision / 100, chip.revision % 100, chip.cores);
    ESP_LOGI(TAG, "IMU: ICM-20948 (U2) on SDA=GPIO%d SCL=GPIO%d, one frame every %d ms",
             (int)SMOVE_IMU_SDA_GPIO, (int)SMOVE_IMU_SCL_GPIO, IMU_SAMPLE_PERIOD_MS);

    led_init();
    imu_bus_init();
    espnow_init();

    icm20948_t imu = { 0 };
    while (!imu_attach(&imu)) {
        ESP_LOGE(TAG, "no IMU answered — check U2, the 1V8 rail and U3; retrying in 2 s");
        led_show(SMOVE_LED_R_GPIO);
        vTaskDelay(pdMS_TO_TICKS(200));
        led_all_off();
        vTaskDelay(pdMS_TO_TICKS(1800));
    }

    /* Blue: streaming, still broadcasting because no receiver said hello. */
    led_show(SMOVE_LED_B_GPIO);
    s_led_paired = false;

    TickType_t next_wake = xTaskGetTickCount();
    const uint32_t stats_periods = (5000u / (uint32_t)IMU_SAMPLE_PERIOD_MS) ?: 1u;

    uint16_t seq = 0;
    uint32_t imu_errors = 0;
    uint32_t consecutive_errors = 0;
    uint32_t periods = 0;

    while (true) {
        icm20948_sample_t s;
        const esp_err_t err = icm20948_read(&imu, &s);

        if (err == ESP_OK) {
            consecutive_errors = 0;
            send_sample(seq++, esp_timer_get_time(), &s);
        } else {
            imu_errors++;
            consecutive_errors++;
            /* Rate-limit the noise: first failure, then every 25th. */
            if (consecutive_errors == 1 || consecutive_errors % 25 == 0) {
                ESP_LOGW(TAG, "read failed (%s), %u consecutive, %u total",
                         esp_err_to_name(err), (unsigned)consecutive_errors, (unsigned)imu_errors);
            }
            if (consecutive_errors >= IMU_MAX_CONSECUTIVE_ERRORS) {
                ESP_LOGW(TAG, "re-attaching the IMU after %u consecutive failures",
                         (unsigned)consecutive_errors);
                led_show(SMOVE_LED_R_GPIO);
                icm20948_deinit(&imu);
                if (imu_attach(&imu)) {
                    consecutive_errors = 0;
                    led_show(s_paired ? SMOVE_LED_G_GPIO : SMOVE_LED_B_GPIO);
                }
            }
        }

        /* Blue -> green the first time a receiver pairs up. */
        if (s_paired != s_led_paired) {
            s_led_paired = s_paired;
            led_show(s_led_paired ? SMOVE_LED_G_GPIO : SMOVE_LED_B_GPIO);
        }

        if (++periods >= stats_periods) {
            periods = 0;
            ESP_LOGI(TAG, "%s: %u sent, %u acked, %u nacked, %u send errors | imu errors %u",
                     s_paired ? "unicast" : "broadcast (no hello yet)",
                     (unsigned)s_stat_sent, (unsigned)s_stat_acked,
                     (unsigned)s_stat_nacked, (unsigned)s_stat_send_err,
                     (unsigned)imu_errors);
        }

        vTaskDelayUntil(&next_wake, pdMS_TO_TICKS(IMU_SAMPLE_PERIOD_MS));
    }
}
