import typing

from pylorawan import consts

from ..common import get_range_datarates
from ..interface import (
    AllOnChMaskCtrl,
    Band,
    Channel,
    ChMaskCtrl,
    DataRate,
    Direction,
    FSKDataRate,
    LoRaDataRate,
    LRFHSSDataRate,
    MaxPayloadSize,
    RangeChMaskCtrl,
    RFUChMaskCtrl,
    RFUDataRate,
)


class EU863_870(Band):
    table_datarates: typing.Dict[int, DataRate] = {
        0: LoRaDataRate(index=0, spreading=12, bandwidth=125, direction=Direction.both),
        1: LoRaDataRate(index=1, spreading=11, bandwidth=125, direction=Direction.both),
        2: LoRaDataRate(index=2, spreading=10, bandwidth=125, direction=Direction.both),
        3: LoRaDataRate(index=3, spreading=9, bandwidth=125, direction=Direction.both),
        4: LoRaDataRate(index=4, spreading=8, bandwidth=125, direction=Direction.both),
        5: LoRaDataRate(index=5, spreading=7, bandwidth=125, direction=Direction.both),
        6: LoRaDataRate(index=6, spreading=7, bandwidth=250, direction=Direction.both),
        7: FSKDataRate(index=7, bitrate=50000, direction=Direction.both),
        8: LRFHSSDataRate(
            index=8,
            coding_rate="1/3",
            occupied_channel_width=137000,
            direction=Direction.uplink,
        ),
        9: LRFHSSDataRate(
            index=9,
            coding_rate="2/3",
            occupied_channel_width=137000,
            direction=Direction.uplink,
        ),
        10: LRFHSSDataRate(
            index=10,
            coding_rate="1/3",
            occupied_channel_width=336000,
            direction=Direction.uplink,
        ),
        11: LRFHSSDataRate(
            index=11,
            coding_rate="2/3",
            occupied_channel_width=336000,
            direction=Direction.uplink,
        ),
        12: RFUDataRate(index=12),
        13: RFUDataRate(index=13),
        14: RFUDataRate(index=14),
        15: RFUDataRate(index=15),
    }

    uplink_dwell_time = 1
    downlink_dwell_time = 1

    max_duty_cycle = 0
    max_eirp_index = 5
    table_tx_power: typing.Dict[int, typing.Union[int, consts.RFU]] = {
        0: consts.TableEIRP[max_eirp_index],
        1: consts.TableEIRP[max_eirp_index] - 2,
        2: consts.TableEIRP[max_eirp_index] - 4,
        3: consts.TableEIRP[max_eirp_index] - 6,
        4: consts.TableEIRP[max_eirp_index] - 8,
        5: consts.TableEIRP[max_eirp_index] - 10,
        6: consts.TableEIRP[max_eirp_index] - 12,
        7: consts.TableEIRP[max_eirp_index] - 14,
        # RFU
        8: consts.RFU(),
        9: consts.RFU(),
        10: consts.RFU(),
        11: consts.RFU(),
        12: consts.RFU(),
        13: consts.RFU(),
        14: consts.RFU(),
        15: consts.RFU(),
    }

    table_maximum_payload_size: typing.Dict[int, MaxPayloadSize] = {
        0: MaxPayloadSize(dr=0, n=51),
        1: MaxPayloadSize(dr=1, n=51),
        2: MaxPayloadSize(dr=2, n=51),
        3: MaxPayloadSize(dr=3, n=115),
        4: MaxPayloadSize(dr=4, n=222),
        5: MaxPayloadSize(dr=5, n=222),
        6: MaxPayloadSize(dr=6, n=222),
        7: MaxPayloadSize(dr=7, n=222),
        # 8: Not defined,
        # 9: Not defined,
        # 10: Not defined,
        # 11: Not defined,
        # 12: Not defined,
        # 13: Not defined,
        # 14: Not defined,
        # 15: Not defined,
    }

    table_ch_mask_cntl_value: typing.Dict[int, ChMaskCtrl] = {
        0: RangeChMaskCtrl(index=0, start=0, end=15),
        1: RFUChMaskCtrl(index=1),
        2: RFUChMaskCtrl(index=2),
        3: RFUChMaskCtrl(index=3),
        4: RFUChMaskCtrl(index=4),
        5: RFUChMaskCtrl(index=5),
        6: AllOnChMaskCtrl(index=6),
        7: RFUChMaskCtrl(index=7),
    }

    rx1_delay = 1
    rx1_dr_offset = 0
    rx2_datarate = table_datarates[0]  # DR0 (SF12, 125 kHz)
    rx2_frequency = 8695250  # freq (in hundreds of Hz) = rx2_frequency (in KHz) * 10
    tx_power = table_tx_power[0]  # +16dBm
    join_accept_delay1 = 5

    is_dynamic_channel_plan_region = True
    is_support_tx_param_setup = True

    # Downlink channels for this band are same as Uplink channels.
    uplink_channels = downlink_channels = [
        # Fixed channels
        Channel(
            index=0,
            frequency_khz=868100,
            datarates=get_range_datarates(table_datarates, 0, 6),
            fixed=True,
        ),
        Channel(
            index=1,
            frequency_khz=868300,
            datarates=get_range_datarates(table_datarates, 0, 6),
            fixed=True,
        ),
        Channel(
            index=2,
            frequency_khz=868500,
            datarates=get_range_datarates(table_datarates, 0, 6),
            fixed=True,
        ),
        # Extra datarates
        Channel(
            index=3,
            frequency_khz=867100,
            datarates=get_range_datarates(table_datarates, 0, 6),
            fixed=False,
        ),
        Channel(
            index=4,
            frequency_khz=867500,
            datarates=get_range_datarates(table_datarates, 0, 6),
            fixed=False,
        ),
        Channel(
            index=5,
            frequency_khz=867700,
            datarates=get_range_datarates(table_datarates, 0, 6),
            fixed=False,
        ),
        Channel(
            index=6,
            frequency_khz=867900,
            datarates=get_range_datarates(table_datarates, 0, 6),
            fixed=False,
        ),
        Channel(index=7, frequency_khz=867300, datarates=[table_datarates[6]], fixed=False),
        Channel(index=8, frequency_khz=867700, datarates=[table_datarates[7]], fixed=False),
    ]

    def get_range_datarate(self, uplink_datarate: DataRate, rx1_datarate_offset: int) -> DataRate:
        downlink_dr_index = max(0, uplink_datarate.index - rx1_datarate_offset)
        return self.table_datarates[downlink_dr_index]

    def get_downlink_datarate(self, uplink_datarate: DataRate, rx1_datarate_offset: int) -> DataRate:
        downlink_dr_index = min(max(0, uplink_datarate.index - rx1_datarate_offset), 7)

        return self.table_datarates[downlink_dr_index]

    def get_downlink_channel(self, uplink_channel: Channel) -> Channel:
        index = uplink_channel.index
        return self.downlink_channels[index]

    def get_max_payload_size(self, datarate: DataRate) -> int:
        max_size = self.table_maximum_payload_size[datarate.index]
        return max_size.n
