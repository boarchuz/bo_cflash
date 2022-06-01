# ESP-IDF Custom Flash Generator

CFlash is an ESP-IDF component to generate a custom flash configuration.

In the default configuration, ESP-IDF will flash the bootloader, partition table, and the factory app. This is inefficient and inconvenient when developing bootloaders, firmware intended for non-factory partitions, or when more control is required for custom designs.

CFlash makes it easy to customise what is flashed, and where.

## Features
* Individual toggles for flashing the bootloader, partition table, and app
* Flash the app firmware directly to an OTA or test partition
* Included OTA data generator can automatically set the boot partition to any app partition
* Optionally overwrite the default ESP-IDF flash configuration to seamlessly integrate with your workflow (eg. via your IDE's "Build, Flash and Monitor" command)

## Usage
* Clone into your project's components directory
* Configure via menuconfig
