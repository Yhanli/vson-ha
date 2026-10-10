"""VSON Smart (WP8621N fish feeder) via VSON cloud."""
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import VsonAuthError, VsonClient, VsonError

DOMAIN = "vson"
PLATFORMS = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SENSOR]
_LOGGER = logging.getLogger(__name__)


class VsonCoordinator(DataUpdateCoordinator[dict[str, dict]]):
    """Polls status for every feeder; data = {mac: status}."""

    def __init__(self, hass: HomeAssistant, client: VsonClient, feeders: list[dict]) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=60))
        self.client = client
        self.feeders = feeders

    async def _async_update_data(self) -> dict[str, dict]:
        try:
            return {d["mac"]: await self.client.status(d["mac"]) for d in self.feeders}
        except VsonAuthError as e:
            raise ConfigEntryAuthFailed(str(e)) from e
        except (VsonError, OSError) as e:
            raise UpdateFailed(str(e)) from e


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = VsonClient(async_get_clientsession(hass), entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])
    try:
        feeders = await client.feeders()
    except VsonAuthError as e:
        raise ConfigEntryAuthFailed(str(e)) from e
    coordinator = VsonCoordinator(hass, client, feeders)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
