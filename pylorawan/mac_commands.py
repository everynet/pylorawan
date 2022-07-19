# -*- coding: utf-8 -*-

from __future__ import annotations

import io
import json
import logging
import typing
from abc import ABCMeta, abstractmethod
from enum import Enum

from .exceptions import MACCommandCreateError, MACCommandLoadFromDictError, MACCommandParseError


class MACCommand(metaclass=ABCMeta):
    def __repr__(self) -> str:
        return json.dumps(self.as_dict())

    @property
    @abstractmethod
    def SIZE(self) -> int:
        pass

    @property
    def size(self) -> int:
        return self.SIZE + 1

    @property
    @abstractmethod
    def CID(self) -> int:
        pass

    @classmethod
    def parse(cls, raw: bytes):
        return cls()

    def generate(self) -> bytes:
        return self.CID.to_bytes(1, byteorder="little")

    def as_dict(self) -> dict:
        return {"mac_command": self.__class__.__name__, "params": {}}

    @classmethod
    def from_dict(cls, mac_command_as_dict) -> MACCommand:
        if mac_command_as_dict["mac_command"] != cls.__name__:
            raise MACCommandLoadFromDictError("Mac command name and class mismatch")

        return cls(**mac_command_as_dict["params"])


class LinkCheckReq(MACCommand):
    CID = 0x02
    SIZE = 0


class LinkADRAns(MACCommand):
    CID = 0x03
    SIZE = 1

    def __init__(
        self,
        channel_mask_ack: bool = False,
        datarate_ack: bool = False,
        power_ack: bool = False,
    ):
        self.channel_mask_ack = channel_mask_ack
        self.datarate_ack = datarate_ack
        self.power_ack = power_ack

    @classmethod
    def parse(cls, raw: bytes) -> MACCommand:
        return cls(
            bool(raw[0] & 0b1),
            bool(raw[0] & 0b10),
            bool(raw[0] & 0b100),
        )

    def generate(self) -> bytes:
        status = self.power_ack << 2 | self.datarate_ack << 1 | self.channel_mask_ack
        return bytes([self.CID, status])

    def as_dict(self) -> dict:
        ret = super().as_dict()
        ret["params"] = {
            "channel_mask_ack": self.channel_mask_ack,
            "datarate_ack": self.datarate_ack,
            "power_ack": self.power_ack,
        }

        return ret


class DutyCycleAns(MACCommand):
    CID = 0x04
    SIZE = 0


class RXParamSetupAns(MACCommand):
    CID = 0x05
    SIZE = 1

    def __init__(self, channel_ack=False, rx2_datarate_ack=False, rx1_datarate_offset_ack=False):
        self.channel_ack = channel_ack
        self.rx2_datarate_ack = rx2_datarate_ack
        self.rx1_datarate_offset_ack = rx1_datarate_offset_ack

    @classmethod
    def parse(cls, raw: bytes) -> MACCommand:
        return cls(
            bool(raw[0] & 0b1),
            bool(raw[0] & 0b10),
            bool(raw[0] & 0b100),
        )

    def generate(self) -> bytes:
        status = self.rx1_datarate_offset_ack << 2 | self.rx2_datarate_ack << 1 | self.channel_ack

        return bytes([self.CID, status])

    def as_dict(self) -> dict:
        ret = super().as_dict()
        ret["params"] = {
            "channel_ack": self.channel_ack,
            "rx2_datarate_ack": self.rx2_datarate_ack,
            "rx1_datarate_offset_ack": self.rx1_datarate_offset_ack,
        }

        return ret


class DevStatusAns(MACCommand):
    CID = 0x06
    SIZE = 2

    def __init__(self, battery: int = 255, margin: int = 0):
        self.battery = battery
        self.margin = margin

    @classmethod
    def parse(cls, raw: bytes) -> MACCommand:
        margin = raw[1] & 0b11111
        return cls(raw[0], (-margin - 1) if (raw[1] & 0b100000) else margin)

    def generate(self) -> bytes:
        return bytes(
            [
                self.CID,
                self.battery,
                (self.margin & 0b11111) if self.margin > 0 else ((-self.margin - 1) & 0b11111 | 0b100000),
            ]
        )

    def as_dict(self) -> dict:
        ret = super().as_dict()
        ret["params"] = {"battery": self.battery, "margin": self.margin}

        return ret


