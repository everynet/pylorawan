import typing
from abc import ABCMeta, abstractmethod
from enum import Enum, IntEnum, auto

from pylorawan import consts, exceptions


class Modulation(Enum):
    LoRa = consts.LoRaModulation
    FSK = consts.FSKModulation
    LRFHSS = consts.LRFHSSModulation


class Direction(IntEnum):
    uplink = auto()
    downlink = auto()
    both = auto()


##############
# Datarates  #
##############
class DataRate:
    def __init__(self, index: int, direction: Direction):
        self.index = index
        self.direction = direction

    def allowed_for_uplink(self) -> bool:
        return self.direction != Direction.downlink

    def allowed_for_downlink(self) -> bool:
        return self.direction != Direction.uplink

    def __repr__(self):
        return f"{self.__class__.__name__}({self.index})"


class RFUDataRate(DataRate, consts.RFU):
    modulation = None

    def __init__(self, index: int):
        super().__init__(index=index, direction=Direction.both)


class LoRaDataRate(DataRate):
    modulation: typing.Optional[Modulation] = Modulation.LoRa

    def __init__(
        self,
        index: int,
        spreading: int,
        bandwidth: int,
        direction: Direction,
    ):
        super().__init__(index=index, direction=direction)

        self.spreading = spreading
        self.bandwidth = bandwidth  # in kHz

    def __repr__(self):
        return f"LoRaDataRate({self.index}: SF{self.spreading}BW{self.bandwidth})"


class FSKDataRate(DataRate):
    modulation: typing.Optional[Modulation] = Modulation.FSK

    def __init__(self, index: int, bitrate: int, direction: Direction):
        super().__init__(index=index, direction=direction)

        self.bitrate = bitrate  # bit per second

    def __repr__(self):
        return f"FSKDataRate({self.index}: {self.bitrate} bps)"


class LRFHSSDataRate(DataRate):
    modulation: typing.Optional[Modulation] = Modulation.LRFHSS

    def __init__(
        self,
        index: int,
        coding_rate: str,
        occupied_channel_width: int,
        direction: Direction,
    ):
        super().__init__(index=index, direction=direction)

        self.coding_rate = coding_rate
        self.occupied_channel_width = occupied_channel_width


# Max payload size
class BaseMaxPayloadSize:
    def __init__(self, dr: int) -> None:
        self.dr = dr

    def __repr__(self):
        return f"{self.__class__.__name__}(dr={self.dr})"


class MaxPayloadSize(BaseMaxPayloadSize):
    def __init__(self, dr: int, n: int):
        super().__init__(dr)
        self.n = n

    @property
    def m(self) -> int:
        return self.n + 8

    def __repr__(self):
        return f"{self.__class__.__name__}(dr={self.dr}, n={self.n}, m={self.m})"


class MaxPayloadSizeWithDwell(BaseMaxPayloadSize):
    def __init__(self, dr: int, n_dwell_0: typing.Optional[int], n_dwell_1: typing.Optional[int]):
        super().__init__(dr)
        self.n_dwell_0 = n_dwell_0
        self.n_dwell_1 = n_dwell_1

    @property
    def m_dwell_0(self) -> int:
        if self.n_dwell_0 is None:
            return None
        return self.n_dwell_0 + 8

    @property
    def m_dwell_1(self) -> int:
        if self.n_dwell_1 is None:
            return None
        return self.n_dwell_1 + 8

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(dr={self.dr}, n={self.n_dwell_0}|{self.n_dwell_1}, "
            f"m={self.m_dwell_0}|{self.m_dwell_1})"
        )


# ChMaskCtrl value


class ChMaskCtrl:
    def __init__(self, index: int):
        self.index = index

    def __repr__(self):
        return f"{self.__class__.__name__}({self.index})"


class RFUChMaskCtrl(ChMaskCtrl, consts.RFU):
    pass


class RangeChMaskCtrl(ChMaskCtrl):
    def __init__(self, index: int, start: int, end: int):
        super().__init__(index)
        self.start = start
        self.end = end

    def __repr__(self):
        return f"{self.__class__.__name__}({self.index}, start={self.start}, end={self.end})"


class On125kHzChMaskCtrl(ChMaskCtrl):
    pass


class Off125kHzChMaskCtrl(ChMaskCtrl):
    pass


class AllOnChMaskCtrl(ChMaskCtrl):
    pass


