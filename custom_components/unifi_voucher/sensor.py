"""UniFi Hotspot Manager sensor platform."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.const import (
    CONF_HOST,
    REVOLUTIONS_PER_MINUTE,
    UnitOfTemperature,
    ATTR_TEMPERATURE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.helpers.entity import Entity

from .const import (
    DOMAIN,
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
        # TODO
        #SensorEntityDescription(
        #    key=ATTR_FANSPEED,
        #    translation_key=ATTR_FANSPEED,
        #    icon="mdi:fan",
        #    native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        #    unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        #    state_class=SensorStateClass.MEASUREMENT,
        #),
        SensorEntityDescription(
            key="voucher",
            translation_key="voucher",
            icon="mdi:numeric",
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

    @property
    def native_value(self) -> str:
        """Return the native value of the sensor."""
        return self._get_state()
