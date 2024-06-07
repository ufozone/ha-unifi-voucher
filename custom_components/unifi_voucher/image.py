"""UniFi Hotspot Manager image platform.

Support for QR code for guest WLANs.
"""
from __future__ import annotations

import io
import os
import segno

from PIL import Image

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
    coordinator = config_entry.runtime_data
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
            img_byte_arr = io.BytesIO()
            qrcode_content = segno.helpers.make_wifi_data(
                ssid=self.current_wlan_name,
                password=None,
                security="nopass",
            )
            img_qrcode = segno.make(qrcode_content, error='h')
            img_qrcode.save(
                out=img_byte_arr,
                kind="png",
                scale=5,
            )
            # QR code logo is given
            if (_qrcode_logo_path := self.coordinator.get_qrcode_logo_path()) and os.path.isfile(_qrcode_logo_path):
                img_byte_arr.seek(0)  # Important to let Pillow load the PNG
                img_qrcode = Image.open(img_byte_arr)
                img_qrcode = img_qrcode.convert("RGB")  # Ensure colors for the output
                img_width, img_height = img_qrcode.size
                logo_max_size = img_height // 3
                img_logo = Image.open(_qrcode_logo_path, "r")
                img_logo.thumbnail((logo_max_size, logo_max_size)) # Resize the logo to logo_max_size
                img_qrcode.paste(
                    img_logo, ((img_width - img_logo.size[0]) // 2, (img_height - img_logo.size[1]) // 2), img_logo
                )
                img_byte_arr = io.BytesIO()
                img_qrcode.save(
                    img_byte_arr,
                    format="PNG",
                    #optimize=True,
                    #compress_level=9,
                )
            self.cached_image = img_byte_arr.getvalue()
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