# Channels


class Channel:
    def __init__(
        self,
        index: int,
        frequency_khz: int,
        datarates: typing.List[DataRate],
        coding_rate: typing.Optional[str] = "4/5",
        fixed=True,
        is_used=True,
    ):
        self.index = index
        self.frequency_khz = frequency_khz
        self.datarates = datarates
        self.coding_rate = coding_rate
        self.fixed = fixed
        self.is_used = is_used

    def datarate_index_is_used(self, index: int) -> bool:
        min_index = self.datarates[0].index
        max_index = self.datarates[-1].index

        return min_index <= index <= max_index

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return (
            f"Channel(index={self.index}, frequency_khz={self.frequency_khz}, datarates={self.datarates}, "
            f"coding_rate={self.coding_rate!r}, fixed={self.fixed}, is_used={self.is_used})"
        )


# Bands


class Band(metaclass=ABCMeta):
    @classmethod
    @property
    def name(cls) -> str:
        """
        This property returns name of the band, as defined in standart.

        :return: band name
        :rtype: str
        """
        return cls.__name__.replace("_", "-")

    @property
    @abstractmethod
    def is_support_tx_param_setup(self) -> bool:
        return False

    @property
    @abstractmethod
    def is_dynamic_channel_plan_region(self) -> bool:
        return False

    # TODO: Make uplink/downlink channels also be Dict, no List (as other tables)
    @property
    @abstractmethod
    def uplink_channels(self) -> typing.List[Channel]:
        return []

    @property
    @abstractmethod
    def downlink_channels(self) -> typing.List[Channel]:
        return []

    @property
    @abstractmethod
    def uplink_dwell_time(self) -> int:
        return 0

    @property
    @abstractmethod
    def downlink_dwell_time(self) -> int:
        return 0

    @property
    @abstractmethod
    def max_eirp_index(self) -> int:
        return 0

    @property
    @abstractmethod
    def table_datarates(self) -> typing.Dict[int, DataRate]:
        return {}

    @property
    @abstractmethod
    def table_tx_power(self) -> typing.Dict[int, typing.Union[int, consts.RFU]]:
        return {}

    @property
    @abstractmethod
    def table_maximum_payload_size(self) -> typing.Dict[int, BaseMaxPayloadSize]:
        return {}

    @property
    @abstractmethod
    def table_ch_mask_cntl_value(self) -> typing.Dict[int, ChMaskCtrl]:
        return {}

    @abstractmethod
    def get_downlink_datarate(uplink_darate: DataRate, rx1_datarate_offset: int) -> DataRate:
        pass

    def get_datarate_by_sf_bw(self, spreading: int, bandwidth_khz: int) -> typing.Optional[LoRaDataRate]:
        for _, datarate in self.table_datarates.items():
            if (
                isinstance(datarate, LoRaDataRate)
                and datarate.spreading == spreading
                and datarate.bandwidth == bandwidth_khz
            ):
                return datarate

    def get_ch_mask_cntl_by_ch_index(self, index: int) -> int:
        table_index = index // 16

        if (
            table_index not in self.table_ch_mask_cntl_value
            or self.table_ch_mask_cntl_value[table_index]["type"] != "range"
        ):
            raise exceptions.ChMaskCntlError(f"Wrong channel index: {index}")

        return table_index

    def get_uplink_channel_by_index(self, index: int) -> Channel:
        return self.uplink_channels[index]

    def get_uplink_channel_by_freq_khz(self, frequency_khz: int) -> Channel:
        for channel in self.uplink_channels:
            if channel.frequency_khz == frequency_khz:
                return channel

    @abstractmethod
    def get_downlink_channel(self, uplink_channel: Channel) -> Channel:
        pass

    @abstractmethod
    def get_max_payload_size(datarate: DataRate) -> int:
        pass

    @property
    @abstractmethod
    def rx1_delay(self) -> int:
        return 0

    @property
    @abstractmethod
    def rx1_dr_offset(self) -> int:
        return 0

    @property
    @abstractmethod
    def rx2_datarate(self) -> int:
        return 0

    @property
    @abstractmethod
    def rx2_frequency(self) -> int:
        return 0

    @property
    @abstractmethod
    def tx_power(self) -> int:
        return 0

    @property
    @abstractmethod
    def join_accept_delay1(self) -> int:
        return 0

    def __str__(self):
        return self.__class__.__name__
