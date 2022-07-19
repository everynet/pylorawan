# Python LoRaWAN protocol library

The library supports LoRaWAN 1.0.x protocol versions.

We've done our best to follow interfaces and field naming conventions the same way as they are defined in the LoRaWAN specification.

Please bear in mind, that this library is still work in progress


### Modules

#### `pylorawan.message`

This module contains objects concerning the structure of LoRaWAN messages, such as:

- `PHYPayload`
- `MACPayloadUplink`
- `MACPayloadDownlink`
- `JoinRequest`
- `JoinAccept`
- `MHDR`
- e.t.c.

#### `pylorawan.common`

This module contains common functions, that help working with encoding/decoding AES128 data like `FMRPayload`, or check and verify `MIC`


### `pylorawan.bands`

This module is work in progress and it contains the following LoRaWAN Regional Parameters for the bands:

- RP2_1_0_2
    - AS923
    - AU915-928
    - EU863-870
    - US902-928
- RP2_1_0_3
    - AS923-2
    - AU915-928
    - EU863-870
    - US902-928

## Code examples

This section illustrates how the following messages can be generated:

- [Generate JoinRequest](#How-to-generate-a-join-request)
- [Generate JoinAccept](#How-to-generate-a-join-accept)
- [Generate Uplink](#How-to-generate-an-uplink)
- [Generate Downlink](#How-to-generate-downlink)
- [Parse PHYPaload](#Parsing-PHYPayload-that-contains-Uplink-or-Downlink-or-JoinRequest-message)
- [Parse JoinAccept](#Parsing-JoinAccept-message)

### How to generate a join-request
```python
import pylorawan

dev_eui = 0x264BBE386884C5B1
join_eui = 0x36CC25B0B06B4FF3

app_key = 0xCCDBB4A27AA30F26B14902075AC627C5 .to_bytes(16, "big")

dev_nonce = 123

# Generate mhdr
mtype = pylorawan.message.MType.JoinRequest
mhdr = pylorawan.message.MHDR(mtype=mtype, major=0)

join_req = pylorawan.message.JoinRequest(join_eui, dev_eui, dev_nonce)

mic = pylorawan.common.generate_mic_join_request(mhdr, join_req, app_key)

phy_payload = pylorawan.message.PHYPayload(mhdr=mhdr, payload=join_req, mic=mic)
raw_bytes_join_request_msg = phy_payload.generate()
```

### How to generate a join-accept
```python
import pylorawan

dev_addr = 0xFA83B2A1
app_key = 0xCCDBB4A27AA30F26B14902075AC627C5 .to_bytes(16, "big")
app_nonce = 0xFAFAFA

net_id = 0xB
rx1_delay = 1
rx1_dr_offset = 0
rx2_datarate = 0

dl_settings = pylorawan.message.DLSettings(
    rx1_dr_offset=rx1_dr_offset, rx2_datarate=rx2_datarate
)
cf_list = b""

join_accept = pylorawan.message.JoinAccept(
    app_nonce=app_nonce,
    net_id=net_id,
    dev_addr=dev_addr,
    dl_settings=dl_settings,
    rx_delay=rx1_delay,
    cf_list=cf_list,
)

raw_bytes_join_accept_msg = join_accept.generate(app_key=app_key)
```

### How to generate an uplink

```python
import pylorawan

dev_addr = 0xFA83B2A1
app_s_key = 0xB03E77747853D8C9610C355AE0873212 .to_bytes(16, "big")
nwk_s_key = 0x65C4660F6CF17E89F696AC27D731F809 .to_bytes(16, "big")

f_cnt = 1
f_port = 1
f_opts = b""
direction = 0

# Generate mhdr
mtype = pylorawan.message.MType.UnconfirmedDataUp
mhdr = pylorawan.message.MHDR(mtype=mtype, major=0)

# Generate MACPayload
encrypted_frm_payload = pylorawan.common.encrypt_frm_payload(
    frm_payload, app_s_key, dev_addr, f_cnt, direction
)

f_ctrl = pylorawan.message.FCtrlUplink(
    adr=True, adr_ack_req=False, ack=False, class_b=False, f_opts_len=0
)
fhdr = pylorawan.message.FHDRUplink(
    dev_addr=dev_addr, f_ctrl=f_ctrl, f_cnt=f_cnt, f_opts=f_opts
)

mac_payload = pylorawan.message.MACPayloadUplink(
    fhdr=fhdr, f_port=f_port, frm_payload=encrypted_frm_payload
)

# Geneerate MIC
mic = pylorawan.common.generate_mic_mac_payload(mhdr, mac_payload, nwk_s_key)

# Generate PHYPayload
phy_payload = pylorawan.message.PHYPayload(mhdr=mhdr, payload=mac_payload, mic=mic)
raw_bytes_uplink_msg = phy_payload.generate()
```

### How to generate downlink

```python
import pylorawan

dev_addr = 0xFA83B2A1
nwk_s_key = 0x65C4660F6CF17E89F696AC27D731F809.to_bytes(16, "big")

adr_bit = True
ack_bit = False
f_pending = False
f_opts_len = 0
f_opts = b""

f_cnt = 1
f_port = 1
frm_payload = b"fafa"

# Generate mhdr
mtype = pylorawan.message.MType.UnconfirmedDataDown
mhdr = pylorawan.message.MHDR(mtype=mtype, major=0)

# Generate MACPayload
f_ctrl = pylorawan.message.FCtrlDownlink(
    adr=adr,
    ack=ack_bit,
    f_pending=f_pending,
    f_opts_len=f_opts_len,
)

fhdr = pylorawan.message.FHDRDownlink(
    dev_addr=dev_addr, f_ctrl=f_ctrl, f_cnt=f_cnt, f_opts=f_opts
)

encrypted_frm_payload = pylorawan.common.encrypt_frm_payload(
    frm_payload, nwk_s_key, dev_addr, f_cnt, 1
)

mac_payload = pylorawan.message.MACPayloadDownlink(
    fhdr=fhdr, f_port=f_port, frm_payload=encrypted_frm_payload
)

# Generate MIC
mic = pylorawan.common.generate_mic_mac_payload(
    mhdr, mac_payload, nwk_s_key
)

# Generate PHYPayload
phy_payload = pylorawan.message.PHYPayload(mhdr=mhdr, payload=mac_payload, mic=mic)

raw_bytes_downlink_msg = phy_payload.generate()
```

### Parsing PHYPayload, that contains Uplink or Downlink or JoinRequest message


```python 
import pylorawan

data = b"\x00\xf4h\x8bOb\xcf\xed<O\x17\xd7\x93\x8c\x1b\xbezm\xe0K\xbbWe"

phy_payload = pylorawan.message.PHYPayload.parse(data)
```

### Parsing JoinAccept message

```python
import pylorawan

data = b"@\x02*\x04r\x80\x13\x04\x01\xec\xf1\xdb7"
app_key = 0xCCDBB4A27AA30F26B14902075AC627C5 .to_bytes(16, "big")

join_accept = pylorawan.message.JoinAccept.parse(data, app_key)
```
