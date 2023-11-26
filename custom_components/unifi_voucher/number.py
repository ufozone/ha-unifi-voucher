"""UniFi Hotspot Manager number platform."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.const import (
    UnitOfTime,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.helpers.entity import Entity

from .const import (
    DOMAIN,
    CONF_VOUCHER_QUOTA,
    CONF_VOUCHER_EXPIRE,
    DEFAULT_VOUCHER,
)
from .coordinator import UnifiVoucherCoordinator
from .entity import UnifiVoucherEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: Entity,
) -> None:
    """Do setup numbers from a config entry created in the integrations UI."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    entity_descriptions = [
        NumberEntityDescription(
            key=CONF_VOUCHER_QUOTA,
            icon="mdi:numeric-9-plus",
            translation_key=CONF_VOUCHER_QUOTA,
        ),
        NumberEntityDescription(
            key=CONF_VOUCHER_EXPIRE,
            icon="mdi:clock-outline",
            native_unit_of_measurement=UnitOfTime.HOURS,
            translation_key=CONF_VOUCHER_EXPIRE,
        ),
    ]

    async_add_entities(
        [
            UnifiVoucherNumber(
                coordinator=coordinator,
                entity_description=entity_description,
            )
            for entity_description in entity_descriptions
        ],
        update_before_add=True,
    )


class UnifiVoucherNumber(UnifiVoucherEntity, NumberEntity):
    """Representation of a UniFi Hotspot Manager number."""

    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: UnifiVoucherCoordinator,
        entity_description: NumberEntityDescription,
    ) -> None:
        """Initialize the number class."""
        super().__init__(
            coordinator=coordinator,
            entity_type="number",
            entity_key=entity_description.key,
        )
        self.entity_description = entity_description
        self._attr_native_min_value = DEFAULT_VOUCHER.get(entity_description.key).get("min", 0)
        self._attr_native_max_value = DEFAULT_VOUCHER.get(entity_description.key).get("max", 10000)
        self._attr_native_step = DEFAULT_VOUCHER.get(entity_description.key).get("step", 1)

    def _get_scale(self) -> float:
        """Scale factor."""
        return float(DEFAULT_VOUCHER.get(self.entity_description.key).get("scale", 1))

    @property
    def native_value(self) -> int:
        """Return the entity value to represent the entity state."""
        return int(self.coordinator.get_entry_option(self.entity_description.key) / self._get_scale())

    async def async_set_native_value(self, value: float) -> None:
        """Change the value."""
        value = int(value)
        await self.coordinator.async_set_entry_option(
            self.entity_description.key,
            int(value) * self._get_scale(),
        )