# -*- coding: utf-8 -*-

from __future__ import annotations

import binascii
import io
import os
import struct
import time
import typing
from abc import ABCMeta, abstractmethod
from enum import Enum

from .encryption import aes128_decrypt, aes128_encrypt, generate_mic
from .exceptions import JoinRequestError, MACPayloadError, MHDRError, MICError, ParseMessageError, PHYPayloadError


class MType(Enum):
    JoinRequest = 0x00
    JoinAccept = 0x01
    UnconfirmedDataUp = 0x02
    UnconfirmedDataDown = 0x03
    ConfirmedDataUp = 0x04
    ConfirmedDataDown = 0x05
    RFU = 0x06
    Proprietary = 0x07


class MHDR:
    def __init__(
        self,
        mtype: MType,
        major: int,
    ):
        if not isinstance(mtype, MType):
            raise MHDRError("The field mtype has an invalid value")
        if not (isinstance(major, int) and 0 <= major < 4):
            raise MHDRError("The field major has an invalid value")

        self._mtype = mtype
        self._major = major

    @property
    def mtype(self) -> int:
        return self._mtype

    @property
    def major(self) -> int:
        return self._major

    @property
    def rfu(self) -> int:
        return 0

    @classmethod
    def parse(cls, raw: bytes) -> MHDR:
        if len(raw) != 1:
            raise ParseMessageError("Can't parse MHDR, wrong length")

        mtype = MType(raw[0] >> 5 & 0b111)
        major = raw[0] & 0b11

        return cls(mtype, major)

    def generate(self) -> bytes:
        int_mhdr = self.mtype.value << 5 | self.rfu << 2 | self.major
        return int_mhdr.to_bytes(1, byteorder="little")

    def as_dict(self) -> dict:
        return {"MHDR": {"mtype": self.mtype, "rfu": self.rfu, "major": self.major}}


class PHYPayload:
    def __init__(
        self,
        mhdr: MHDR,
        payload: typing.Union[MACPayload, JoinRequest, Proprietary],
        mic: typing.Optional[bytes],
    ):
        if mhdr is not None and not isinstance(mhdr, MHDR):
            raise PHYPayloadError("mhdr should be instance of MDHR class")

        if (
            mhdr.mtype == MType.Proprietary
            and not isinstance(payload, Proprietary)
            or (
                mhdr.mtype
                in {
                    MType.UnconfirmedDataDown,
                    MType.UnconfirmedDataUp,
                    MType.ConfirmedDataDown,
                    MType.ConfirmedDataUp,
                }
                and not isinstance(payload, MACPayload)
            )
            or (mhdr.mtype == MType.JoinRequest and not isinstance(payload, JoinRequest))
        ):
            raise PHYPayloadError("The field payload has an inconsistent type with MHDR.MType")

        self._mhdr = mhdr
        self._payload = payload
        self._mic = mic

    @property
    def mhdr(self):
        return self._mhdr

    @property
    def payload(self):
        return self._payload

    @property
    def mic(self):
        return self._mic

    @classmethod
    def parse(cls, raw: bytes) -> PHYPayload:
        if len(raw) < 5:
            raise ParseMessageError("Wrong size of LoRaWAN message")

        mhdr = MHDR.parse(raw[:1])
        if mhdr.mtype in {MType.ConfirmedDataUp, MType.UnconfirmedDataUp}:
            payload_cls = MACPayloadUplink
        elif mhdr.mtype in {MType.ConfirmedDataDown, MType.UnconfirmedDataDown}:
            payload_cls = MACPayloadDownlink
        elif mhdr.mtype == MType.JoinRequest:
            payload_cls = JoinRequest
        elif mhdr.mtype == MType.Proprietary:
            payload_cls = Proprietary
        else:
            raise PHYPayloadError("Can't parse PHYPayload, mtype has an invalid value")

        payload = payload_cls.parse(raw[1:-4])
        mic = raw[-4:]

        return cls(mhdr, payload, mic)

    def generate(self) -> bytes:
        return self.mhdr.generate() + self.payload.generate() + self.mic

    def as_dict(self) -> dict:
        return {"mhdr": self.mhdr.as_dict(), "payload": self.payload.as_dict(), "mic": self.mic}


