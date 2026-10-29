idf_component_register(SRCS "imu_stream.c" "icm20948.c"
                       INCLUDE_DIRS ".")

# Optional build-time knob: sample period in ms (-DIMU_SAMPLE_PERIOD_MS=<ms>, or
# IMU_SAMPLE_PERIOD_MS=<ms> ./viz.sh). Falls back to the default in imu_stream.c.
if(DEFINED IMU_SAMPLE_PERIOD_MS)
    target_compile_definitions(${COMPONENT_LIB} PRIVATE
                               IMU_SAMPLE_PERIOD_MS=${IMU_SAMPLE_PERIOD_MS})
endif()
