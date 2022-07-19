class LoRaError(Exception):
    pass


class ParseMessageError(LoRaError):
    pass


class MACCommandParseError(LoRaError):
    pass


class MACCommandCreateError(LoRaError):
    pass


class MACCommandLoadFromDictError(LoRaError):
    pass


class MHDRError(LoRaError):
    pass


class PHYPayloadError(LoRaError):
    pass


class MACPayloadError(LoRaError):
    pass


class JoinRequestError(LoRaError):
    pass


class JoinAcceptError(LoRaError):
    pass


class DeviceError(LoRaError):
    pass


class BandError(LoRaError):
    pass


class ChMaskCntlError(BandError):
    pass


class MICError(LoRaError):
    pass
