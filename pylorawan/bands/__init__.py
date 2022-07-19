from . import RP2_1_0_2, RP2_1_0_3
from .interface import Band

RP_AVAILABLE = {
    "RP2_1_0_2": RP2_1_0_2,
    "RP2_1_0_3": RP2_1_0_3,
}


def get_band_by_name(name: str, rp: str = "RP2_1_0_2") -> Band:
    regional_params = RP_AVAILABLE[rp.upper()]
    return regional_params.get_band_by_name(name)


__all__ = [
    "RP2_1_0_2_REV_B",
    "RP2_1_0_3",
    "RP_AVAILABLE",
    "get_band_by_name",
]
