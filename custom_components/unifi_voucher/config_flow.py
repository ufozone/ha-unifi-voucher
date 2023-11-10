"""Adds config flow for UniFi WiFi Voucher."""
from __future__ import annotations

from types import MappingProxyType

from homeassistant.config_entries import (
    ConfigFlow,
    CONN_CLASS_LOCAL_PUSH,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import (
    selector,
)
from homeassistant.helpers.aiohttp_client import (
    async_create_clientsession,
)
import voluptuous as vol
import socket

from .const import (
    LOGGER,
    DOMAIN,
    DEFAULT_SITE_ID,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_VERIFY_SSL,
    CONF_SITE_ID,
)
from .controller import get_unifi_controller
from .errors import AuthenticationRequired, CannotConnect


class UnifiVoucherConfigFlow(ConfigFlow, domain=DOMAIN):
    """UniFi WiFi Voucher config flow."""

    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_LOCAL_PUSH

    data: dict[str, any] | None
    options: dict[str, any] | None

    async def async_step_user(
        self,
        user_input: dict[str, any] | None = None,
    ) -> FlowResult:
        """Invoke when a user initiates a flow via the user interface."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._async_abort_entries_match(
                {
                    CONF_HOST: user_input[CONF_HOST],
                    CONF_PORT: user_input[CONF_PORT],
                }
            )
            _data = {
                CONF_HOST: user_input[CONF_HOST],
                CONF_USERNAME: user_input[CONF_USERNAME],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
                CONF_PORT: int(user_input[CONF_PORT]),
                CONF_VERIFY_SSL: user_input[CONF_VERIFY_SSL],
                CONF_SITE_ID: DEFAULT_SITE_ID,
            }
            try:
                session = async_create_clientsession(self.hass, user_input[CONF_VERIFY_SSL])
                controller = await get_unifi_controller(
                    self.hass, MappingProxyType(_data)
                )
                await controller.sites.update()
                self.sites = controller.sites
                LOGGER.debug(controller.sites)
            except AuthenticationRequired:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception as exception:
                LOGGER.exception(exception)
                errors["base"] = "unknown"

            if not errors:
                # Input is valid, set data
                self.data = _data
                self.data.update()
                return self.async_create_entry(
                    title=self.data[CONF_HOST],
                    data=self.data,
                )

        if await _async_discover_unifi(
            self.hass
        ):
            DEFAULT_HOST = "unifi"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=(user_input or {}).get(CONF_HOST, DEFAULT_HOST),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Required(
                        CONF_USERNAME,
                        default=(user_input or {}).get(CONF_USERNAME, ""),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Required(
                        CONF_PASSWORD,
                        default=(user_input or {}).get(CONF_PASSWORD, ""),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Required(
                        CONF_PORT,
                        default=(user_input or {}).get(CONF_PORT, DEFAULT_PORT),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=1,
                            max=65535,
                        )
                    ),
                    vol.Optional(
                        CONF_VERIFY_SSL,
                        default=(user_input or {}).get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
                    ): selector.BooleanSelector(),
                }
            ),
            errors=errors,
        )

async def _async_discover_unifi(hass: HomeAssistant) -> str | None:
    """Discover UniFi Network address."""
    try:
        return await hass.async_add_executor_job(socket.gethostbyname, "unifi")
    except socket.gaierror:
        return None
