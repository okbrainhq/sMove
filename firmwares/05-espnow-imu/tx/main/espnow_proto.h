/*
 * espnow_proto.h — the sMove ESP-NOW wire format (05-espnow-imu).
 *
 * Kept byte-for-byte identical in tx/main and rx/main on purpose: the two ends
 * are flashed from the same commit, so a version bump on one side is a build
 * failure on the other instead of silently decoded garbage.
 *
 * Both chips are little-endian ESP32s, so the packed structs can be memcpy'd
 * straight onto the radio buffer — no serialisation layer, no endian swap.
 *
 *   IMU   tx -> rx, one per sample (10 Hz by default)
 *   HELLO rx -> tx, 1 Hz, so the tx side can pair without a hard-coded MAC
 */
#pragma once

#include <stdint.h>

/* "SMOV" as it lands in a little-endian uint32_t. */
#define SMOVE_ESPNOW_MAGIC    0x534D4F56u
#define SMOVE_ESPNOW_VERSION  1

/* Wi-Fi channel both ends park on. */
#define SMOVE_ESPNOW_CHANNEL  1

#define SMOVE_ESPNOW_MSG_IMU    1
#define SMOVE_ESPNOW_MSG_HELLO  2

/* tx -> rx: one IMU sample. */
typedef struct __attribute__((packed)) {
    uint32_t magic;    /* SMOVE_ESPNOW_MAGIC */
    uint8_t  version;  /* SMOVE_ESPNOW_VERSION */
    uint8_t  type;     /* SMOVE_ESPNOW_MSG_IMU */
    uint16_t seq;      /* +1 per sample, wraps; the rx side counts gaps as loss */
    uint32_t t_us;     /* sender esp_timer_get_time(), low 32 bits */
    float    ax, ay, az;  /* g */
    float    gx, gy, gz;  /* deg/s */
} smove_espnow_imu_t;

/* rx -> tx: "I am here, pair with me". Also carries a little liveness info. */
typedef struct __attribute__((packed)) {
    uint32_t magic;     /* SMOVE_ESPNOW_MAGIC */
    uint8_t  version;   /* SMOVE_ESPNOW_VERSION */
    uint8_t  type;      /* SMOVE_ESPNOW_MSG_HELLO */
    uint16_t period_ms; /* 0: the rx side does not know the tx cadence */
    uint32_t uptime_s;  /* receiver uptime */
} smove_espnow_hello_t;

_Static_assert(sizeof(smove_espnow_imu_t) == 36, "IMU frame layout changed");
_Static_assert(sizeof(smove_espnow_hello_t) == 12, "HELLO frame layout changed");
