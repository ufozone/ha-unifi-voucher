"""UniFi Hotspot Manager sensor platform."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.helpers.entity import Entity

from .const import (
    DOMAIN,
    ATTR_VOUCHER,
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
        SensorEntityDescription(
            key=ATTR_VOUCHER,
            translation_key=ATTR_VOUCHER,
            icon="mdi:numeric",
            device_class=None,
        ),
    ]

    async_add_entities(
        [
            UnifiVoucherSensor(
                coordinator=coordinator,
                entity_description=entity_description,
            )
            for entity_description in entity_descriptions
        ],
        update_before_add=True,
    )


class UnifiVoucherSensor(UnifiVoucherEntity, SensorEntity):
    """Representation of a UniFi Hotspot Manager sensor."""

    def __init__(
        self,
        coordinator: UnifiVoucherCoordinator,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(
            coordinator=coordinator,
            entity_type="sensor",
            entity_key=entity_description.key,
        )
        self.entity_description = entity_description

    def _get_latest_voucher(self) -> dict[str, any] | None:
        """Get last voucher."""
        if (voucher_id := self.coordinator.latest_voucher_id) in self.coordinator.vouchers:
            return self.coordinator.vouchers[voucher_id]

        return None

    def _update_extra_state_attributes(self) -> None:
        """Update extra attributes."""
        if (voucher := self._get_latest_voucher()) is None:
            return None

        _x = {
            "quota": voucher.get("quota"),
            "used": voucher.get("used"),
            "duration": str(voucher.get("duration")), # TODO: Localized string
            "status": voucher.get("status").lower(),
            "create_time": voucher.get("create_time"),
        }
        if voucher.get("start_time") is not None:
            _x["start_time"] = voucher.get("start_time")

        if voucher.get("end_time") is not None:
            _x["end_time"] = voucher.get("end_time")

        if voucher.get("status_expires") is not None:
            _x["status_expires"] = str(voucher.get("status_expires")) # TODO: Localized string

        self._additional_extra_state_attributes = _x

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (self.coordinator.latest_voucher_id in self.coordinator.vouchers)

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        if (voucher := self._get_latest_voucher()) is None:
            return None

        return voucher.get("code")
