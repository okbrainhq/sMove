// sMove board map — smove-r2-main (U1 = ESP32-C3-MINI-1-N4)
//
// User-interface RGB LED, D1 = LiteOn LTST-C19HE1WT (COMMON ANODE):
//
//   D1 pad 4 (common anode) -- 3V3_MAIN
//   D1 pad 1 (red   cathode) -- R11 1k -- U1 GPIO3  (net LED_R)
//   D1 pad 2 (green cathode) -- R12 1k -- U1 GPIO7  (net LED_G)
//   D1 pad 3 (blue  cathode) -- R13 1k -- U1 GPIO10 (net LED_B)
//
// The cathodes are pulled to 3V3 through the LED, so the GPIOs SINK current:
//   level 0 (low)  -> colour ON
//   level 1 (high) -> colour OFF
// All three pins must idle HIGH so the LED stays dark (including at reset,
// before the GPIO matrix is configured).
//
// 9-axis IMU, U2 = TDK InvenSense ICM-20948 (QFN-24 3x3 mm).
//
// The IMU core and its I/O rail run from 1V8_IMU (U5, AP2112K-1V8), so the I2C
// lines cross the PCA9306 level translator (U3) before reaching the C3:
//
//   U2 pad 24 (SDA) -- /IMU/SDA_1V8 -- U3 pad 4 || U3 pad 5 -- /SDA_HOST -- U1 pad 19 (GPIO5)
//   U2 pad 23 (SCL) -- /IMU/SCL_1V8 -- U3 pad 3 || U3 pad 6 -- /SCL_HOST -- U1 pad 18 (GPIO4)
//   U2 pad 22 (nCS)      -> 1V8_IMU  => I2C mode (not SPI)
//   U2 pad 12 (INT1)     not connected on this board — poll the data registers
//   U2 pad 10 (REGOUT)   -- C10 1uF, internal regulator, do not load
//
// Bus pull-ups: R16/R17 4.7k to 1V8_IMU on the IMU side, R18/R19 4.7k to
// 3V3_MAIN on the host side. Only the IMU sits on this bus.
//
// I2C address: measured 0x68 on the assembled board (AD0 low). The datasheet
// pair is 0x68/0x69, so the driver probes 0x68 and falls back to 0x69.
//
// The board underside faces the body and the IMU +Z axis stays outward (see the
// enclosure notes), so +Z reads ~+1 g when the unit rests on its back.
#pragma once

#include "driver/gpio.h"

#define SMOVE_LED_R_GPIO   GPIO_NUM_3
#define SMOVE_LED_G_GPIO   GPIO_NUM_7
#define SMOVE_LED_B_GPIO   GPIO_NUM_10

/* Common-anode LED: driving the pin low turns that colour on. */
#define SMOVE_LED_ON_LEVEL  0
#define SMOVE_LED_OFF_LEVEL 1

/* ICM-20948 on the 1.8 V I2C bus behind the PCA9306. */
#define SMOVE_IMU_SDA_GPIO        GPIO_NUM_5
#define SMOVE_IMU_SCL_GPIO        GPIO_NUM_4
#define SMOVE_IMU_I2C_ADDR        0x68   /* measured on smove-r2-main (AD0 low) */
#define SMOVE_IMU_I2C_ADDR_ALT    0x69   /* probe fallback (AD0 high / reworked board) */
#define SMOVE_IMU_I2C_SPEED_HZ    400000 /* bus supports 400 kHz; drop to 100 kHz if long leads */
