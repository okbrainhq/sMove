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
#pragma once

#include "driver/gpio.h"

#define SMOVE_LED_R_GPIO   GPIO_NUM_3
#define SMOVE_LED_G_GPIO   GPIO_NUM_7
#define SMOVE_LED_B_GPIO   GPIO_NUM_10

/* Common-anode LED: driving the pin low turns that colour on. */
#define SMOVE_LED_ON_LEVEL  0
#define SMOVE_LED_OFF_LEVEL 1
