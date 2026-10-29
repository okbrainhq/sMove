/*
 * sMove — 05-espnow-imu, receiver (the "other ESP32" on the bench)
 *
 * Listens on SMOVE_ESPNOW_CHANNEL for the sMove transmitter, and relays every
 * IMU frame to the PC as one machine-readable line on the UART console
 * (/dev/ttyUSB0 through the on-board CP210x bridge, 115200 8N1):
 *
 *   # sMove ESP-NOW IMU receiver — MAC a4:f0:0f:53:40:78, channel 1
 *   S,<seq>,<tx_us>,<rx_us>,<ax>,<ay>,<az>,<gx>,<gy>,<gz>,<rssi>
 *   T,<rssi>,<received>,<lost>,<age_ms>
 *
 *   S  one per IMU frame (10 Hz by default)
 *      seq    sender's sample counter (gaps = frames lost in the air)
 *      tx_us  sender esp_timer_get_time() at sampling, µs
 *      rx_us  this chip's esp_timer at reception, µs — different epoch, so only
 *             rx_us - tx_us *differences* are meaningful (host/espnow_monitor.py
 *             uses the running minimum as the offset and shows the jitter)
 *      rssi   dBm of the received frame
 *   T  once a second: link summary, so a stalled stream is obvious even with
 *      `cat /dev/ttyUSB0` and no host tool
 *
 * The HELLO task advertises this board's MAC once a second so the transmitter
 * can switch from broadcast to unicast without either side hard-coding an
 * address — swap the bench board and the link re-pairs by itself.
 *
 * Nothing is printed from the Wi-Fi callback: frames are queued and formatted
 * in a normal task, so a slow console can never stall the radio.
 */
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/task.h"

#include "esp_event.h"
#include "esp_log.h"
#include "esp_mac.h"
#include "esp_netif.h"
#include "esp_now.h"
#include "esp_timer.h"
#include "esp_wifi.h"
#include "nvs_flash.h"

#include "espnow_proto.h"

static const char *TAG = "smove-now-rx";

#define ESPNOW_QUEUE_LEN     8      /* ~0.8 s of frames at 10 Hz */
#define ESPNOW_HELLO_MS      1000   /* pairing beacon cadence */

static const uint8_t k_broadcast[6] = { 0xff, 0xff, 0xff, 0xff, 0xff, 0xff };

typedef struct {
    smove_espnow_imu_t pkt;
    uint8_t src[6];
    int8_t rssi;
    int64_t rx_us;
} rx_item_t;

static QueueHandle_t s_queue;

/* ---------------------------------------------------------------- receive */

static void on_recv(const esp_now_recv_info_t *info, const uint8_t *data, int len)
{
    if (info == NULL || data == NULL || len != (int)sizeof(smove_espnow_imu_t)) {
        return;
    }

    rx_item_t item;
    memcpy(&item.pkt, data, sizeof item.pkt);
    if (item.pkt.magic != SMOVE_ESPNOW_MAGIC ||
        item.pkt.version != SMOVE_ESPNOW_VERSION ||
        item.pkt.type != SMOVE_ESPNOW_MSG_IMU) {
        return;
    }

    memcpy(item.src, info->src_addr, ESP_NOW_ETH_ALEN);
    item.rssi = info->rx_ctrl ? (int8_t)info->rx_ctrl->rssi : 0;
    item.rx_us = esp_timer_get_time();

    /* Never block the Wi-Fi task: on overflow the frame is simply dropped and
     * shows up as a sequence gap on the PC side, which is the truth anyway. */
    (void)xQueueSend(s_queue, &item, 0);
}

/* -------------------------------------------------------------- ESP-NOW init */

static bool peer_add_broadcast(void)
{
    esp_now_peer_info_t peer = { 0 };
    memcpy(peer.peer_addr, k_broadcast, ESP_NOW_ETH_ALEN);
    peer.channel = SMOVE_ESPNOW_CHANNEL;
    peer.ifidx = WIFI_IF_STA;
    peer.encrypt = false;

    const esp_err_t err = esp_now_add_peer(&peer);
    return err == ESP_OK || err == ESP_ERR_ESPNOW_EXIST;
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
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_start());
    /* The receiver must never be dozing when a frame lands. */
    ESP_ERROR_CHECK(esp_wifi_set_ps(WIFI_PS_NONE));
    ESP_ERROR_CHECK(esp_wifi_set_channel(SMOVE_ESPNOW_CHANNEL, WIFI_SECOND_CHAN_NONE));

    ESP_ERROR_CHECK(esp_now_init());
    ESP_ERROR_CHECK(esp_now_register_recv_cb(on_recv));

    if (!peer_add_broadcast()) {
        ESP_LOGE(TAG, "cannot register the broadcast peer — HELLO beacons will not go out");
    }
}

