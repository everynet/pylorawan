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
    MaxPayloadSizeWithDwell,
    RangeChMaskCtrl,
    RFUChMaskCtrl,
    RFUDataRate,
)


class AS923(Band):
    table_datarates: typing.Dict[int, DataRate] = {
        0: LoRaDataRate(index=0, spreading=12, bandwidth=125, direction=Direction.both),
        1: LoRaDataRate(index=1, spreading=11, bandwidth=125, direction=Direction.both),
        2: LoRaDataRate(index=2, spreading=10, bandwidth=125, direction=Direction.both),
        3: LoRaDataRate(index=3, spreading=9, bandwidth=125, direction=Direction.both),
        4: LoRaDataRate(index=4, spreading=8, bandwidth=125, direction=Direction.both),
        5: LoRaDataRate(index=5, spreading=7, bandwidth=125, direction=Direction.both),
        6: LoRaDataRate(index=6, spreading=7, bandwidth=250, direction=Direction.both),
        7: FSKDataRate(index=7, bitrate=50000, direction=Direction.both),
        8: RFUDataRate(index=8),
        9: RFUDataRate(index=9),
        10: RFUDataRate(index=10),
        11: RFUDataRate(index=11),
        12: RFUDataRate(index=12),
        13: RFUDataRate(index=13),
        14: RFUDataRate(index=14),
        15: RFUDataRate(index=15),
    }

    uplink_dwell_time = 0
    downlink_dwell_time = 0

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

    # The maximum application payload length in the absence of the optional FOpt control field (N).
    table_maximum_payload_size: typing.Dict[int, MaxPayloadSizeWithDwell] = {
        0: MaxPayloadSizeWithDwell(dr=0, n_dwell_0=51, n_dwell_1=None),
        1: MaxPayloadSizeWithDwell(dr=1, n_dwell_0=51, n_dwell_1=None),
        2: MaxPayloadSizeWithDwell(dr=2, n_dwell_0=51, n_dwell_1=11),
        3: MaxPayloadSizeWithDwell(dr=3, n_dwell_0=115, n_dwell_1=53),
        4: MaxPayloadSizeWithDwell(dr=4, n_dwell_0=222, n_dwell_1=125),
        5: MaxPayloadSizeWithDwell(dr=5, n_dwell_0=222, n_dwell_1=242),
        6: MaxPayloadSizeWithDwell(dr=6, n_dwell_0=222, n_dwell_1=242),
        7: MaxPayloadSizeWithDwell(dr=7, n_dwell_0=222, n_dwell_1=242),
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
    rx2_datarate = table_datarates[2]  # DR2 (SF10/125KHz)
    rx2_frequency = 9232000  # freq (in hundreds of Hz) = rx2_frequency (in KHz) * 10
    tx_power = table_tx_power[0]  # +16dBm
    join_accept_delay1 = 5

    is_dynamic_channel_plan_region = True
    is_support_tx_param_setup = True

    # Downlink channels for this band are same as Uplink channels.
    uplink_channels = downlink_channels = [
        # Fixed channels
        Channel(
            index=0,
            frequency_khz=923200,
            datarates=get_range_datarates(table_datarates, 0, 6),
            fixed=True,
        ),
        Channel(
            index=1,
            frequency_khz=923400,
            datarates=get_range_datarates(table_datarates, 0, 6),
            fixed=True,
        ),
        # Extra channels
        Channel(
            index=2,
            frequency_khz=923000,
            datarates=get_range_datarates(table_datarates, 0, 6),
            fixed=False,
        ),
        Channel(
            index=3,
            frequency_khz=923600,
            datarates=get_range_datarates(table_datarates, 0, 6),
            fixed=False,
        ),
        Channel(
            index=4,
            frequency_khz=923800,
            datarates=get_range_datarates(table_datarates, 0, 6),
            fixed=False,
        ),
        Channel(index=5, frequency_khz=924000, datarates=[table_datarates[6]], fixed=False),
        Channel(
            index=6,
            frequency_khz=924200,
            datarates=get_range_datarates(table_datarates, 0, 6),
            fixed=False,
        ),
        Channel(index=7, frequency_khz=924400, datarates=[table_datarates[7]], fixed=False),
    ]

    # TODO: ensure, there is no extra logic required here (based on DownlinkDwellTime cases).
    def get_downlink_datarate(self, uplink_datarate: DataRate, rx1_datarate_offset: int) -> DataRate:
        downlink_dr_index = min(5, max(0, uplink_datarate.index - rx1_datarate_offset))
        return self.table_datarates[downlink_dr_index]

    def get_downlink_channel(self, uplink_channel: Channel) -> Channel:
        index = uplink_channel.index
        return self.downlink_channels[index]

    def get_max_payload_size(self, datarate: DataRate, dwell_time: int = 0) -> int:
        max_size = self.table_maximum_payload_size[datarate.index]
        if dwell_time == 0:
            return max_size.n_dwell_0
        elif dwell_time == 1:
            return max_size.n_dwell_1
        else:
            raise ValueError(f"Invalid value {dwell_time=!r}, must be 0 or 1")
