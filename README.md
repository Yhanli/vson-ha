# VSON Smart for Home Assistant

Unofficial cloud integration for VSON Smart WiFi fish feeders (tested: **WP8621N** "Intelligent fish feeder").

## Entities (per feeder)

| Entity | Type | Notes |
|---|---|---|
| Feed | button | Drops one portion |
| Online | binary_sensor (connectivity) | From VSON cloud |
| Food low | binary_sensor (problem) | Feeder's shortage sensor |
| Last fed | sensor (timestamp) | Assumes HA timezone = feeder's timezone |

Polls the VSON cloud every 60 s. Feeding schedules: use HA automations with the Feed button.

## Install

HACS → ⋮ → Custom repositories → add this repo (category: Integration) → install → restart HA →
Settings → Devices & services → Add integration → **VSON Smart**.

Account name is **case-sensitive**. Logging in from HA may log the phone app out; the cleanest setup is a
second VSON account with the feeder shared to it.

## Test the client without HA

```
pip install aiohttp cryptography
python custom_components/vson/api.py          # list feeders + status
python custom_components/vson/api.py --feed   # feed once
```

Credentials from env `VSON_USER` / `VSON_PASS` or a `.vsonconfig` file (`KEY=value` lines) in the current dir.

Not affiliated with VSON.
