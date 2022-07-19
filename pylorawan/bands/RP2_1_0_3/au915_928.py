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
    MaxPayloadSizeWithDwell,
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
    starting_frequency_125bw_khz = 915200
    step_for_125bw_khz = 200
    datarates = [table_datarates[i] for i in range(6)]
    for index in range(64):
        channels.append(
            Channel(
                index=index,
                frequency_khz=starting_frequency_125bw_khz + index * step_for_125bw_khz,
                datarates=datarates,
            )
        )

    # 8 channels 64-71 utilizing LoRa 500 kHz BW
    starting_frequency_500bw_khz = 915900
    step_for_500bw_khz = 1600
    datarates = [table_datarates[6]]
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
    starting_frequency_khz = 923300
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


class AU915_928(Band):
    table_datarates: typing.Dict[int, DataRate] = {
        0: LoRaDataRate(index=0, spreading=12, bandwidth=125, direction=Direction.uplink),
        1: LoRaDataRate(index=1, spreading=11, bandwidth=125, direction=Direction.uplink),
        2: LoRaDataRate(index=2, spreading=10, bandwidth=125, direction=Direction.uplink),
        3: LoRaDataRate(index=3, spreading=9, bandwidth=125, direction=Direction.uplink),
        4: LoRaDataRate(index=4, spreading=8, bandwidth=125, direction=Direction.uplink),
        5: LoRaDataRate(index=5, spreading=7, bandwidth=125, direction=Direction.uplink),
        6: LoRaDataRate(index=6, spreading=8, bandwidth=500, direction=Direction.uplink),
        7: LRFHSSDataRate(
            index=7,
            coding_rate="1/3",
            occupied_channel_width=1523000,
            direction=Direction.uplink,
        ),
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

    table_maximum_payload_size: typing.Dict[int, MaxPayloadSizeWithDwell] = {
        0: MaxPayloadSizeWithDwell(dr=0, n_dwell_0=51, n_dwell_1=None),
        1: MaxPayloadSizeWithDwell(dr=1, n_dwell_0=51, n_dwell_1=None),
        2: MaxPayloadSizeWithDwell(dr=2, n_dwell_0=115, n_dwell_1=11),
        3: MaxPayloadSizeWithDwell(dr=3, n_dwell_0=222, n_dwell_1=53),
        4: MaxPayloadSizeWithDwell(dr=4, n_dwell_0=222, n_dwell_1=125),
        5: MaxPayloadSizeWithDwell(dr=5, n_dwell_0=222, n_dwell_1=222),
        6: MaxPayloadSizeWithDwell(dr=5, n_dwell_0=222, n_dwell_1=222),
        7: MaxPayloadSizeWithDwell(dr=5, n_dwell_0=50, n_dwell_1=50),
        8: MaxPayloadSizeWithDwell(dr=5, n_dwell_0=53, n_dwell_1=53),
        9: MaxPayloadSizeWithDwell(dr=5, n_dwell_0=129, n_dwell_1=129),
        10: MaxPayloadSizeWithDwell(dr=5, n_dwell_0=222, n_dwell_1=222),
        11: MaxPayloadSizeWithDwell(dr=5, n_dwell_0=222, n_dwell_1=222),
        12: MaxPayloadSizeWithDwell(dr=5, n_dwell_0=222, n_dwell_1=222),
        13: MaxPayloadSizeWithDwell(dr=5, n_dwell_0=222, n_dwell_1=222),
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
        downlink_dr_index = min(max(8, 8 + uplink_datarate.index - rx1_datarate_offset), 13)

        return self.table_datarates[downlink_dr_index]

    def get_downlink_channel(self, uplink_channel: Channel) -> Channel:
        index = uplink_channel.index % 8
        return self.downlink_channels[index]

    def get_max_payload_size(self, datarate: DataRate, dwell_time: int = 0) -> int:
        max_size = self.table_maximum_payload_size[datarate.index]
        if dwell_time == 0:
            return max_size.n_dwell_0
        elif dwell_time == 1:
            return max_size.n_dwell_1
        else:
            raise ValueError(f"Invalid value {dwell_time=!r}, must be 0 or 1")


class AU915_928A(AU915_928):
    uplink_channels = calculate_uplink_channels_for_subband_a(AU915_928.uplink_channels)
