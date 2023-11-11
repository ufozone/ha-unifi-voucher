"""UniFi Hotspot Manager entity."""
from __future__ import annotations

from homeassistant.core import callback
from homeassistant.const import (
    ATTR_CONFIGURATION_URL,
    ATTR_NAME,
    ATTR_IDENTIFIERS,
    ATTR_MANUFACTURER,
    ATTR_STATE,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import (
    DOMAIN,
    MANUFACTURER,
    ATTR_EXTRA_STATE_ATTRIBUTES,
    ATTR_AVAILABLE,
    ATTR_LAST_PULL,
)
from .coordinator import UnifiVoucherCoordinator


class UnifiVoucherEntity(CoordinatorEntity):
    """UniFi Hotspot Manager class."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: UnifiVoucherCoordinator,
        entity_type: str,
        entity_key: str,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)

        self._host = "unifi_voucher" # TODO
        self._entity_type = entity_type
        self._entity_key = entity_key

        if entity_key:
            self._unique_id = slugify(f"{self._host}_{entity_key}")
        else:
            self._unique_id = slugify(f"{self._host}")

        self.entity_id = f"{entity_type}.{self._unique_id}"

    def _get_state(
        self,
    ) -> any:
        """Get state of the current entity."""
        return self.coordinator.data.get(self._entity_key, {}).get(ATTR_STATE, None)

    def _get_attribute(
        self,
        attr: str,
        default_value: any | None = None,
    ) -> any:
        """Get attribute of the current entity."""
        return self.coordinator.data.get(self._entity_key, {}).get(attr, default_value)

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._unique_id

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.data.get(ATTR_AVAILABLE)

    @property
    def device_info(self):
        """Return the device info."""
        return {
            ATTR_IDENTIFIERS: {
                (DOMAIN, self._host)
            },
            ATTR_NAME: self._host,
            ATTR_MANUFACTURER: MANUFACTURER,
        }

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return axtra attributes."""
        _extra_state_attributes = self._get_attribute(ATTR_EXTRA_STATE_ATTRIBUTES, {})
        _extra_state_attributes.update(
            {
                ATTR_LAST_PULL: self.coordinator.data.get(ATTR_LAST_PULL),
            }
        )
        return _extra_state_attributes

    async def async_update(self) -> None:
        """Peform async_update."""
        self._update_handler()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_handler()
        self.async_write_ha_state()

    def _update_handler(self) -> None:
        """Handle updated data."""
