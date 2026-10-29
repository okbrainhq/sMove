/*
 * icm20948.c — ICM-20948 bring-up driver for smove-r2-main (U2).
 *
 * Register map (TDK DS-000189): the device is banked, and a bank switch and the
 * actual register access are separate I2C transactions — REG_BANK_SEL (0x7F) is
 * written first with the bank in bits 5:4. Every helper below does that, so a
 * caller never has to think about banks.
 *
 * Reference frame is the chip's own: +X/+Y in the package plane, +Z out of the
 * top of the package (the board's outward face).
 */

#include "icm20948.h"

#include <string.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "esp_log.h"

static const char *TAG = "icm20948";

/* ---------------------------------------------------------------- registers */
/* User bank 0 */
#define REG_WHO_AM_I        0x00
#define REG_USER_CTRL       0x03
#define REG_PWR_MGMT_1      0x06
#define REG_PWR_MGMT_2      0x07
#define REG_I2C_MST_STATUS  0x17
#define REG_ACCEL_XOUT_H    0x2D
#define REG_BANK_SEL        0x7F

/* User bank 2 */
#define REG_GYRO_CONFIG_1   0x01
#define REG_ACCEL_CONFIG    0x14

/* User bank 3 (internal I2C master) */
#define REG_I2C_MST_CTRL    0x01
#define REG_I2C_SLV0_ADDR   0x03
#define REG_I2C_SLV0_REG    0x04
#define REG_I2C_SLV0_CTRL   0x05
#define REG_I2C_SLV0_DO     0x06

/* Register bank selection: bank n lives in bits 5:4 of REG_BANK_SEL. */
#define BANK(n) ((uint8_t)((n) << 4))

/* Bank 0 bit fields */
#define PWR_MGMT_1_DEVICE_RESET 0x80
#define PWR_MGMT_1_CLK_AUTO     0x01   /* PLL from the best available gyro axis */
#define USER_CTRL_I2C_MST_EN    0x20   /* enable the internal I2C master (mag) */
#define USER_CTRL_I2C_MST_RST   0x02   /* reset the internal I2C master module */

/* Bank 2 bit fields: DLPFCFG in bits 5:3, FS_SEL in bits 2:1, FCHOICE in bit 0
 * (bit 0 = 1 bypasses the DLPF, so it stays 0 = DLPF enabled). */
#define GYRO_DLPFCFG_50HZ       (3 << 3)
#define GYRO_FS_SEL_250DPS      (0u << 1)
#define ACCEL_DLPFCFG_50HZ      (3 << 3)
#define ACCEL_FS_SEL_2G         (0u << 1)

/* Scale factors for the ranges above. */
#define ACCEL_LSB_PER_G         16384.0f
#define GYRO_LSB_PER_DPS        131.0f

/* ------------------------------------------------------- AK09916 (via U2) */
#define AK09916_I2C_ADDR        0x0C   /* 7-bit address on the internal bus */
#define AK09916_REG_CNTL2       0x31
#define AK09916_REG_CNTL3       0x32
#define AK09916_REG_ST1         0x10   /* ST1, HXL..HZH, TMPS, ST2 (9 bytes) */
#define AK09916_MODE_100HZ      0x08
#define AK09916_SOFT_RESET      0x01
#define AK09916_LSB_PER_UT      0.15f  /* µT per LSB */
#define MAG_BURST_BYTES         9      /* ST1..ST2 */
#define MAG_DATA_OFFSET         1      /* HXL is the byte after ST1 */
#define MAG_ST1_DRDY            0x01   /* ST1: measurement data ready */
#define MAG_ST2_HOFL            0x08   /* ST2: magnetic sensor overflow */

/* I2C master clock: I2C_MST_CLK = 7 -> ~345 kHz (needed for a 100 Hz mag read). */
#define I2C_MST_CTRL_400KHZ     0x07

/* Burst layout: 6 accel + 6 gyro + 2 temp (bank 0) + 9 mag bytes (0x3B..0x43). */
#define REG_EXT_SLV_SENS_DATA_0 0x3B
#define ACCEL_OFFSET            0
#define GYRO_OFFSET             6
#define TEMP_OFFSET             12
#define MAG_OFFSET              14
#define SAMPLE_BURST_BYTES      (MAG_OFFSET + MAG_BURST_BYTES)

#define I2C_TIMEOUT_MS          50
#define RESET_DELAY_MS          100
#define MAG_SETTLE_MS           10

/* ------------------------------------------------------------ raw helpers */

