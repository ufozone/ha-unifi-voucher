"""UniFi Hotspot Manager sensor platform."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.const import (
    UnitOfInformation,
    UnitOfDataRate,
    UnitOfTime,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.helpers.entity import Entity

from .const import (
    CONF_WLAN_NAME,
    ATTR_VOUCHER,
    DEFAULT_IDENTIFIER_STRING,
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

    def _format_duration(self, duration: timedelta) -> str:
        seconds = int(duration.total_seconds())
        periods = [
            (UnitOfTime.DAYS,    60*60*24),
            (UnitOfTime.HOURS,   60*60),
            (UnitOfTime.MINUTES, 60),
            (UnitOfTime.SECONDS, 1),
        ]
        strings = []
        for period_key, period_seconds in periods:
            if seconds >= period_seconds:
                period_value, seconds = divmod(seconds, period_seconds)
                strings.append(f"{period_value} {period_key}")

        return ", ".join(strings)

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
            CONF_WLAN_NAME: self.coordinator.get_wlan_name(),
            "id": voucher.get("id"),
            "quota": voucher.get("quota"),
            "used": voucher.get("used"),
            "duration": self._format_duration(voucher.get("duration")),
            "status": voucher.get("status").lower(),
            "create_time": voucher.get("create_time"),
        }
        # If note longer than default identifier plus two characters ": "
        if len(voucher.get("note")) > (_index := (len(DEFAULT_IDENTIFIER_STRING) + 2)):
            _x["note"] = voucher.get("note")[_index:]

        if voucher.get("start_time") is not None:
            _x["start_time"] = voucher.get("start_time")

        if voucher.get("end_time") is not None:
            _x["end_time"] = voucher.get("end_time")

        if voucher.get("status_expires") is not None:
            _x["status_expires"] = self._format_duration(voucher.get("status_expires"))

        if voucher.get("qos_usage_quota") > 0:
            _x["usage_quota"] = str(voucher.get("qos_usage_quota")) + " " + UnitOfInformation.MEGABYTES

        if voucher.get("qos_rate_max_up") > 0:
            _x["rate_max_up"] = str(voucher.get("qos_rate_max_up")) + " " + UnitOfDataRate.KILOBITS_PER_SECOND

        if voucher.get("qos_rate_max_down") > 0:
            _x["rate_max_down"] = str(voucher.get("qos_rate_max_down")) + " " + UnitOfDataRate.KILOBITS_PER_SECOND

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
