LoRaWAN_1_0_2 = "1.0.2"
LoRaWAN_1_0_3 = "1.0.3"
LoRaWAN_1_0_4 = "1.0.4"

LoRaModulation = "lora"
FSKModulation = "fsk"
LRFHSSModulation = "lr-fhss"

TableEIRP = [8, 10, 12, 13, 14, 16, 18, 20, 21, 24, 26, 27, 29, 30, 33, 36]

MAX_F_OPTS_LEN = 15

MAX_RX1_DELAY = 15
MAX_JOIN_ACCEPT_DELAY1 = 5

MAX_RX2_DELAY = MAX_RX1_DELAY + 1
MAX_JOIN_ACCEPT_DELAY2 = MAX_JOIN_ACCEPT_DELAY1 + 1

JOIN_ACCEPT_DELAY1 = 5
MAX_FCNT_GAP = 16384
ADR_ACK_LIMIT = 64
ADR_ACK_DELAY = 32

GPS_EPOCH_DIFF = 315964782  # last leap second 2017-1-1
CLASS_B_TX_DELAY = 0.5
BEACON_LOSS_TIMEOUT = 2 * 60 * 60  # 2 hours
BEACON_INTERVAL = 128
BEACON_RESERVED = 2.120
BEACON_GUARD = 3.0
PING_SLOT_LEN = 0.03
MIN_PING_DATARATE = 0
MAX_PING_DATARATE = 5


class RFU:
    """
    This class represent "Reserved for Future Usage", it must be used for RFU values instead of regular None.
    """

    def __repr__(self):
        return f"{self.__class__.__name__}()"
