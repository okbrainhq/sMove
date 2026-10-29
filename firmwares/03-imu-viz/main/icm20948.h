/*
 * icm20948.h — minimal ICM-20948 (U2 on smove-r2-main) driver.
 *
 * Blocking I2C transfers on the ESP-IDF "new" I2C master driver, no DMP, no
 * FIFO: one register burst per sample, which is all a bring-up demo needs.
 *
 * Fixed configuration (change the ICM20948_* config macros in icm20948.c to
 * trade resolution for range):
 *   accelerometer  ±2 g   (16384 LSB/g), DLPF ~50 Hz
 *   gyroscope      ±250 dps (131 LSB/dps), DLPF ~50 Hz
 *   magnetometer   AK09916, continuous 100 Hz, read through the internal I2C
 *                  master into EXT_SLV_SENS_DATA_00..08
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "driver/i2c_master.h"
#include "esp_err.h"

/* WHO_AM_I value of the ICM-20948 (bank 0, register 0x00). */
#define ICM20948_WHO_AM_I_VALUE 0xEA

/* One coherent read of accel + gyro + temperature + magnetometer. */
typedef struct {
    float accel_g[3];    /* X, Y, Z in g, board axes */
    float gyro_dps[3];   /* X, Y, Z in deg/s */
    float temp_c;        /* die temperature in °C */
    float mag_uT[3];     /* X, Y, Z in µT (AK09916, 0.15 µT/LSB) */
    bool  mag_valid;     /* false while the AK09916 has no fresh sample */
} icm20948_sample_t;

/* Driver instance. Treat the fields as read-only after init. */
typedef struct {
    i2c_master_dev_handle_t dev;
    uint8_t address;
    float accel_lsb_per_g;
    float gyro_lsb_per_dps;
    bool mag_configured;
} icm20948_t;

/*
 * Attach the IMU to an existing I2C master bus at `address` (0x68 on this board,
 * 0x69 as the alternate strap), reset it, verify WHO_AM_I, wake it and configure
 * the three sensors.
 *
 * Returns ESP_OK on success, ESP_ERR_NOT_FOUND when WHO_AM_I does not match and
 * any I2C failure verbatim. On failure the device handle is released again, so
 * the caller can retry with a different address.
 */
esp_err_t icm20948_init(icm20948_t *imu, i2c_master_bus_handle_t bus, uint8_t address);

/* Read one sample. Single 22-byte burst; ESP_OK or the I2C error. */
esp_err_t icm20948_read(icm20948_t *imu, icm20948_sample_t *out);

/* Detach from the bus (does not touch the sensor configuration). */
esp_err_t icm20948_deinit(icm20948_t *imu);