static int16_t be16(const uint8_t *p)
{
    return (int16_t)((uint16_t)p[0] << 8 | p[1]);
}

static int16_t le16(const uint8_t *p)
{
    return (int16_t)((uint16_t)p[1] << 8 | p[0]);
}

/* ------------------------------------------------------------- I2C plumbing */

static esp_err_t select_bank(const icm20948_t *imu, uint8_t bank)
{
    const uint8_t buf[2] = { REG_BANK_SEL, BANK(bank) };
    return i2c_master_transmit(imu->dev, buf, sizeof buf, I2C_TIMEOUT_MS);
}

static esp_err_t write_reg(const icm20948_t *imu, uint8_t bank, uint8_t reg, uint8_t value)
{
    esp_err_t err = select_bank(imu, bank);
    if (err != ESP_OK) {
        return err;
    }
    const uint8_t buf[2] = { reg, value };
    return i2c_master_transmit(imu->dev, buf, sizeof buf, I2C_TIMEOUT_MS);
}

static esp_err_t read_regs(const icm20948_t *imu, uint8_t bank, uint8_t reg,
                           uint8_t *out, size_t len)
{
    esp_err_t err = select_bank(imu, bank);
    if (err != ESP_OK) {
        return err;
    }
    return i2c_master_transmit_receive(imu->dev, &reg, 1, out, len, I2C_TIMEOUT_MS);
}

static esp_err_t read_reg(const icm20948_t *imu, uint8_t bank, uint8_t reg, uint8_t *out)
{
    return read_regs(imu, bank, reg, out, 1);
}

/* ------------------------------------------------------ magnetometer setup */

/*
 * One-shot write into an AK09916 register through U2's internal I2C master:
 * point SLV0 at (address, register, data), trigger a single-byte transfer by
 * enabling SLV0, then disable it again so it does not keep re-writing.
 */
static esp_err_t mag_write(icm20948_t *imu, uint8_t reg, uint8_t value)
{
    esp_err_t err;

    if ((err = write_reg(imu, 3, REG_I2C_SLV0_ADDR, AK09916_I2C_ADDR)) != ESP_OK ||
        (err = write_reg(imu, 3, REG_I2C_SLV0_REG, reg)) != ESP_OK ||
        (err = write_reg(imu, 3, REG_I2C_SLV0_DO, value)) != ESP_OK ||
        (err = write_reg(imu, 3, REG_I2C_SLV0_CTRL, 0x81)) != ESP_OK) { /* EN + LENG=1 */
        return err;
    }

    vTaskDelay(pdMS_TO_TICKS(MAG_SETTLE_MS));
    return write_reg(imu, 3, REG_I2C_SLV0_CTRL, 0x00);
}

/*
 * Configure the AK09916 for continuous 100 Hz measurement and leave SLV0 reading
 * HXL..ST2 into EXT_SLV_SENS_DATA_00..07, so every main-bus burst carries a
 * fresh magnetometer sample with no extra transactions.
 */
