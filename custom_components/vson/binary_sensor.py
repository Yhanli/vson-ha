from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity

from .entity import VsonEntity


async def async_setup_entry(hass, entry, async_add_entities):
    c = entry.runtime_data
    async_add_entities(e for f in c.feeders for e in (Online(c, f, "online"), FoodLow(c, f, "food_low")))


class Online(VsonEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    @property
    def is_on(self):
        return str(self.status.get("equipmentState")) == "0"  # 0 online, 1 offline


class FoodLow(VsonEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def is_on(self):
        return str(self.status.get("isMaterial")) == "1"  # app: 1 = "shortage of material"
