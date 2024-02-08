"""UniFi Hotspot Manager entity."""
from __future__ import annotations

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import (
    DOMAIN,
    MANUFACTURER,
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

        self._entry_id = coordinator.get_entry_id()
        self._entity_type = entity_type
        self._entity_key = entity_key

        if entity_key:
            self._unique_id = slugify(f"{self._entry_id}_{entity_key}")
        else:
            self._unique_id = slugify(f"{self._entry_id}")

        self._additional_extra_state_attributes = {}
        self.entity_id = f"{entity_type}.{self._unique_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={
                (DOMAIN, self._entry_id)
            },
            name=self.coordinator.get_entry_title(),
            manufacturer=MANUFACTURER,
            configuration_url=self.coordinator.get_configuration_url(),
        )

    def _update_extra_state_attributes(self) -> None:
        """Update extra attributes."""
        self._additional_extra_state_attributes = {}

    def _update_handler(self) -> None:
        """Handle updated data."""
        self._update_extra_state_attributes()

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._unique_id

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator._available

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return axtra attributes."""
        _extra_state_attributes = self._additional_extra_state_attributes
        _extra_state_attributes.update(
            {
                ATTR_LAST_PULL: self.coordinator._last_pull,
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
