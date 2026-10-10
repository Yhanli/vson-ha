from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError

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
        await self.coordinator.async_request_refresh()