class FHDR(metaclass=ABCMeta):
    DEV_ADDR_SIZE = 4
    FCTRL_SIZE = 1
    FCNT_SIZE = 2

    def __init__(
        self,
        dev_addr: int,
        f_ctrl: typing.Union[FCtrlUplink, FCtrlDownlink],
        f_cnt: int,
        f_opts: bytes = b"",
    ):
        self._dev_addr = dev_addr
        self._f_ctrl = f_ctrl
        self._f_cnt = f_cnt
        self._f_opts = f_opts

    @property
    def dev_addr(self) -> int:
        return self._dev_addr

    @property
    def f_ctrl(self) -> typing.Union[FCtrlUplink, FCtrlDownlink]:
        return self._f_ctrl

    @property
    def f_cnt(self) -> int:
        return self._f_cnt

    @f_cnt.setter
    def f_cnt(self, value: int) -> None:
        self._f_cnt = value

    @property
    def f_opts(self) -> bytes:
        return self._f_opts

    @staticmethod
    @abstractmethod
    def get_fctrl_cls() -> typing.Union[FCtrlDownlink, FCtrlUplink]:
        pass

    @classmethod
    def parse(cls, raw_stream: io.BytesIO) -> FHDR:
        fctrl_cls = cls.get_fctrl_cls()

        dev_addr = int.from_bytes(raw_stream.read(cls.DEV_ADDR_SIZE), byteorder="little")
        f_ctrl = fctrl_cls.parse(raw_stream.read(cls.FCTRL_SIZE))
        f_cnt = int.from_bytes(raw_stream.read(cls.FCNT_SIZE), byteorder="little")
        f_opts = raw_stream.read(f_ctrl.f_opts_len)

        return cls(dev_addr, f_ctrl, f_cnt, f_opts)

    def generate(self) -> bytes:
        return (
            self.dev_addr.to_bytes(self.DEV_ADDR_SIZE, byteorder="little")
            + self.f_ctrl.generate()
            + self.f_cnt.to_bytes(self.FCNT_SIZE, byteorder="little")
            + self.f_opts
        )

    def as_dict(self) -> dict:
        return {
            "dev_addr": self.dev_addr,
            "f_ctrl": self.f_ctrl.as_dict(),
            "f_cnt": self.f_cnt,
            "f_opts": self.f_opts,
        }


class MACPayload(metaclass=ABCMeta):
    FPORT_SIZE = 1

    def __init__(
        self,
        fhdr: FHDR,
        f_port: typing.Optional[int] = None,
        frm_payload: bytes = b"",
    ):
        if not isinstance(fhdr, FHDR):
            raise MACPayloadError("The field fhdr must be instance of MHDR")

        if not (f_port is None or 0 <= f_port < 256):
            raise MACPayloadError("The field f_port has an invalid value")

        if not isinstance(frm_payload, bytes):
            raise MACPayloadError("The field frm_payload has an invalid value")

        self._fhdr = fhdr
        self._f_port = f_port
        self._frm_payload = frm_payload

    @staticmethod
    @abstractmethod
    def get_fhdr_cls() -> FHDR:
        pass

    @property
    def fhdr(self) -> FHDR:
        return self._fhdr

    @property
    def f_port(self) -> typing.Optional[int]:
        return self._f_port

    @property
    def frm_payload(self) -> bytes:
        return self._frm_payload

    @classmethod
    def parse(cls, raw: bytes) -> MACPayload:
        if len(raw) < 7:
            raise ParseMessageError("Can't parse MACPayload, wrong size")

        fhdr_cls = cls.get_fhdr_cls()

        raw_stream = io.BytesIO(raw)
        fhdr = fhdr_cls.parse(raw_stream)

        f_port = raw_stream.read(cls.FPORT_SIZE) or None

        if f_port is not None:
            f_port = int.from_bytes(f_port, byteorder="little")

        frm_payload = raw_stream.read()

        return cls(fhdr, f_port=f_port, frm_payload=frm_payload)

    def generate(self) -> bytes:
        raw = self.fhdr.generate()

        if self.f_port is not None:
            raw += self.f_port.to_bytes(self.FPORT_SIZE, byteorder="little")
            raw += self.frm_payload

        return raw

    def as_dict(self) -> dict:
        return {
            "fhdr": self.fhdr.as_dict(),
            "f_port": self.f_port,
            "frm_payload": self.frm_payload,
        }