class NewChannelAns(MACCommand):
    CID = 0x07
    SIZE = 1

    def __init__(self, channel_frequency_ack: bool = False, datarate_range_ack: bool = False):
        self.channel_frequency_ack = channel_frequency_ack
        self.datarate_range_ack = datarate_range_ack

    @classmethod
    def parse(cls, raw: bytes) -> MACCommand:
        return cls(bool(raw[0] & 0b1), bool(raw[0] & 0b10))

    def generate(self) -> bytes:
        status = self.datarate_range_ack << 1 | self.channel_frequency_ack

        return bytes([self.CID, status])

    def as_dict(self) -> dict:
        ret = super().as_dict()
        ret["params"] = {
            "channel_frequency_ack": self.channel_frequency_ack,
            "datarate_range_ack": self.datarate_range_ack,
        }

        return ret


class RXTimingSetupAns(MACCommand):
    CID = 0x08
    SIZE = 0


class TXParamSetupAns(MACCommand):
    CID = 0x09
    SIZE = 0


class DlChannelAns(MACCommand):
    CID = 0x0A
    SIZE = 1

    def __init__(self, channel_frequency_ok: bool = False, uplink_frequency_exists: bool = False):
        self.channel_frequency_ok = channel_frequency_ok
        self.uplink_frequency_exists = uplink_frequency_exists

    @classmethod
    def parse(cls, raw: bytes) -> MACCommand:
        return cls(bool(raw[0] & 0b1), bool(raw[0] & 0b10))

    def generate(self) -> bytes:
        status = self.uplink_frequency_exists << 1 | self.channel_frequency_ok

        return bytes([self.CID, status])

    def as_dict(self) -> dict:
        ret = super().as_dict()
        ret["params"] = {
            "uplink_frequency_exists": self.uplink_frequency_exists,
            "channel_frequency_ok": self.channel_frequency_ok,
        }

        return ret


class DeviceTimeReq(MACCommand):
    CID = 0x0D
    SIZE = 0


class PingSlotInfoReq(MACCommand):
    CID = 0x10
    SIZE = 1

    def __init__(self, periodicity: int):
        self.periodicity = periodicity & 0x07

    @classmethod
    def parse(cls, raw: bytes) -> MACCommand:
        return cls(int.from_bytes(raw, byteorder="little"))

    def generate(self) -> bytes:
        return bytes([self.CID, self.periodicity])

    def as_dict(self):
        ret = super().as_dict()
        ret["params"] = {"periodicity": self.periodicity}

        return ret


class BeaconFreqAns(MACCommand):
    CID = 0x13
    SIZE = 1

    def __init__(self, status: bool):
        self.status = status

    @classmethod
    def parse(cls, raw: bytes) -> MACCommand:
        return cls(bool(int.from_bytes(raw, byteorder="little") & 0b1))

    def generate(self) -> bytes:
        return bytes([self.CID, self.status])

    def as_dict(self) -> dict:
        ret = super().as_dict()
        ret["params"] = {"status": self.status}

        return ret


class PingSlotChannelAns(MACCommand):
    CID = 0x11
    SIZE = 1

    def __init__(self, datarate_status: bool, channel_frequency_status: bool):
        self.datarate_status = datarate_status
        self.channel_frequency_status = channel_frequency_status

    @classmethod
    def parse(cls, raw: bytes) -> MACCommand:
        dr_status = bool(raw[0] & 0b10)
        freq_status = bool(raw[0] & 0b1)

        return cls(dr_status, freq_status)

    def generate(self) -> bytes:
        status = self.datarate_status << 1 | self.channel_frequency_status

        return bytes([self.CID, status])

    def as_dict(self) -> dict:
        ret = super().as_dict()
        ret["params"] = {
            "datarate_status": self.datarate_status,
            "channel_frequency_status": self.channel_frequency_status,
        }

        return ret


