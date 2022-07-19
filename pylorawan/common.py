# -*- coding: utf-8 -*-

import struct
import typing
from enum import Enum
from math import ceil
from random import randint

from .encryption import aes128_encrypt, generate_mic
from .exceptions import LoRaError
from .mac_commands import MACCommand, MACCommandDirection, MACCommandParser
from .message import MHDR, JoinAccept, JoinRequest, MACPayload, MACPayloadDownlink, PHYPayload


class TypeOfKey(Enum):
    NwkSKey = 1
    AppSKey = 2


def readable(b: bytes) -> str:
    return b[::-1].hex()


def unreadable(s: str) -> bytes:
    return bytes.fromhex(s)[::-1]


def decrypt_frm_payload(frm_payload: bytes, key: bytes, dev_addr: int, counter: int, direction: int) -> bytes:
    k = ceil(len(frm_payload) / 16)
    s = bytearray()
    s_i = bytearray(
        b"\x01\x00\x00\x00\x00"
        + direction.to_bytes(1, byteorder="little")
        + struct.pack("<LL", dev_addr, counter)
        + bytes(2)
    )

    for i in range(k):
        s_i[15] = i + 1
        s.extend(aes128_encrypt(key, s_i))

    return bytes([a ^ b for a, b in zip(frm_payload, s)])


def encrypt_frm_payload(frm_payload: bytes, key: bytes, dev_addr: int, counter: int, direction: int) -> bytes:
    return decrypt_frm_payload(frm_payload, key, dev_addr, counter, direction)


def generate_mic_mac_payload(mhdr: MHDR, mac_payload: MACPayload, nwk_skey: bytes) -> bytes:
    msg = mhdr.generate() + mac_payload.generate()

    direction = int(isinstance(mac_payload, (MACPayloadDownlink)))

    block_b_0 = (
        bytes([0x49, 0x0, 0x0, 0x0, 0x0, direction])
        + struct.pack("<LL", mac_payload.fhdr.dev_addr, mac_payload.fhdr.f_cnt)
        + bytes([0, len(msg)])
    )

    return generate_mic(nwk_skey, block_b_0 + msg)


def generate_mic_join_request(mhdr: MHDR, join_request: JoinRequest, app_key: bytes) -> bytes:
    message = mhdr.generate() + join_request.generate()

    return generate_mic(app_key, message)


def verify_mic_join_accept(join_accept: JoinAccept, app_key: bytes) -> bool:
    return generate_mic_join_accept(phy_payload.mhdr, phy_payload.payload, app_key) == phy_payload.mic


def verify_mic_join_request(phy_payload: PHYPayload, app_key: bytes) -> bool:
    return generate_mic_join_request(phy_payload.mhdr, phy_payload.payload, app_key) == phy_payload.mic


def verify_mic_mac_payload(phy_payload: PHYPayload, nwk_skey: bytes) -> bool:
    return generate_mic_mac_payload(phy_payload.mhdr, phy_payload.payload, nwk_skey) == phy_payload.mic


def verify_mic_phy_payload(phy_payload: PHYPayload, key: bytes) -> bool:
    if isinstance(phy_payload.payload, JoinRequest):
        return verify_mic_join_request(phy_payload, key)
    elif isinstance(phy_payload.payload, MACPayload):
        return verify_mic_mac_payload(phy_payload, key)


def generate_key(app_key: bytes, type_of_key: TypeOfKey, app_nonce: int, net_id: int, dev_nonce: int) -> bytes:
    message = (
        type_of_key.value.to_bytes(1, "big")
        + app_nonce.to_bytes(3, "little")
        + net_id.to_bytes(3, "little")
        + dev_nonce.to_bytes(2, "little")
        + bytes(7)  # pad16
    )
    return aes128_encrypt(app_key, message)


def generate_nwk_s_key(app_key: bytes, app_nonce: int, net_id: int, dev_nonce: int) -> bytes:
    return generate_key(app_key, TypeOfKey.NwkSKey, app_nonce, net_id, dev_nonce)


def generate_app_s_key(app_key: bytes, app_nonce: int, net_id: int, dev_nonce: int) -> bytes:
    return generate_key(app_key, TypeOfKey.AppSKey, app_nonce, net_id, dev_nonce)


def calc_ping_offset(beacon_time: int, dev_addr: str, ping_period: int) -> int:
    key = bytes(16)

    message: bytes = struct.pack("<i", beacon_time) + unreadable(dev_addr) + bytes(8)  # 4 bytes  # 4 bytes  # pad 16

    rand: bytes = aes128_encrypt(key, message)

    return (rand[0] + rand[1] * 256) % ping_period


def generate_dev_addr_for_network(net_id: int) -> int:
    # NOTE: key - net_id_type, value - (prefix, prefix_len, nwk_id_len)
    net_type_to_params = {
        0: (0, 1, 6),
        1: (0b10, 2, 6),
        2: (0b110, 3, 9),
        3: (0b1110, 4, 11),
        4: (0b11110, 5, 12),
        5: (0b111110, 6, 13),
        6: (0b1111110, 7, 15),
        7: (0b11111110, 8, 17),
    }

    net_id_type = net_id >> 21

    if net_id_type > 7:
        raise LoRaError("Wrong length, net_id must be 3 bytes")

    prefix, prefix_len, nwk_id_len = net_type_to_params[net_id_type]

    nwk_addr_len = 32 - nwk_id_len - prefix_len
    nwk_id = net_id & (2**nwk_id_len - 1)

    # dev_addr = prefix | nwk_id | nwk_addr
    msbits = (prefix << nwk_id_len + nwk_addr_len) + (nwk_id << nwk_addr_len)
    nwk_addr = randint(0, 2**nwk_addr_len - 1)

    return msbits + nwk_addr


def extract_mac_commands(mac_payload: MACPayload, nwk_s_key: bytes) -> typing.List[MACCommand]:
    direction = int(isinstance(mac_payload, (MACPayloadDownlink)))

    if mac_payload.f_port == 0:
        commands_buffer = decrypt_frm_payload(
            mac_payload.frm_payload, nwk_s_key, mac_payload.fhdr.dev_addr, mac_payload.fhdr.f_cnt, direction
        )
    else:
        commands_buffer = mac_payload.fhdr.f_opts

    return MACCommandParser.parse(commands_buffer, MACCommandDirection(direction + 1))