static esp_err_t mag_start(icm20948_t *imu)
{
    esp_err_t err;

    /* Speed up the internal master before touching the AK09916. */
    if ((err = write_reg(imu, 3, REG_I2C_MST_CTRL, I2C_MST_CTRL_400KHZ)) != ESP_OK) {
        return err;
    }
    if ((err = mag_write(imu, AK09916_REG_CNTL3, AK09916_SOFT_RESET)) != ESP_OK) {
        return err;
    }
    if ((err = mag_write(imu, AK09916_REG_CNTL2, AK09916_MODE_100HZ)) != ESP_OK) {
        return err;
    }

    /* Continuous read: SLV0_ADDR with the read bit, LENG = 9 bytes, starting at
     * ST1 so every burst carries the data-ready and overflow flags with it. */
    if ((err = write_reg(imu, 3, REG_I2C_SLV0_ADDR, 0x80 | AK09916_I2C_ADDR)) != ESP_OK ||
        (err = write_reg(imu, 3, REG_I2C_SLV0_REG, AK09916_REG_ST1)) != ESP_OK ||
        (err = write_reg(imu, 3, REG_I2C_SLV0_CTRL, 0x80 | MAG_BURST_BYTES)) != ESP_OK) {
        return err;
    }

    /*
     * Confirm the AK09916 actually answers before claiming the magnetometer
     * works: ST1.DRDY only goes high once the die has completed a measurement,
     * so an absent or unconfigured mag stays 0x00 here.
     */
    uint8_t probe[MAG_BURST_BYTES] = { 0 };
    for (int attempt = 0; attempt < 5; attempt++) {
        vTaskDelay(pdMS_TO_TICKS(MAG_SETTLE_MS * 2));
        if (read_regs(imu, 0, REG_EXT_SLV_SENS_DATA_0, probe, sizeof probe) != ESP_OK) {
            continue;
        }
        if (probe[0] != 0x00) {   /* ST1 */
            imu->mag_configured = true;
            ESP_LOGI(TAG, "AK09916 online: ST1=0x%02x ST2=0x%02x (100 Hz continuous)",
                     probe[0], probe[MAG_BURST_BYTES - 1]);
            return ESP_OK;
        }
    }

    ESP_LOGW(TAG, "AK09916 did not answer through SLV0 (ST1 stayed 0x00)");
    {
        uint8_t user_ctrl = 0, mst_status = 0, slv[3] = { 0 }, wia2 = 0;

        /* Second opinion: read the AK09916 device ID (WIA2 = 0x01, expect 0x09)
         * through a single SLV0 read, so "no die" is distinguishable from
         * "continuous mode write failed". */
        if (write_reg(imu, 3, REG_I2C_SLV0_ADDR, 0x80 | AK09916_I2C_ADDR) == ESP_OK &&
            write_reg(imu, 3, REG_I2C_SLV0_REG, 0x01) == ESP_OK &&
            write_reg(imu, 3, REG_I2C_SLV0_CTRL, 0x81) == ESP_OK) {
            vTaskDelay(pdMS_TO_TICKS(MAG_SETTLE_MS * 2));
            read_reg(imu, 0, REG_EXT_SLV_SENS_DATA_0, &wia2);
        }

        read_reg(imu, 0, REG_USER_CTRL, &user_ctrl);
        read_reg(imu, 0, REG_I2C_MST_STATUS, &mst_status);
        read_regs(imu, 3, REG_I2C_SLV0_ADDR, slv, sizeof slv);
        ESP_LOGW(TAG, "diag: USER_CTRL=0x%02x I2C_MST_STATUS=0x%02x "
                      "SLV0 addr/reg/ctrl=0x%02x/0x%02x/0x%02x "
                      "AK09916 WIA2=0x%02x (expect 0x09), ST1..=%02x %02x %02x",
                 user_ctrl, mst_status, slv[0], slv[1], slv[2], wia2,
                 probe[0], probe[1], probe[2]);
    }
    return ESP_ERR_NOT_FOUND;
}

/*
 * Bring the internal I2C master up: reset it once (it can latch a stuck state
 * after a device reset) and then enable it. SLV0 transfers — including the
 * AK09916 register writes — only happen while I2C_MST_EN is set.
 */
static esp_err_t internal_master_start(icm20948_t *imu)
{
    esp_err_t err = write_reg(imu, 0, REG_USER_CTRL, USER_CTRL_I2C_MST_RST);
    if (err != ESP_OK) {
        return err;
    }
    vTaskDelay(pdMS_TO_TICKS(MAG_SETTLE_MS));

    err = write_reg(imu, 0, REG_USER_CTRL, USER_CTRL_I2C_MST_EN);
    vTaskDelay(pdMS_TO_TICKS(MAG_SETTLE_MS));
    return err;
}

/* ------------------------------------------------------------------- API */