class PingSlotChannelReq(MACCommand):
    CID = 0x11
    SIZE = 1

    def __init__(self, datarate: int, frequency: int):
        self.datarate = datarate & 0x0F
        self.frequency = frequency & 0xFFFFFF

    @classmethod
    def parse(cls, raw: bytes) -> MACCommand:
        freq = int.from_bytes(raw[:3], byteorder="little")
        datarate = raw[3] & 0x0F

        return cls(datarate, freq)

    def generate(self) -> bytes:
        return (
            self.CID.to_bytes(1, byteorder="little")
            + self.frequency.to_bytes(3, byteorder="little")
            + self.datarate.to_bytes(1, byteorder="little")
        )

    def as_dict(self) -> dict:
        ret = super().as_dict()
        ret["params"] = {
            "datarate": self.datarate,
            "frequency": self.frequency,
        }

        return ret


class BeaconFreqReq(MACCommand):
    CID = 0x13
    SIZE = 3

    def __init__(self, frequency: int):
        self.frequency = frequency & 0xFFFFFF

    @classmethod
    def parse(cls, raw: bytes) -> MACCommand:
        return cls(int.from_bytes(raw, byteorder="little"))

    def generate(self) -> bytes:
        return self.CID.to_bytes(1, byteorder="little") + self.frequency.to_bytes(3, byteorder="little")

    def as_dict(self) -> dict:
        ret = super().as_dict()
        ret["params"] = {"frequency": self.frequency}

        return ret


class PingSlotInfoAns(MACCommand):
    CID = 0x10
    SIZE = 0


class LinkCheckAns(MACCommand):
    CID = 0x02
    SIZE = 2

    def __init__(self, margin: int = 0, gw_cnt: int = 1):
        self.margin = margin
        self.gw_cnt = gw_cnt

    @classmethod
    def parse(cls, raw: bytes) -> MACCommand:
        return cls(raw[0], raw[1])

    def generate(self) -> bytes:
        return bytes([self.CID, self.margin, self.gw_cnt])

    def as_dict(self) -> dict:
        ret = super().as_dict()
        ret["params"] = {"margin": self.margin, "gw_cnt": self.gw_cnt}

        return ret


class LinkADRReq(MACCommand):
    CID = 0x03
    SIZE = 4

    def __init__(
        self,
        tx_power: int,
        datarate: int,
        ch_mask: int,
        nb_trans: int,
        ch_mask_cntl: int,
    ):
        self.tx_power = tx_power
        self.datarate = datarate
        self.ch_mask = ch_mask
        self.nb_trans = nb_trans
        self.ch_mask_cntl = ch_mask_cntl

    @classmethod
    def parse(cls, raw: bytes) -> MACCommand:
        return cls(
            raw[0] & 0x0F,
            raw[0] >> 4,
            int.from_bytes(raw[1:3], byteorder="little"),
            raw[3] & 0x0F,
            (raw[3] >> 4) & 0b111,
        )

    def generate(self) -> bytes:
        return bytes(
            [
                self.CID,
                self.tx_power & 0x0F | ((self.datarate & 0x0F) << 4),
                self.ch_mask & 0xFF,
                (self.ch_mask >> 8) & 0xFF,
                self.nb_trans & 0x0F | ((self.ch_mask_cntl & 0b111) << 4),
            ]
        )

    def as_dict(self) -> dict:
        ret = super().as_dict()
        ret["params"] = {
            "tx_power": self.tx_power,
            "datarate": self.datarate,
            "ch_mask": self.ch_mask,
            "nb_trans": self.nb_trans,
            "ch_mask_cntl": self.ch_mask_cntl,
        }

        return ret


class DutyCycleReq(MACCommand):
    CID = 0x04
    SIZE = 1

    def __init__(self, max_dcycle: int):
        self.max_dcycle = max_dcycle

    @classmethod
    def parse(cls, raw: bytes) -> MACCommand:
        return cls(raw[0])

    def generate(self) -> bytes:
        return bytes([self.CID, self.max_dcycle])

    def as_dict(self) -> dict:
        ret = super().as_dict()
        ret["params"] = {"max_dcycle": self.max_dcycle}

        return ret


