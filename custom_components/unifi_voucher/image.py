"""UniFi Hotspot Manager image platform.

Support for QR code for guest WLANs.
"""
from __future__ import annotations

from aiounifi.models.wlan import wlan_qr_code

from homeassistant.core import (
    HomeAssistant,
    callback,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.image import (
    ImageEntity,
    ImageEntityDescription,
)
from homeassistant.helpers.entity import (
    Entity,
    EntityCategory,
)

import homeassistant.util.dt as dt_util

from .const import (
    LOGGER,
    DOMAIN,
    CONF_WLAN_NAME,
    ATTR_QR_CODE,
)
from .coordinator import UnifiVoucherCoordinator
from .entity import UnifiVoucherEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: Entity,
) -> None:
    """Do setup sensors from a config entry created in the integrations UI."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    entity_descriptions = [
        ImageEntityDescription(
            key=ATTR_QR_CODE,
            translation_key=ATTR_QR_CODE,
            icon="mdi:qrcode",
            device_class=None,
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
    ]

    async_add_entities(
        [
            UnifiVoucherImage(
                coordinator=coordinator,
                entity_description=entity_description,
            )
            for entity_description in entity_descriptions
        ],
        update_before_add=True,
    )


class UnifiVoucherImage(UnifiVoucherEntity, ImageEntity):
    """Representation of a UniFi Hotspot Manager image."""

    _attr_content_type = "image/png"
    _attr_entity_registry_enabled_default = False

    cached_image: bytes | None = None
    current_wlan_name: str | None = None

    def __init__(
        self,
        coordinator: UnifiVoucherCoordinator,
        entity_description: ImageEntityDescription,
    ) -> None:
        """Initialize the image class."""
        super().__init__(
            coordinator=coordinator,
            entity_type="image",
            entity_key=entity_description.key,
        )
        ImageEntity.__init__(self, coordinator.hass)
        self.entity_description = entity_description
        self.current_wlan_name = coordinator.config_entry.options.get(CONF_WLAN_NAME, "")
        self._attr_image_last_updated = dt_util.utcnow()

    def _update_extra_state_attributes(self) -> None:
        """Update extra attributes."""
        self._additional_extra_state_attributes = {
            CONF_WLAN_NAME: self.current_wlan_name,
        }

    def image(self) -> bytes | None:
        """Return bytes of image."""
        if self.cached_image is None:
            self.cached_image = wlan_qr_code(
                name=self.current_wlan_name,
                password=None,
            )
        return self.cached_image

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return True if self.current_wlan_name else False

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (_wlan_name := self.coordinator.get_wlan_name()) != self.current_wlan_name:
            LOGGER.debug("Guest WLAN name changed to %s", _wlan_name)

            self.current_wlan_name = _wlan_name
            self._attr_image_last_updated = dt_util.utcnow()
            self.cached_image = None

        super()._handle_coordinator_update()