/* ------------------------------------------------------------------ tasks */

/* Advertise our MAC so the transmitter can unicast to us. */
static void hello_task(void *arg)
{
    (void)arg;

    while (true) {
        const smove_espnow_hello_t out = {
            .magic     = SMOVE_ESPNOW_MAGIC,
            .version   = SMOVE_ESPNOW_VERSION,
            .type      = SMOVE_ESPNOW_MSG_HELLO,
            .period_ms = 0, /* the receiver does not know the tx cadence */
            .uptime_s  = (uint32_t)(esp_timer_get_time() / 1000000),
        };
        const esp_err_t err = esp_now_send(k_broadcast, (const uint8_t *)&out, sizeof out);
        if (err != ESP_OK) {
            ESP_LOGW(TAG, "hello send failed: %s", esp_err_to_name(err));
        }
        vTaskDelay(pdMS_TO_TICKS(ESPNOW_HELLO_MS));
    }
}

/*
 * Formatting + link statistics live here, single-threaded: one task owns
 * stdout, so lines never interleave.
 */
static void printer_task(void *arg)
{
    (void)arg;

    uint16_t last_seq = 0;
    bool have_last = false;
    uint32_t received = 0;
    uint32_t lost = 0;
    uint32_t dup_or_reorder = 0;
    bool announced = false;

    int8_t last_rssi = 0;
    int64_t last_rx_us = 0;
    char last_src[18] = "-";

    int64_t next_report_us = esp_timer_get_time() + 1000000;

    while (true) {
        rx_item_t item;
        if (xQueueReceive(s_queue, &item, pdMS_TO_TICKS(100)) == pdTRUE) {
            const uint16_t seq = item.pkt.seq;

            if (!have_last) {
                have_last = true;
            } else {
                const uint16_t delta = (uint16_t)(seq - last_seq);
                if (delta == 1) {
                    /* in order */
                } else if (delta == 0) {
                    dup_or_reorder++; /* retransmit / duplicate frame */
                } else if (delta < 0x8000) {
                    lost += (uint32_t)(delta - 1); /* forward gap */
                } else {
                    dup_or_reorder++; /* late frame */
                }
            }
            last_seq = seq;

            received++;
            last_rssi = item.rssi;
            last_rx_us = item.rx_us;
            snprintf(last_src, sizeof last_src, "%02x:%02x:%02x:%02x:%02x:%02x",
                     item.src[0], item.src[1], item.src[2],
                     item.src[3], item.src[4], item.src[5]);

            if (!announced) {
                announced = true;
                printf("# first IMU frame from %s (seq %u)\n", last_src, (unsigned)seq);
            }

            printf("S,%u,%lu,%lu,%.3f,%.3f,%.3f,%.2f,%.2f,%.2f,%d\n",
                   (unsigned)seq,
                   (unsigned long)item.pkt.t_us,
                   (unsigned long)item.rx_us,
                   (double)item.pkt.ax, (double)item.pkt.ay, (double)item.pkt.az,
                   (double)item.pkt.gx, (double)item.pkt.gy, (double)item.pkt.gz,
                   (int)last_rssi);
            fflush(stdout);
        }

        const int64_t now_us = esp_timer_get_time();
        if (now_us >= next_report_us) {
            next_report_us = now_us + 1000000;
            const long age_ms = last_rx_us ? (long)((now_us - last_rx_us) / 1000) : -1;
            printf("T,%d,%lu,%lu,%ld\n",
                   (int)last_rssi, (unsigned long)received, (unsigned long)lost, age_ms);
            fflush(stdout);
        }
    }
}

void app_main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);

    s_queue = xQueueCreate(ESPNOW_QUEUE_LEN, sizeof(rx_item_t));
    configASSERT(s_queue != NULL);

    ESP_LOGI(TAG, "boot: sMove 05-espnow-imu/rx");
    espnow_init();

    uint8_t mac[6] = { 0 };
    esp_read_mac(mac, ESP_MAC_WIFI_STA);
    printf("# sMove ESP-NOW IMU receiver — MAC %02x:%02x:%02x:%02x:%02x:%02x, channel %d\n",
           mac[0], mac[1], mac[2], mac[3], mac[4], mac[5], SMOVE_ESPNOW_CHANNEL);
    printf("# waiting for IMU frames from the sMove transmitter\n");
    fflush(stdout);

    xTaskCreate(hello_task, "hello", 3072, NULL, 6, NULL);
    xTaskCreate(printer_task, "printer", 4096, NULL, 5, NULL);
}
