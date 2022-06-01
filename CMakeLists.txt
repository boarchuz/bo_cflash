idf_component_register(PRIV_REQUIRES partition_table esptool_py)

if(NOT CONFIG_BO_CFLASH_CUSTOM_TARGET)
    # Component is disabled; do nothing
    return()
endif()

if(BOOTLOADER_BUILD)
    return()
endif()

# Create a custom flash target that will be used to generate flasher_args
idf_component_get_property(main_args esptool_py FLASH_ARGS)
idf_component_get_property(sub_args esptool_py FLASH_SUB_ARGS)
esptool_py_flash_target(${CONFIG_BO_CFLASH_CUSTOM_TARGET_NAME} "${main_args}" "${sub_args}")

idf_build_get_property(build_dir BUILD_DIR)

if(CONFIG_BO_CFLASH_FLASH_BOOTLOADER)
    # Add the bootloader to the custom flash target
    esptool_py_flash_target_image(
        ${CONFIG_BO_CFLASH_CUSTOM_TARGET_NAME}
        bootloader
        "${CONFIG_BOOTLOADER_OFFSET_IN_FLASH}"
        "${BOOTLOADER_BUILD_DIR}/bootloader.bin"
    )
endif()

if(CONFIG_BO_CFLASH_FLASH_PARTITION_TABLE)
    # Add the partition table to the custom flash target
    esptool_py_flash_target_image(
        ${CONFIG_BO_CFLASH_CUSTOM_TARGET_NAME}
        partition-table
        "${CONFIG_PARTITION_TABLE_OFFSET}"
        "${build_dir}/partition_table/partition-table.bin"
    )
endif()

if(CONFIG_BO_CFLASH_FLASH_APP)
    # Add the app to the custom flash target
    if(CONFIG_BO_CFLASH_FLASH_APP_PARTITION_CUSTOM_SET_OFFSET)
        set(app_partition_offset "${CONFIG_BO_CFLASH_FLASH_APP_PARTITION_CUSTOM_OFFSET}")
    else()
        partition_table_get_partition_info(app_partition_offset "-t ${CONFIG_BO_CFLASH_FLASH_APP_PARTITION_TYPE} -s ${CONFIG_BO_CFLASH_FLASH_APP_PARTITION_SUBTYPE}" "offset")
    endif()
    esptool_py_flash_target_image(
        ${CONFIG_BO_CFLASH_CUSTOM_TARGET_NAME}
        app
        "${app_partition_offset}"
        "${build_dir}/${PROJECT_BIN}"
    )
endif()

if(CONFIG_BO_CFLASH_SET_BOOT)
    partition_table_get_partition_info(otadata_offset "--partition-type data --partition-subtype ota" "offset")
    if(otadata_offset)
        # Add otadata to the custom flash target
        if(CONFIG_BO_CFLASH_SET_BOOT_CONFIG_CURRENT)
            set(boot_partition_subtype "${CONFIG_BO_CFLASH_FLASH_APP_PARTITION_SUBTYPE}")
        else()
            set(boot_partition_subtype "${CONFIG_BO_CFLASH_SET_BOOT_CONFIG_PARTITION_SUBTYPE}")
        endif()

        set(otadata_bin ${build_dir}/cflash_otadata.bin)

        idf_build_get_property(python PYTHON)
        add_custom_command(
            OUTPUT ${otadata_bin}
            COMMAND ${python} ${CMAKE_CURRENT_SOURCE_DIR}/gen_otadata.py ${boot_partition_subtype} ${otadata_bin}
        )
        add_custom_target(cflash_otadata ALL DEPENDS ${otadata_bin})
        add_dependencies(${CONFIG_BO_CFLASH_CUSTOM_TARGET_NAME} cflash_otadata)
        esptool_py_flash_target_image(
            ${CONFIG_BO_CFLASH_CUSTOM_TARGET_NAME}
            otadata
            "${otadata_offset}"
            "${otadata_bin}"
        )
    else()
        message(WARNING "otadata partition does not exist; skipping boot config")
    endif()
endif()

if(CONFIG_BO_CFLASH_FLASH_CUSTOM_BIN_1)
    # Add custom binary 1 to the custom flash target
    set(custom_bin_1_path "${build_dir}/${CONFIG_BO_CFLASH_FLASH_CUSTOM_BIN_1_PATH}")
    if(CONFIG_BO_CFLASH_FLASH_CUSTOM_BIN_1_CONFIG_TYPES)
        partition_table_get_partition_info(custom_bin_1_offset "--partition-type ${CONFIG_BO_CFLASH_FLASH_CUSTOM_BIN_1_PARTITION_TYPE} --partition-subtype ${CONFIG_BO_CFLASH_FLASH_CUSTOM_BIN_1_PARTITION_SUBTYPE}" "offset")
        if(NOT custom_bin_1_offset)
            message(FATAL_ERROR "custom binary (1) partition not found")
        endif()
    else()
        set(custom_bin_1_offset "${CONFIG_BO_CFLASH_FLASH_CUSTOM_BIN_1_OFFSET}")
    endif()
    esptool_py_flash_target_image(
        ${CONFIG_BO_CFLASH_CUSTOM_TARGET_NAME}
        custom_bin_1
        "${custom_bin_1_offset}"
        "${custom_bin_1_path}"
    )
endif()

