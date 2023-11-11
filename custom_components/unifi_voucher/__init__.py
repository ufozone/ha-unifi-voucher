"""UniFi Hotspot Manager integration."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
)

from .const import (
    DOMAIN,
    PLATFORMS,
)
from .coordinator import UnifiVoucherCoordinator


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up UniFi Hotspot Manager component."""
    hass.data.setdefault(DOMAIN, {})

    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})

    try:
        coordinator = UnifiVoucherCoordinator(
            hass=hass,
            config_entry=config_entry,
        )
        await coordinator.initialize()
        await coordinator.async_config_entry_first_refresh()

    except AuthenticationRequired as err:
        raise ConfigEntryAuthFailed from err

    except Exception as err:
        raise ConfigEntryNotReady from err

    hass.data[DOMAIN][config_entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    config_entry.async_on_unload(config_entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS):
        # Remove config entry from domain.
        hass.data[DOMAIN].pop(config_entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, config_entry)
    await async_setup_entry(hass, config_entry)
