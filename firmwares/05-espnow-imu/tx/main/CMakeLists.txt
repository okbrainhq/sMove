idf_component_register(SRCS "imu_espnow_tx.c" "icm20948.c"
                       INCLUDE_DIRS ".")

# Optional build-time knob: sample + transmit period in ms
# (-DIMU_SAMPLE_PERIOD_MS=<ms>, or IMU_SAMPLE_PERIOD_MS=<ms> ./flash-tx.sh).
# Falls back to the 100 ms default in imu_espnow_tx.c.
if(DEFINED IMU_SAMPLE_PERIOD_MS)
    target_compile_definitions(${COMPONENT_LIB} PRIVATE
                               IMU_SAMPLE_PERIOD_MS=${IMU_SAMPLE_PERIOD_MS})
endif()