if(CONFIG_BO_CFLASH_FLASH_CUSTOM_BIN_2)
    # Add custom binary 2 to the custom flash target
    set(custom_bin_2_path "${build_dir}/${CONFIG_BO_CFLASH_FLASH_CUSTOM_BIN_2_PATH}")
    if(CONFIG_BO_CFLASH_FLASH_CUSTOM_BIN_2_CONFIG_TYPES)
        partition_table_get_partition_info(custom_bin_2_offset "--partition-type ${CONFIG_BO_CFLASH_FLASH_CUSTOM_BIN_2_PARTITION_TYPE} --partition-subtype ${CONFIG_BO_CFLASH_FLASH_CUSTOM_BIN_2_PARTITION_SUBTYPE}" "offset")
        if(NOT custom_bin_2_offset)
            message(FATAL_ERROR "custom binary (2) partition not found")
        endif()
    else()
        set(custom_bin_2_offset "${CONFIG_BO_CFLASH_FLASH_CUSTOM_BIN_2_OFFSET}")
    endif()
    esptool_py_flash_target_image(
        ${CONFIG_BO_CFLASH_CUSTOM_TARGET_NAME}
        custom_bin_2
        "${custom_bin_2_offset}"
        "${custom_bin_2_path}"
    )
endif()

# Set configuration for flasher_args.json (see esptool.py)
set(ESPTOOLPY_BEFORE "${CONFIG_ESPTOOLPY_BEFORE}")
set(ESPTOOLPY_AFTER  "${CONFIG_ESPTOOLPY_AFTER}")
if(CONFIG_ESPTOOLPY_NO_STUB)
    set(ESPTOOLPY_WITH_STUB false)
else()
    set(ESPTOOLPY_WITH_STUB true)
endif()

if(CONFIG_SECURE_BOOT OR CONFIG_SECURE_FLASH_ENC_ENABLED)
    # If security enabled then override post flash option
    set(ESPTOOLPY_AFTER "no_reset")
endif()

# Generate flasher args files
# see flasher_args.json.in
set(flasher_args_content
"{
    \"write_flash_args\" : [ \"--flash_mode\", \"${ESPFLASHMODE}\",
                        \"--flash_size\", \"${ESPFLASHSIZE}\",
                        \"--flash_freq\", \"${ESPFLASHFREQ}\" ],
    \"flash_settings\" : {
        \"flash_mode\": \"${ESPFLASHMODE}\",
        \"flash_size\": \"${ESPFLASHSIZE}\",
        \"flash_freq\": \"${ESPFLASHFREQ}\"
    },
    \"flash_files\" : {
        $<JOIN:$<TARGET_PROPERTY:${CONFIG_BO_CFLASH_CUSTOM_TARGET_NAME},FLASH_FILE>,,
        >
    },
    $<JOIN:$<TARGET_PROPERTY:${CONFIG_BO_CFLASH_CUSTOM_TARGET_NAME},FLASH_ENTRY>,,
    >$<$<BOOL:$<TARGET_PROPERTY:${CONFIG_BO_CFLASH_CUSTOM_TARGET_NAME},FLASH_ENTRY>>:,>
    \"extra_esptool_args\" : {
        \"after\"  : \"${ESPTOOLPY_AFTER}\",
        \"before\" : \"${ESPTOOLPY_BEFORE}\",
        \"stub\"   : ${ESPTOOLPY_WITH_STUB},
        \"chip\"   : \"${ESPTOOLPY_CHIP}\"
    }
}"
)
string(CONFIGURE "${flasher_args_content}" flasher_args_content)

# Generate custom flasher_args_x.json
file_generate("${CMAKE_CURRENT_BINARY_DIR}/flasher_args.json.in"
            CONTENT "${flasher_args_content}")
file_generate("${CMAKE_BINARY_DIR}/flasher_args_${CONFIG_BO_CFLASH_CUSTOM_TARGET_NAME}.json"
            INPUT "${CMAKE_CURRENT_BINARY_DIR}/flasher_args.json.in")

if(CONFIG_BO_CFLASH_OVERWRITE_FLASHER_ARGS)
   # Add a custom target (that depends on esptool.py in order to run after it) to overwrite flasher_args.json
   add_custom_target(
       bo_cflash_overwrite_flasher_args
       BYPRODUCTS ${CMAKE_BINARY_DIR}/flasher_args.json
       COMMAND ${CMAKE_COMMAND} -E echo "[bo_cflash] setting flasher_args.json"
       # Backup the default to flasher_args_default.json
       COMMAND ${CMAKE_COMMAND} -E chdir ${CMAKE_BINARY_DIR} cp ${CMAKE_BINARY_DIR}/flasher_args.json ${CMAKE_BINARY_DIR}/flasher_args_default.json
       # Remove the default
       COMMAND ${CMAKE_COMMAND} -E chdir ${CMAKE_BINARY_DIR} rm -f ${CMAKE_BINARY_DIR}/flasher_args.json
       # Set custom flasher_args.json
       COMMAND ${CMAKE_COMMAND} -E chdir ${CMAKE_BINARY_DIR} cp ${CMAKE_BINARY_DIR}/flasher_args_${CONFIG_BO_CFLASH_CUSTOM_TARGET_NAME}.json ${CMAKE_BINARY_DIR}/flasher_args.json
   )
   add_dependencies(${COMPONENT_LIB} bo_cflash_overwrite_flasher_args esptool_py)
endif()
