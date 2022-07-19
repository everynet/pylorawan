import typing
from copy import deepcopy

from pylorawan import consts

from ..interface import (
    Band,
    Channel,
    ChMaskCtrl,
    DataRate,
    Direction,
    LoRaDataRate,
    LRFHSSDataRate,
    MaxPayloadSize,
    Off125kHzChMaskCtrl,
    On125kHzChMaskCtrl,
    RangeChMaskCtrl,
    RFUChMaskCtrl,
    RFUDataRate,
)


###########
# Helpers #
###########
def calculate_uplink_channels(table_datarates: typing.Dict[int, DataRate]) -> typing.List[Channel]:
    channels = []

    # 64 channels utilizing LoRa 125 kHz BW
    starting_frequency_125bw_khz = 902300
    step_for_125bw_khz = 200
    datarates = [table_datarates[i] for i in range(4)]
    for index in range(64):
        channels.append(
            Channel(
                index=index,
                frequency_khz=starting_frequency_125bw_khz + index * step_for_125bw_khz,
                datarates=datarates,
            )
        )

    # 8 channels 64-71 utilizing LoRa 500 kHz BW
    starting_frequency_500bw_khz = 903000
    step_for_500bw_khz = 1600
    datarates = [table_datarates[4]]
    for offset, index in enumerate(range(64, 72)):
        channels.append(
            Channel(
                index=index,
                frequency_khz=starting_frequency_500bw_khz + offset * step_for_500bw_khz,
                datarates=datarates,
            )
        )

    return channels


def calculate_downlink_channels(table_datarates: typing.Dict[int, DataRate]) -> typing.List[Channel]:
    starting_frequency_khz = 923000
    step_khz = 600

    datarates = [table_datarates[i] for i in range(8, 14)]

    return [
        Channel(
            index=index,
            frequency_khz=starting_frequency_khz + index * step_khz,
            datarates=datarates,
        )
        for index in range(8)
    ]


def calculate_uplink_channels_for_subband_a(
    channels: typing.List[Channel],
) -> typing.List[Channel]:
    def modify_uplink_channel(channel: Channel) -> Channel:
        if channel.index >= 8:
            channel.is_used = False
        else:
            channel.is_used = True
        return channel

    return [modify_uplink_channel(deepcopy(ch)) for ch in channels]


def calculate_uplink_channels_for_subband_ab(
    channels: typing.List[Channel],
) -> typing.List[Channel]:
    def modify_uplink_channel(channel: Channel) -> Channel:
        # Only channels [2..5], [10..13] and 64 are used in this subband
        if 2 <= channel.index <= 5 or 10 <= channel.index <= 13 or channel.index == 64:
            channel.is_used = True
        else:
            channel.is_used = False
        return channel

    return [modify_uplink_channel(deepcopy(ch)) for ch in channels]


