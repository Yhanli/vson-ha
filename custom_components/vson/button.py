from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_call_later

from .api import VsonError
from .entity import VsonEntity


async def async_setup_entry(hass, entry, async_add_entities):
    c = entry.runtime_data
    async_add_entities(Feed(c, f, "feed") for f in c.feeders)


class Feed(VsonEntity, ButtonEntity):
    async def async_press(self) -> None:
        try:
            await self.coordinator.client.feed(self.mac)
        except VsonError as e:
            raise HomeAssistantError(f"Feed failed: {e}") from e
        # Feeder reports to cloud a few seconds after feeding; re-poll so "Last fed" updates promptly.
        # ponytail: fixed delays (device latency unmeasured); tune if 15s proves too short.
        for delay in (5, 15):
            async_call_later(self.hass, delay, self._refresh)

    async def _refresh(self, _now) -> None:
        await self.coordinator.async_refresh()
