"""UniFi Hotspot Manager integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.helpers.service import (
    verify_domain_control,
)

from .const import (
    LOGGER,
    DOMAIN,
    CONF_VOUCHER_NUMBER,
    CONF_VOUCHER_QUOTA,
    CONF_VOUCHER_DURATION,
    CONF_VOUCHER_USAGE_QUOTA,
    CONF_VOUCHER_RATE_MAX_UP,
    CONF_VOUCHER_RATE_MAX_DOWN,
    DEFAULT_VOUCHER,
)
from .coordinator import UnifiVoucherCoordinator

SERVICE_LIST = "list"
SERVICE_CREATE = "create"
SERVICE_DELETE = "delete"
SERVICE_UPDATE = "update"

@callback
def async_setup_services(
    hass: HomeAssistant,
    coordinator: UnifiVoucherCoordinator,
) -> None:
    """Set up services for UniFi Hotspot Manager integration."""

    @verify_domain_control(hass, DOMAIN)
    async def async_list(service_call: ServiceCall) -> ServiceResponse:
        LOGGER.debug(service_call)
        _vouchers = []
        vouchers = coordinator.vouchers.values()
        for voucher in vouchers:
            _x = {
                "id": voucher.get("id"),
                "code": voucher.get("code"),
                "quota": voucher.get("quota"),
                "used": voucher.get("used"),
                "duration": int(voucher.get("duration").total_seconds() / 3600),
                "status": voucher.get("status"),
                "create_time": voucher.get("create_time"),
            }
            if voucher.get("start_time") is not None:
                _x["start_time"] = voucher.get("start_time")

            if voucher.get("end_time") is not None:
                _x["end_time"] = voucher.get("end_time")

            if voucher.get("status_expires") is not None:
                _x["status_expires"] = int(voucher["status_expires"].total_seconds() / 3600)

            if voucher.get("qos_usage_quota") > 0:
                _x["usage_quota"] = voucher.get("qos_usage_quota")

            if voucher.get("qos_rate_max_up") > 0:
                _x["rate_max_up"] = voucher.get("qos_rate_max_up")

            if voucher.get("qos_rate_max_down") > 0:
                _x["rate_max_down"] = voucher.get("qos_rate_max_down")

            _vouchers.append(_x)

        return {
            "count": len(_vouchers),
            "vouchers": list(_vouchers),
        }

    @verify_domain_control(hass, DOMAIN)
    async def async_create(service_call: ServiceCall) -> None:
        LOGGER.debug(service_call)
        await coordinator.async_create_voucher(
            number=service_call.data.get("number"),
            quota=service_call.data.get("quota"),
            duration=service_call.data.get("duration"),
            usage_quota=service_call.data.get("usage_quota"),
            rate_max_up=service_call.data.get("rate_max_up"),
            rate_max_down=service_call.data.get("rate_max_down"),
        )

    @verify_domain_control(hass, DOMAIN)
    async def async_delete(service_call: ServiceCall) -> None:
        LOGGER.debug(service_call)
        await coordinator.async_delete_voucher(
            obj_id=service_call.data.get("id"),
        )

    @verify_domain_control(hass, DOMAIN)
    async def async_update(service_call: ServiceCall) -> None:
        LOGGER.debug(service_call)
        await coordinator.async_update_vouchers()

    hass.services.async_register(
        domain=DOMAIN,
        service=SERVICE_LIST,
        service_func=async_list,
        schema=vol.Schema({}),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        domain=DOMAIN,
        service=SERVICE_CREATE,
        service_func=async_create,
        schema=vol.Schema(
            {
                vol.Optional(
                    "number",
                    default=coordinator.get_entry_option(CONF_VOUCHER_NUMBER)
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(
                        min=DEFAULT_VOUCHER[CONF_VOUCHER_NUMBER].get("min", 1),
                        max=DEFAULT_VOUCHER[CONF_VOUCHER_NUMBER].get("max", 10000),
                    )
                ),
                vol.Optional(
                    "quota",
                    default=coordinator.get_entry_option(CONF_VOUCHER_QUOTA)
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(
                        min=DEFAULT_VOUCHER[CONF_VOUCHER_QUOTA].get("min", 0),
                        max=DEFAULT_VOUCHER[CONF_VOUCHER_QUOTA].get("max", 10000),
                    )
                ),
                vol.Optional(
                    "duration",
                    default=coordinator.get_entry_option(CONF_VOUCHER_DURATION)
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(
                        min=DEFAULT_VOUCHER[CONF_VOUCHER_DURATION].get("min", 1),
                        max=DEFAULT_VOUCHER[CONF_VOUCHER_DURATION].get("max", 1000000),
                    )
                ),
                vol.Optional(
                    "usage_quota",
                    default=coordinator.get_entry_option(CONF_VOUCHER_USAGE_QUOTA)
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(
                        min=DEFAULT_VOUCHER[CONF_VOUCHER_USAGE_QUOTA].get("min", 0),
                        max=DEFAULT_VOUCHER[CONF_VOUCHER_USAGE_QUOTA].get("max", 1048576),
                    )
                ),
                vol.Optional(
                    "rate_max_up",
                    default=coordinator.get_entry_option(CONF_VOUCHER_RATE_MAX_UP)
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(
                        min=DEFAULT_VOUCHER[CONF_VOUCHER_RATE_MAX_UP].get("min", 0),
                        max=DEFAULT_VOUCHER[CONF_VOUCHER_RATE_MAX_UP].get("max", 100000),
                    )
                ),
                vol.Optional(
                    "rate_max_down",
                    default=coordinator.get_entry_option(CONF_VOUCHER_RATE_MAX_DOWN)
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(
                        min=DEFAULT_VOUCHER[CONF_VOUCHER_RATE_MAX_DOWN].get("min", 0),
                        max=DEFAULT_VOUCHER[CONF_VOUCHER_RATE_MAX_DOWN].get("max", 100000),
                    )
                ),
            }
        ),
    )
    hass.services.async_register(
        domain=DOMAIN,
        service=SERVICE_DELETE,
        service_func=async_delete,
        schema=vol.Schema(
            {
                vol.Optional("id"): vol.Coerce(str),
            }
        ),
    )
    hass.services.async_register(
        domain=DOMAIN,
        service=SERVICE_UPDATE,
        service_func=async_update,
        schema=vol.Schema({}),
    )

@callback
def async_unload_services(hass: HomeAssistant) -> None:
    """Unload UniFi Network services."""
    hass.services.async_remove(DOMAIN, SERVICE_LIST)
    hass.services.async_remove(DOMAIN, SERVICE_CREATE)
    hass.services.async_remove(DOMAIN, SERVICE_DELETE)
    hass.services.async_remove(DOMAIN, SERVICE_UPDATE)