class RXParamSetupReq(MACCommand):
    CID = 0x05
    SIZE = 4

    def __init__(self, rx2_datarate: int, rx1_datarate_offset: int, rx2_frequency: int):
        self.rx2_datarate = rx2_datarate
        self.rx1_datarate_offset = rx1_datarate_offset
        self.rx2_frequency = rx2_frequency

    @classmethod
    def parse(cls, raw: bytes) -> MACCommand:
        return cls(
            raw[0] & 0x0F,
            (raw[0] >> 4) & 0x07,
            int.from_bytes(raw[1:4], byteorder="little"),
        )

    def generate(self) -> bytes:
        return bytes(
            [
                self.CID,
                (self.rx2_datarate & 0x0F) | ((self.rx1_datarate_offset & 0x07) << 4),
            ]
        ) + self.rx2_frequency.to_bytes(3, byteorder="little")

    def as_dict(self) -> dict:
        ret = super().as_dict()
        ret["params"] = {
            "rx2_datarate": self.rx2_datarate,
            "rx1_datarate_offset": self.rx1_datarate_offset,
            "rx2_frequency": self.rx2_frequency,
        }

        return ret


class DevStatusReq(MACCommand):
    CID = 0x06
    SIZE = 0


class NewChannelReq(MACCommand):
    CID = 0x07
    SIZE = 5

    def __init__(self, ch_index: int, ch_frequency: int, min_datarate: int, max_datarate: int):
        self.ch_index = ch_index
        self.ch_frequency = ch_frequency
        self.min_datarate = min_datarate
        self.max_datarate = max_datarate

    @classmethod
    def parse(cls, raw: bytes) -> MACCommand:
        return cls(
            raw[0],
            int.from_bytes(raw[1:4], byteorder="little"),
            raw[4] & 0x0F,
            (raw[4] >> 4) & 0x0F,
        )

    def generate(self) -> bytes:
        return (
            bytes([self.CID, self.ch_index])
            + self.ch_frequency.to_bytes(3, byteorder="little")
            + bytes([self.min_datarate & 0x0F | (self.max_datarate & 0x0F) << 4])
        )

    def as_dict(self) -> dict:
        ret = super().as_dict()
        ret["params"] = {
            "ch_index": self.ch_index,
            "ch_frequency": self.ch_frequency,
            "min_datarate": self.min_datarate,
            "max_datarate": self.max_datarate,
        }

        return ret


class RXTimingSetupReq(MACCommand):
    CID = 0x08
    SIZE = 1

    def __init__(self, delay: int = 1):
        self.delay = delay & 0x0F

    @classmethod
    def parse(cls, raw: bytes) -> MACCommand:
        return cls(raw[0])

    def generate(self) -> bytes:
        return bytes([self.CID, self.delay])

    def as_dict(self) -> dict:
        ret = super().as_dict()
        ret["params"] = {"delay": self.delay}

        return ret


class TXParamSetupReq(MACCommand):
    CID = 0x09
    SIZE = 1

    def __init__(self, max_eirp: int, uplink_dwell_time: int, downlink_dwell_time: int):
        self.max_eirp = max_eirp & 0x0F
        self.uplink_dwell_time = uplink_dwell_time & 1
        self.downlink_dwell_time = downlink_dwell_time & 1

    @classmethod
    def parse(cls, raw: bytes) -> MACCommand:
        if len(raw) != cls.SIZE:
            raise MACCommandParseError("Wrong length of message")

        return cls(raw[0] & 0x0F, raw[0] >> 4 & 1, raw[0] >> 5 & 1)

    def generate(self) -> bytes:
        return bytes(
            [
                self.CID,
                self.downlink_dwell_time << 5 | self.uplink_dwell_time << 4 | self.max_eirp,
            ]
        )

    def as_dict(self) -> dict:
        ret = super().as_dict()
        ret["params"] = {
            "downlink_dwell_time": self.downlink_dwell_time,
            "uplink_dwell_time": self.uplink_dwell_time,
            "max_eirp": self.max_eirp,
        }

        return ret


class DlChannelReq(MACCommand):
    CID = 0x0A
    SIZE = 4

    def __init__(self, ch_index, freq):
        self.ch_index = ch_index
        self.freq = freq

    @classmethod
    def parse(cls, raw: bytes) -> MACCommand:
        return cls(raw[0], int.from_bytes(raw[1:], byteorder="little"))

    def generate(self) -> bytes:
        return bytes([self.CID, self.ch_index]) + self.freq.to_bytes(3, byteorder="little")

    def as_dict(self) -> dict:
        ret = super().as_dict()
        ret["params"] = {"ch_index": self.ch_index, "freq": self.freq}

        return ret


