idf_component_register(SRCS "blink.c"
                       INCLUDE_DIRS ".")

# Optional build-time knob: -DBLINK_HALF_PERIOD_MS=<ms> (or BLINK_HALF_PERIOD_MS=<ms>
# ./flash.sh). Falls back to the default in blink.c.
if(DEFINED BLINK_HALF_PERIOD_MS)
    target_compile_definitions(${COMPONENT_LIB} PRIVATE
                               BLINK_HALF_PERIOD_MS=${BLINK_HALF_PERIOD_MS})
endif()
