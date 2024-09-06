"""UniFi Hotspot Manager integration."""
from __future__ import annotations

from homeassistant.core import (
    HomeAssistant,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
)
from homeassistant.helpers import (
    config_validation as cv,
)

from .const import (
    DOMAIN,
    PLATFORMS,
)
from .coordinator import UnifiVoucherCoordinator
from .api import (
    UnifiVoucherApiAuthenticationError,
    UnifiVoucherApiAccessError,
)
from .services import (
    async_setup_services,
    async_unload_services,
)

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up platform from a ConfigEntry."""
    try:
        coordinator = UnifiVoucherCoordinator(
            hass=hass,
            config_entry=config_entry,
        )
        await coordinator.initialize()
        await coordinator.async_config_entry_first_refresh()

    except (
        UnifiVoucherApiAuthenticationError,
        UnifiVoucherApiAccessError,
    ) as err:
        raise ConfigEntryAuthFailed from err

    except Exception as err:
        raise ConfigEntryNotReady from err

    config_entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    config_entry.async_on_unload(
        config_entry.add_update_listener(async_reload_entry)
    )

    # Register services
    async_setup_services(hass, coordinator)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )

    # Un-register services
    async_unload_services(hass)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, config_entry)
    await async_setup_entry(hass, config_entry)
