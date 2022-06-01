#!/usr/bin/env python
#
# generates otadata to select given app partition

import argparse
import sys

__version__ = '1.0'

OTA_DATA_PARTITION_SIZE = 0x2000
ESP_PARTITION_SUBTYPE_APP_FACTORY = 0x00
ESP_PARTITION_SUBTYPE_APP_OTA_MIN = 0x10
ESP_PARTITION_SUBTYPE_APP_OTA_MAX = ESP_PARTITION_SUBTYPE_APP_OTA_MIN + 16

def generate_empty_otadata():
    return bytearray(b'\xFF' * OTA_DATA_PARTITION_SIZE)

def get_otadata_crc(ota_partition_index):
    # There are only 16 possibilities so all matching CRCs are in this array rather than calculating:
    crcs = [
        0x4743989A,
        0x55F63774,
        0xED4A5011,
        0x709D68A8,
        0xC8210FCD,
        0xDA94A023,
        0x6228C746,
        0x3A4BD710,
        0x82F7B075,
        0x90421F9B,
        0x28FE78FE,
        0xB5294047,
        0x0D952722,
        0x1F2088CC,
        0xA79CEFA9,
        0xAFE6A860,
    ]
    return crcs[ota_partition_index]

def generate_otadata(ota_partition_index):
    output = generate_empty_otadata()
    # Refer to esp_ota_select_entry_t
    ota_seq = ota_partition_index + 1
    output[0] = ota_seq
    output[1] = 0
    output[2] = 0
    output[3] = 0
    crc = get_otadata_crc(ota_partition_index)
    output[28] = (crc >>  0) & 0xFF
    output[29] = (crc >>  8) & 0xFF
    output[30] = (crc >> 16) & 0xFF
    output[31] = (crc >> 24) & 0xFF
    return output

def partition_subtype(x):
    subtype = int(x, 0)
    if (subtype != ESP_PARTITION_SUBTYPE_APP_FACTORY) and (subtype < ESP_PARTITION_SUBTYPE_APP_OTA_MIN or subtype >= ESP_PARTITION_SUBTYPE_APP_OTA_MAX):
        raise argparse.ArgumentTypeError("invalid partition subtype")
    return subtype

def main():
    parser = argparse.ArgumentParser(description='Generates otadata binary file to boot the provided app partition')

    parser.add_argument('subtype', help='Partition subtype: 0x00 (factory) or 0x10 (ota_0) to 0x1F (ota_15)', type=partition_subtype)
    parser.add_argument('output', help='Path for binary file.', nargs='?', default='-')
    args = parser.parse_args()

    subtype = args.subtype
    if (subtype == ESP_PARTITION_SUBTYPE_APP_FACTORY):
        output = generate_empty_otadata()
    else:
        output = generate_otadata(subtype - ESP_PARTITION_SUBTYPE_APP_OTA_MIN)
    output_path = args.output
    try:
        stdout_binary = sys.stdout.buffer  # Python 3
    except AttributeError:
        stdout_binary = sys.stdout
    with stdout_binary if output_path == '-' else open(output_path, 'wb') as f:
        f.write(output)
    return 0


class InputError(RuntimeError):
    def __init__(self, e):
        super(InputError, self).__init__(e)

if __name__ == '__main__':
    try:
        r = main()
        sys.exit(r)
    except InputError as e:
        print(e, file=sys.stderr)
        sys.exit(2)
