"""UniFi Hotspot Manager button platform."""
from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.helpers.entity import (
    Entity,
    EntityCategory,
)

from .coordinator import UnifiVoucherCoordinator
from .entity import UnifiVoucherEntity


@dataclass
class UnifiVoucherButtonDescriptionMixin:
    """Mixin to describe a UniFi Hotspot Manager button entity."""

    press_action: Callable[[UnifiVoucherCoordinator], Coroutine]


@dataclass
class UnifiVoucherButtonDescription(
    ButtonEntityDescription,
    UnifiVoucherButtonDescriptionMixin,
):
    """UniFi Hotspot Manager button description."""


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: Entity,
) -> None:
    """Do setup buttons from a config entry created in the integrations UI."""
    coordinator = config_entry.runtime_data
    entity_descriptions = [
        UnifiVoucherButtonDescription(
            key="create",
            icon="mdi:numeric-positive-1",
            translation_key="create",
            device_class=ButtonDeviceClass.RESTART,
            press_action=lambda coordinator: coordinator.async_create_voucher(),
        ),
        UnifiVoucherButtonDescription(
            key="delete",
            icon="mdi:numeric-negative-1",
            translation_key="delete",
            device_class=ButtonDeviceClass.RESTART,
            press_action=lambda coordinator: coordinator.async_delete_voucher(),
        ),
        UnifiVoucherButtonDescription(
            key="update",
            icon="mdi:update",
            translation_key="update",
            device_class=ButtonDeviceClass.UPDATE,
            entity_category=EntityCategory.DIAGNOSTIC,
            press_action=lambda coordinator: coordinator.async_update_vouchers(),
        ),
    ]

    async_add_entities(
        [
            UnifiVoucherButton(
                coordinator=coordinator,
                entity_description=entity_description,
            )
            for entity_description in entity_descriptions
        ],
        update_before_add=True,
    )


class UnifiVoucherButton(UnifiVoucherEntity, ButtonEntity):
    """Representation of a UniFi Hotspot Manager button."""

    def __init__(
        self,
        coordinator: UnifiVoucherCoordinator,
        entity_description: UnifiVoucherButtonDescription,
    ) -> None:
        """Initialize the button class."""
        super().__init__(
            coordinator=coordinator,
            entity_type="button",
            entity_key=entity_description.key,
        )
        self.entity_description = entity_description

    async def async_press(self) -> None:
        """Trigger the button action."""
        await self.entity_description.press_action(self.coordinator)
