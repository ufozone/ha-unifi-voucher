"""Diagnostics support for UniFi Hotspot Manager."""
from __future__ import annotations

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import (
    CONF_PASSWORD,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

TO_REDACT = {
    CONF_PASSWORD,
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> dict[str, any]:
    """Return diagnostics of the config entry and coordinator data."""
    coordinator = config_entry.runtime_data
    diagnostics_data = {
        "config_entry_data": async_redact_data(config_entry.as_dict(), TO_REDACT),
        "coordinator_vouchers": coordinator.vouchers,
        "coordinator_latest_voucher_id": coordinator.latest_voucher_id,
    }

    return diagnostics_data
