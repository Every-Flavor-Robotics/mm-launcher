idf_component_register(SRCS "main.cpp"
                       INCLUDE_DIRS "."
                       REQUIRES hiwonder_bus esp_driver_uart esp_timer nvs_flash vfs esp_app_format)

# espp configs are filled with partial designated initializers by design.
target_compile_options(${COMPONENT_LIB} PRIVATE -Wno-missing-field-initializers)
