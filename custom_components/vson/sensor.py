from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.util import dt as dt_util

from .entity import VsonEntity


async def async_setup_entry(hass, entry, async_add_entities):
    c = entry.runtime_data
    async_add_entities(LastFed(c, f, "last_fed") for f in c.feeders)


class LastFed(VsonEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self):
        t = dt_util.parse_datetime(self.status.get("time") or "")
        # ponytail: server returns naive local time; assumes HA timezone == feeder/account timezone
        return t.replace(tzinfo=dt_util.get_default_time_zone()) if t else None