class FCtrlDownlink:
    def __init__(self, adr: bool, ack: bool, f_pending: bool, f_opts_len: int):
        self._adr = adr
        self._ack = ack
        self._f_pending = f_pending
        self._f_opts_len = f_opts_len

    @property
    def adr(self) -> bool:
        return self._adr

    @property
    def ack(self) -> bool:
        return self._ack

    @property
    def f_pending(self) -> bool:
        return self._f_pending

    @property
    def f_opts_len(self) -> int:
        return self._f_opts_len

    @classmethod
    def parse(self, raw: bytes) -> FCtrlDownlink:
        f_opts_len = raw[0] & 0x0F
        f_pending = bool(raw[0] & 0x10)
        ack = bool(raw[0] & 0x20)
        adr = bool(raw[0] & 0x80)

        return FCtrlDownlink(adr, ack, f_pending, f_opts_len)

    def generate(self) -> bytes:
        return (self.adr << 7 | self.ack << 5 | self.f_pending << 4 | self.f_opts_len).to_bytes(1, "big")

    def as_dict(self) -> dict:
        return {
            "adr": self.adr,
            "ack": self.ack,
            "f_pending": self.f_pending,
            "f_opts_len": self.f_opts_len,
        }


class FCtrlUplink:
    def __init__(self, adr: bool, adr_ack_req: bool, ack: bool, class_b: bool, f_opts_len: int):
        self._adr = adr
        self._adr_ack_req = adr_ack_req
        self._ack = ack
        self._class_b = class_b
        self._f_opts_len = f_opts_len

    @property
    def adr(self) -> bool:
        return self._adr

    @property
    def adr_ack_req(self) -> bool:
        return self._adr_ack_req

    @property
    def ack(self) -> bool:
        return self._ack

    @property
    def class_b(self) -> bool:
        return self._class_b

    @property
    def f_opts_len(self) -> int:
        return self._f_opts_len

    @classmethod
    def parse(self, raw: bytes) -> FCtrlUplink:
        f_opts_len = raw[0] & 0x0F
        class_b = bool(raw[0] & 0x10)
        ack = bool(raw[0] & 0x20)
        adr_ack_req = bool(raw[0] & 0x40)
        adr = bool(raw[0] & 0x80)

        return FCtrlUplink(adr, adr_ack_req, ack, class_b, f_opts_len)

    def generate(self) -> bytes:
        return (self.adr << 7 | self.adr_ack_req << 6 | self.ack << 5 | self.class_b << 4 | self.f_opts_len).to_bytes(
            1, "big"
        )

    def as_dict(self) -> dict:
        return {
            "adr": self.adr,
            "adr_ack_req": self.adr_ack_req,
            "ack": self.ack,
            "class_b": self.class_b,
            "f_opts_len": self.f_opts_len,
        }


class FHDRUplink(FHDR):
    @staticmethod
    def get_fctrl_cls():
        return FCtrlUplink


class FHDRDownlink(FHDR):
    @staticmethod
    def get_fctrl_cls():
        return FCtrlDownlink


class MACPayloadUplink(MACPayload):
    @staticmethod
    def get_fhdr_cls():
        return FHDRUplink


class MACPayloadDownlink(MACPayload):
    @staticmethod
    def get_fhdr_cls():
        return FHDRDownlink


class JoinRequest:
    # 18 bytes
    #######################################
    # size   #   8    #    8   #     2    #
    # fields # AppEUI # DevEUI # DevNonce #
    #######################################

    def __init__(self, app_eui: int, dev_eui: int, dev_nonce: int):
        self._app_eui = app_eui
        self._dev_eui = dev_eui
        self._dev_nonce = dev_nonce

    @property
    def app_eui(self) -> int:
        return self._app_eui

    @property
    def dev_eui(self) -> int:
        return self._dev_eui

    @property
    def dev_nonce(self) -> int:
        return self._dev_nonce

    @classmethod
    def parse(cls, raw: bytes) -> JoinRequest:
        if len(raw) != 18:  # Size of JoinRequest by spec
            raise ParseMessageError("Can't parse JoinRequest, wrong size")

        app_eui, dev_eui, dev_nonce = struct.unpack("<QQH", raw)
        return cls(app_eui, dev_eui, dev_nonce)

    def generate(self) -> bytes:
        return struct.pack("<QQH", self.app_eui, self.dev_eui, self.dev_nonce)

    def as_dict(self) -> dict:
        return {
            "app_eui": self.app_eui,
            "dev_eui": self.dev_eui,
            "dev_nonce": self.dev_nonce,
        }


