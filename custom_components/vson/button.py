import asyncio

from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError

from .api import VsonError
from .entity import VsonEntity


async def async_setup_entry(hass, entry, async_add_entities):
    c = entry.runtime_data
    async_add_entities(Feed(c, f, "feed") for f in c.feeders)


class Feed(VsonEntity, ButtonEntity):
    async def async_press(self) -> None:
        before = self.status.get("time")
        try:
            await self.coordinator.client.feed(self.mac)
        except VsonError as e:
            raise HomeAssistantError(f"Feed failed: {e}") from e
        self.hass.async_create_background_task(self._await_fed(before), f"vson_feed_{self.mac}")

    async def _await_fed(self, before: str | None) -> None:
        # Feeder reports to cloud ~2s after feeding (measured once); poll until "Last fed" changes, max 20s.
        for _ in range(10):
            await asyncio.sleep(2)
            await self.coordinator.async_refresh()
            if self.status.get("time") != before:
                return