esp_err_t icm20948_init(icm20948_t *imu, i2c_master_bus_handle_t bus, uint8_t address)
{
    memset(imu, 0, sizeof *imu);
    imu->address = address;

    const i2c_device_config_t dev_cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = address,
        .scl_speed_hz = 400000,
    };
    esp_err_t err = i2c_master_bus_add_device(bus, &dev_cfg, &imu->dev);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "cannot attach I2C device 0x%02x: %s", address, esp_err_to_name(err));
        return err;
    }

    /* Power-on reset: clears sleep, bank selection and the internal I2C master. */
    err = write_reg(imu, 0, REG_PWR_MGMT_1, PWR_MGMT_1_DEVICE_RESET);
    if (err != ESP_OK) {
        goto fail;
    }
    vTaskDelay(pdMS_TO_TICKS(RESET_DELAY_MS));

    uint8_t who = 0;
    err = read_reg(imu, 0, REG_WHO_AM_I, &who);
    if (err != ESP_OK) {
        goto fail;
    }
    if (who != ICM20948_WHO_AM_I_VALUE) {
        ESP_LOGE(TAG, "address 0x%02x answered 0x%02x, not an ICM-20948 (WHO_AM_I 0x%02x)",
                 address, who, ICM20948_WHO_AM_I_VALUE);
        err = ESP_ERR_NOT_FOUND;
        goto fail;
    }

    /* Wake up, clock from the gyro PLL, then enable accel + gyro (DISABLE_* = 0). */
    if ((err = write_reg(imu, 0, REG_PWR_MGMT_1, PWR_MGMT_1_CLK_AUTO)) != ESP_OK ||
        (err = write_reg(imu, 0, REG_PWR_MGMT_2, 0x00)) != ESP_OK) {
        goto fail;
    }

    /* ±250 dps / ±2 g with the ~50 Hz DLPF: enough bandwidth for a 100 ms log. */
    if ((err = write_reg(imu, 2, REG_GYRO_CONFIG_1, GYRO_DLPFCFG_50HZ | GYRO_FS_SEL_250DPS)) != ESP_OK ||
        (err = write_reg(imu, 2, REG_ACCEL_CONFIG, ACCEL_DLPFCFG_50HZ | ACCEL_FS_SEL_2G)) != ESP_OK) {
        goto fail;
    }
    imu->accel_lsb_per_g = ACCEL_LSB_PER_G;
    imu->gyro_lsb_per_dps = GYRO_LSB_PER_DPS;

    /*
     * The internal I2C master must be running *before* SLV0 is configured: SLV0
     * transfers (including the AK09916 mode writes) only happen while
     * USER_CTRL.I2C_MST_EN is set.
     */
    if ((err = internal_master_start(imu)) != ESP_OK) {
        goto fail;
    }

    /* The magnetometer is a separate die: a failure here must not stop the
     * 6-axis demo, so it is reported and the sample is flagged invalid. */
    err = mag_start(imu);
    if (err != ESP_OK) {
        ESP_LOGW(TAG, "magnetometer not configured (%s); accel/gyro only",
                 esp_err_to_name(err));
        err = ESP_OK;
    }

    ESP_LOGI(TAG, "ICM-20948 ready at 0x%02x: WHO_AM_I=0x%02x, accel ±2 g (%.0f LSB/g), "
                  "gyro ±250 dps (%.0f LSB/dps), DLPF ~50 Hz, mag 100 Hz (%s)",
             address, who, imu->accel_lsb_per_g, imu->gyro_lsb_per_dps,
             imu->mag_configured ? "AK09916 via SLV0" : "unavailable");
    return ESP_OK;

fail:
    ESP_LOGE(TAG, "ICM-20948 init failed at 0x%02x: %s", address, esp_err_to_name(err));
    i2c_master_bus_rm_device(imu->dev);
    imu->dev = NULL;
    return err;
}

esp_err_t icm20948_read(icm20948_t *imu, icm20948_sample_t *out)
{
    uint8_t raw[SAMPLE_BURST_BYTES];
    esp_err_t err = read_regs(imu, 0, REG_ACCEL_XOUT_H, raw, sizeof raw);
    if (err != ESP_OK) {
        return err;
    }

    for (int axis = 0; axis < 3; axis++) {
        out->accel_g[axis] = (float)be16(&raw[ACCEL_OFFSET + 2 * axis]) / imu->accel_lsb_per_g;
        out->gyro_dps[axis] = (float)be16(&raw[GYRO_OFFSET + 2 * axis]) / imu->gyro_lsb_per_dps;
    }
    out->temp_c = (float)be16(&raw[TEMP_OFFSET]) / 333.87f + 21.0f;

    /* Mag payload (ST1, HXL..HZH, TMPS, ST2): 16-bit little endian; ST1.DRDY
     * marks a fresh sample and ST2.HOFL a saturated one. */
    const uint8_t *mag = &raw[MAG_OFFSET];
    const uint8_t st1 = mag[0];
    const uint8_t st2 = mag[MAG_BURST_BYTES - 1];
    out->mag_valid = imu->mag_configured && (st1 & MAG_ST1_DRDY) && !(st2 & MAG_ST2_HOFL);
    for (int axis = 0; axis < 3; axis++) {
        out->mag_uT[axis] = (float)le16(&mag[MAG_DATA_OFFSET + 2 * axis]) * AK09916_LSB_PER_UT;
    }

    return ESP_OK;
}

esp_err_t icm20948_deinit(icm20948_t *imu)
{
    if (imu->dev == NULL) {
        return ESP_OK;
    }
    esp_err_t err = i2c_master_bus_rm_device(imu->dev);
    imu->dev = NULL;
    return err;
}