class DLSettings:
    def __init__(self, rx1_dr_offset: int, rx2_datarate: int):
        self._rx1_dr_offset = rx1_dr_offset
        self._rx2_datarate = rx2_datarate

    @property
    def rx1_dr_offset(self) -> int:
        return self._rx1_dr_offset

    @property
    def rx2_datarate(self) -> int:
        return self._rx2_datarate

    @classmethod
    def parse(cls, raw: bytes) -> DLSettings:
        rx2_datarate = raw[0] & 0x0F
        rx1_dr_offset = raw[0] >> 4 & 0x07

        return cls(rx1_dr_offset, rx2_datarate)

    def generate(self) -> bytes:
        return (self.rx1_dr_offset << 4 | self.rx2_datarate).to_bytes(1, byteorder="little")

    def as_dict(self) -> dict:
        return {"rx1_dr_offset": self.rx1_dr_offset, "rx2_datarate": self.rx2_datarate}


class JoinAccept:
    def __init__(
        self,
        app_nonce: int,
        net_id: int,
        dev_addr: int,
        dl_settings: DLSettings,
        rx_delay: int,
        cf_list=b"",
    ):
        self._app_nonce = app_nonce
        self._net_id = net_id
        self._dev_addr = dev_addr
        self._dl_settings = dl_settings
        self._rx_delay = rx_delay
        self._cf_list = cf_list

    @property
    def app_nonce(self) -> int:
        return self._app_nonce

    @property
    def net_id(self) -> int:
        return self._net_id

    @property
    def dev_addr(self) -> int:
        return self._dev_addr

    @property
    def dl_settings(self) -> DLSettings:
        return self._dl_settings

    @property
    def rx_delay(self) -> int:
        return self._rx_delay

    @property
    def cf_list(self) -> bytes:
        return self._cf_list

    @classmethod
    def parse(cls, raw: bytes, app_key: bytes) -> JoinAccept:
        if len(raw) < 12:
            raise ParseMessageError("Can't parse JoinAccept, wrong size")

        mhdr = MHDR.parse(raw[:1])
        if mhdr.mtype != MType.JoinAccept:
            raise ParseMessageError("Can't parse JoinAccept, wrong mhdr.mtype")

        decoded_raw = aes128_encrypt(key=app_key, message=raw[1:])
        mic = decoded_raw[-4:]

        if mic != generate_mic(app_key, mhdr.generate() + decoded_raw[:-4]):
            raise MICError("Can't parse JoinAccept, wrong mhdr.mtype")

        raw_stream = io.BytesIO(decoded_raw[:-4])

        app_nonce = int.from_bytes(raw_stream.read(3), byteorder="little")
        net_id = int.from_bytes(raw_stream.read(3), byteorder="little")
        dev_addr = int.from_bytes(raw_stream.read(4), byteorder="little")
        dl_settings = DLSettings.parse(raw_stream.read(1))
        rx_delay = int.from_bytes(raw_stream.read(1), byteorder="little")
        cf_list = raw_stream.read()

        return cls(app_nonce, net_id, dev_addr, dl_settings, rx_delay, cf_list)

    def generate(self, app_key: bytes) -> bytes:
        mhdr = MHDR(mtype=MType.JoinAccept, major=0)
        bytes_join_accept = (
            self.app_nonce.to_bytes(3, byteorder="little")
            + self.net_id.to_bytes(3, byteorder="little")
            + self.dev_addr.to_bytes(4, byteorder="little")
            + self.dl_settings.generate()
            + self.rx_delay.to_bytes(1, byteorder="little")
            + self.cf_list
        )
        bytes_mhdr = mhdr.generate()
        mic = generate_mic(app_key, bytes_mhdr + bytes_join_accept)

        encrypted_bytes_join_accept = aes128_decrypt(app_key, bytes_join_accept + mic)

        return bytes_mhdr + encrypted_bytes_join_accept

    def as_dict(self) -> dict:
        return {
            "app_nonce": self.app_nonce,
            "net_id": self.net_id,
            "dev_addr": self.dev_addr,
            "dl_settings": self.dl_settings.as_dict(),
            "rx_delay": self.rx_delay,
            "cf_list": self.cf_list,
        }


class Proprietary:
    def __init__(self, payload: bytes):
        self._payload = payload

    @property
    def payload(self) -> bytes:
        return self._payload

    @classmethod
    def parse(cls, raw: bytes) -> Proprietary:
        return cls(raw)

    def generate(self) -> bytes:
        return self._payload

    def as_dict(self) -> dict:
        return {"payload": self.payload}