class DeviceTimeAns(MACCommand):
    """
    seconds - 32-bit unsigned integer : Seconds since *GPS epoch
    fractional_second - 8bits unsigned integer: fractional second in 2 ^ -8 second steps

    * The GPS epoch (i.e Sunday January the 6th 1980 at 00:00:00 UTC) is used as origin.
    """

    CID = 0x0D
    SIZE = 5

    def __init__(self, seconds: int, fractional_second: int):
        self.seconds = seconds
        self.fractional_second = fractional_second

    @classmethod
    def parse(cls, raw: bytes) -> MACCommand:
        return cls(int.from_bytes(raw[:4], byteorder="little"), raw[4])

    def generate(self) -> bytes:
        return (
            self.CID.to_bytes(1, byteorder="little")
            + self.seconds.to_bytes(4, byteorder="little")
            + self.fractional_second.to_bytes(1, byteorder="little")
        )

    def as_dict(self) -> dict:
        ret = super().as_dict()
        ret["params"] = {
            "seconds": self.seconds,
            "fractional_second": self.fractional_second,
        }


class MACCommandDirection(Enum):
    UP = 1
    DOWN = 2


class MACCommandParser:
    mac_commands_map: typing.Dict[MACCommandDirection, typing.Dict[int, MACCommand]] = {
        MACCommandDirection.UP: {
            0x02: LinkCheckReq,
            0x03: LinkADRAns,
            0x04: DutyCycleAns,
            0x05: RXParamSetupAns,
            0x06: DevStatusAns,
            0x07: NewChannelAns,
            0x08: RXTimingSetupAns,
            0x09: TXParamSetupAns,
            0x0A: DlChannelAns,
            0x0D: DeviceTimeReq,
            # CLASS B
            0x10: PingSlotInfoReq,
            0x11: PingSlotChannelAns,
            0x13: BeaconFreqAns,
        },
        MACCommandDirection.DOWN: {
            0x02: LinkCheckAns,
            0x03: LinkADRReq,
            0x04: DutyCycleReq,
            0x05: RXParamSetupReq,
            0x06: DevStatusReq,
            0x07: NewChannelReq,
            0x08: RXTimingSetupReq,
            0x09: TXParamSetupReq,
            0x0A: DlChannelReq,
            0x0D: DeviceTimeAns,
            # CLASS B
            0x10: PingSlotInfoAns,
            0x11: PingSlotChannelReq,
            0x13: BeaconFreqReq,
        },
    }

    @staticmethod
    def read(cmd_cls: MACCommand, input_stream: io.BytesIO) -> bytearray:
        cmd_buffer = bytearray(cmd_cls.SIZE)
        read_size = input_stream.readinto(cmd_buffer)

        if read_size < cmd_cls.SIZE:
            raise MACCommandParseError("Not enough bytes in stream")

        return cmd_buffer

    @classmethod
    def create(
        cls,
        commands_stream: io.BytesIO,
        command_id: int,
        direction: MACCommandDirection,
    ) -> MACCommand:
        """Read from stream data and then create  instance by CID"""

        cmd_cls = cls.mac_commands_map.get(direction, {}).get(command_id, None)

        if cmd_cls is None:
            raise MACCommandCreateError("Unknown Command ID: %d" % command_id)

        cmd_buffer = cls.read(cmd_cls, commands_stream)

        return cmd_cls.parse(cmd_buffer)

    @classmethod
    def parse(cls, commands_buffer: bytes, direction: MACCommandDirection) -> typing.List[MACCommand]:
        commands_result = []

        commands_stream = io.BytesIO(commands_buffer)
        cmd_index = bytearray(1)
        try:
            while commands_stream.readinto(cmd_index):
                commands_result.append(cls.create(commands_stream, cmd_index[0], direction))
        except Exception as e:
            logging.warning("Error in parsing MAC commands: %s" % str(e))

        return commands_result
