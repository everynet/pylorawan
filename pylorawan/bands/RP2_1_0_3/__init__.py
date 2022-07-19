from ...exceptions import BandError
from ..interface import Band
from .as923 import AS923_2
from .au915_928 import AU915_928, AU915_928A
from .eu863_870 import EU863_870
from .us902_928 import US902_928, US902_928A, US902_928AB

BANDS_AVAILABLE = {
    AS923_2.name: AS923_2,
    AU915_928.name: AU915_928,
    AU915_928A.name: AU915_928A,
    EU863_870.name: EU863_870,
    US902_928.name: US902_928,
    US902_928A.name: US902_928A,
    US902_928AB.name: US902_928AB,
}


def get_band_by_name(name: str) -> Band:
    name = name.upper()
    if name not in BANDS_AVAILABLE:
        raise BandError(f"Band with name: {name!r} doesn't exist in RP: {__name__!r}")
    return BANDS_AVAILABLE[name]


__all__ = [
    "AU915_928",
    "AU915_928A",
    "EU863_870",
    "US902_928",
    "US902_928A",
    "US902_928AB",
    "AS923_2",
    "BANDS_AVAILABLE",
    "get_band_by_name",
]