class US902_928(Band):
    table_datarates: typing.Dict[int, DataRate] = {
        0: LoRaDataRate(index=0, spreading=10, bandwidth=125, direction=Direction.uplink),
        1: LoRaDataRate(index=1, spreading=9, bandwidth=125, direction=Direction.uplink),
        2: LoRaDataRate(index=2, spreading=8, bandwidth=125, direction=Direction.uplink),
        3: LoRaDataRate(index=3, spreading=7, bandwidth=125, direction=Direction.uplink),
        4: LoRaDataRate(index=4, spreading=8, bandwidth=500, direction=Direction.uplink),
        5: LRFHSSDataRate(
            index=5,
            coding_rate="1/3",
            occupied_channel_width=1523000,
            direction=Direction.uplink,
        ),
        6: LRFHSSDataRate(
            index=6,
            coding_rate="2/3",
            occupied_channel_width=1523000,
            direction=Direction.uplink,
        ),
        7: RFUDataRate(index=7),
        8: LoRaDataRate(index=8, spreading=12, bandwidth=500, direction=Direction.downlink),
        9: LoRaDataRate(index=9, spreading=11, bandwidth=500, direction=Direction.downlink),
        10: LoRaDataRate(index=10, spreading=10, bandwidth=500, direction=Direction.downlink),
        11: LoRaDataRate(index=11, spreading=9, bandwidth=500, direction=Direction.downlink),
        12: LoRaDataRate(index=12, spreading=8, bandwidth=500, direction=Direction.downlink),
        13: LoRaDataRate(index=13, spreading=7, bandwidth=500, direction=Direction.downlink),
        14: RFUDataRate(index=14),
        15: RFUDataRate(index=15),
    }

    uplink_dwell_time = 1
    downlink_dwell_time = 1

    max_duty_cycle = 0
    max_eirp_index = 13
    table_tx_power: typing.Dict[int, typing.Union[int, consts.RFU]] = {
        0: consts.TableEIRP[max_eirp_index],
        1: consts.TableEIRP[max_eirp_index] - 2,
        2: consts.TableEIRP[max_eirp_index] - 4,
        3: consts.TableEIRP[max_eirp_index] - 6,
        4: consts.TableEIRP[max_eirp_index] - 8,
        5: consts.TableEIRP[max_eirp_index] - 10,
        6: consts.TableEIRP[max_eirp_index] - 12,
        7: consts.TableEIRP[max_eirp_index] - 14,
        8: consts.TableEIRP[max_eirp_index] - 16,
        9: consts.TableEIRP[max_eirp_index] - 18,
        10: consts.TableEIRP[max_eirp_index] - 20,
        # RFU
        11: consts.RFU(),
        12: consts.RFU(),
        13: consts.RFU(),
        14: consts.RFU(),
        15: consts.RFU(),
    }

    table_maximum_payload_size: typing.Dict[int, MaxPayloadSize] = {
        0: MaxPayloadSize(dr=0, n=11),
        1: MaxPayloadSize(dr=1, n=53),
        2: MaxPayloadSize(dr=2, n=125),
        3: MaxPayloadSize(dr=3, n=242),
        4: MaxPayloadSize(dr=4, n=242),
        # 5: Not defined,
        # 6: Not defined,
        # 7: Not defined,
        8: MaxPayloadSize(dr=8, n=33),
        9: MaxPayloadSize(dr=9, n=109),
        10: MaxPayloadSize(dr=10, n=222),
        11: MaxPayloadSize(dr=11, n=222),
        12: MaxPayloadSize(dr=12, n=222),
        13: MaxPayloadSize(dr=12, n=222),
        # 14: Not defined,
        # 15: Not defined,
    }

    table_ch_mask_cntl_value: typing.Dict[int, ChMaskCtrl] = {
        0: RangeChMaskCtrl(index=0, start=0, end=15),
        1: RangeChMaskCtrl(index=1, start=16, end=31),
        2: RangeChMaskCtrl(index=2, start=32, end=47),
        3: RangeChMaskCtrl(index=3, start=48, end=63),
        4: RangeChMaskCtrl(index=4, start=64, end=71),
        5: RFUChMaskCtrl(index=5),
        6: On125kHzChMaskCtrl(index=6),
        7: Off125kHzChMaskCtrl(index=7),
    }

    rx1_delay = 1
    rx1_dr_offset = 0
    rx2_datarate = table_datarates[8]
    rx2_frequency = 9233000  # freq (in hundreds of Hz) = rx2_frequency (in KHz) * 10
    tx_power = table_tx_power[0]
    join_accept_delay1 = 5

    is_dynamic_channel_plan_region = False
    is_support_tx_param_setup = True

    uplink_channels = calculate_uplink_channels(table_datarates)
    downlink_channels = calculate_downlink_channels(table_datarates)

    def get_downlink_datarate(self, uplink_datarate: DataRate, rx1_datarate_offset: int) -> DataRate:
        downlink_dr_index = min(max(8, 10 + uplink_datarate.index - rx1_datarate_offset), 13)
        return self.table_datarates[downlink_dr_index]

    def get_downlink_channel(self, uplink_channel: Channel) -> Channel:
        index = uplink_channel.index % 8
        return self.downlink_channels[index]

    def get_max_payload_size(self, datarate: DataRate) -> int:
        max_size = self.table_maximum_payload_size[datarate.index]
        return max_size.n


class US902_928A(US902_928):
    uplink_channels = calculate_uplink_channels_for_subband_a(US902_928.uplink_channels)


class US902_928AB(US902_928):
    uplink_channels = calculate_uplink_channels_for_subband_ab(US902_928.uplink_channels)
