"""Adds config flow for UniFi Hotspot Manager."""
from __future__ import annotations

from aiounifi.interfaces.sites import Sites
from aiounifi.models.site import Site

from homeassistant.core import (
    callback,
    HomeAssistant,
)
from homeassistant.config_entries import (
    ConfigEntry,
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
import voluptuous as vol
import socket

from .const import (
    LOGGER,
    DOMAIN,
    DEFAULT_SITE_ID,
    DEFAULT_HOST,
    DEFAULT_USERNAME,
    DEFAULT_PASSWORD,
    DEFAULT_PORT,
    DEFAULT_VERIFY_SSL,
    CONF_SITE_ID,
)
from .api import (
    UnifiVoucherApiClient,
    UnifiVoucherApiAuthenticationError,
    UnifiVoucherApiAccessError,
    UnifiVoucherApiConnectionError,
    UnifiVoucherApiError,
)


class UnifiVoucherConfigFlow(ConfigFlow, domain=DOMAIN):
    """UniFi Hotspot Manager config flow."""

    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_LOCAL_PUSH

    def __init__(self) -> None:
        """Initialize the UniFi Network flow."""
        self._title: str | None = None
        self._options: dict[str, any] | None = None
        self._sites: dict[str, str] | None = None

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
                    CONF_USERNAME: user_input[CONF_USERNAME],
                }
            )
            try:
                client = UnifiVoucherApiClient(
                    self.hass,
                    host=user_input[CONF_HOST],
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                    port=int(user_input[CONF_PORT]),
                    site_id=DEFAULT_SITE_ID,
                    verify_ssl=user_input[CONF_VERIFY_SSL],
                )
                self._sites = await client.check_api_user()
            except UnifiVoucherApiConnectionError:
                errors["base"] = "cannot_connect"
            except UnifiVoucherApiAuthenticationError:
                errors["base"] = "invalid_auth"
            except UnifiVoucherApiAccessError:
                errors["base"] = "no_access"
            except (UnifiVoucherApiError, Exception) as exception:
                LOGGER.exception(exception)
                errors["base"] = "unknown"

            if not errors:
                # Input is valid, set data
                self._options = {
                    CONF_HOST: user_input.get(CONF_HOST, "").strip(),
                    CONF_USERNAME: user_input.get(CONF_USERNAME, "").strip(),
                    CONF_PASSWORD: user_input.get(CONF_PASSWORD, "").strip(),
                    CONF_PORT: int(user_input[CONF_PORT]),
                    CONF_SITE_ID: DEFAULT_SITE_ID,
                    CONF_VERIFY_SSL: user_input.get(CONF_VERIFY_SSL, False),
                }
                # Go to site selection, if user has access to more than one site
                if len(self._sites) > 1:
                    return await self.async_step_site()

                site_id = list(self._sites.keys())[0]

                self._title = self._sites.get(site_id)
                self._options.update({
                    CONF_SITE_ID: site_id
                })
                # User is done, create the config entry.
                return self.async_create_entry(
                    title=self._title,
                    data={},
                    options=self._options,
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
                        default=(user_input or {}).get(CONF_USERNAME, DEFAULT_USERNAME),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Required(
                        CONF_PASSWORD,
                        default=(user_input or {}).get(CONF_PASSWORD, DEFAULT_PASSWORD),
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

    async def async_step_site(
        self,
        user_input: dict[str, any] | None = None,
    ) -> FlowResult:
        """Second step in config flow to save site."""
        errors: dict[str, str] = {}
        if user_input is not None:
            site_id = user_input.get(CONF_SITE_ID, "")

            if not self._sites.get(site_id):
                errors["base"] = "site_invalid"

            if not errors:
                # Input is valid, set data.
                self._title = self._sites.get(site_id)
                self._options.update({
                    CONF_SITE_ID: site_id
                })
                # User is done, create the config entry.
                return self.async_create_entry(
                    title=self._title,
                    data={},
                    options=self._options,
                )
        return self.async_show_form(
            step_id="site",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SITE_ID,
                        default=(user_input or {}).get(CONF_SITE_ID, ""),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(
                                    value=site_id,
                                    label=site_description,
                                )
                                for site_id, site_description in self._sites.items()
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                            translation_key=CONF_SITE_ID,
                            multiple=False,
                        )
                    ),
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
