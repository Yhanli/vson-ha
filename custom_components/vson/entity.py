from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, VsonCoordinator


class VsonEntity(CoordinatorEntity[VsonCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: VsonCoordinator, feeder: dict, key: str) -> None:
        super().__init__(coordinator)
        self.mac = feeder["mac"]
        self._attr_unique_id = f"{self.mac}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.mac)}, name=feeder.get("name") or "Fish feeder",
            manufacturer="VSON", model="WP8621N",
            sw_version=(coordinator.data.get(self.mac) or {}).get("version"))

    @property
    def status(self) -> dict:
        return self.coordinator.data.get(self.mac) or {}
