"""Adds config flow for UniFi Hotspot Manager."""
from __future__ import annotations

import os

from homeassistant.core import (
    HomeAssistant,
    callback,
)
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlow,
    CONN_CLASS_LOCAL_PUSH,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    UnitOfDataRate,
    UnitOfInformation,
    UnitOfTime,
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
    DEFAULT_VOUCHER,
    CONF_SITE_ID,
    CONF_WLAN_NAME,
    CONF_VOUCHER_NUMBER,
    CONF_VOUCHER_QUOTA,
    CONF_VOUCHER_DURATION,
    CONF_VOUCHER_USAGE_QUOTA,
    CONF_VOUCHER_RATE_MAX_UP,
    CONF_VOUCHER_RATE_MAX_DOWN,
    CONF_CREATE_IF_NONE_EXISTS,
    CONF_QRCODE_LOGO_PATH,
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
        self.title: str | None = None
        self.data: dict[str, any] | None = None
        self.options: dict[str, any] | None = None
        self.sites: dict[str, str] | None = None
        self.reauth_config_entry: ConfigEntry | None = None
        self.reauth_schema: dict[vol.Marker, any] = {}

    async def async_step_user(
        self,
        user_input: dict[str, any] | None = None,
    ) -> FlowResult:
        """Invoke when a user initiates a flow via the user interface."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                client = UnifiVoucherApiClient(
                    self.hass,
                    host=user_input.get(CONF_HOST),
                    username=user_input.get(CONF_USERNAME),
                    password=user_input.get(CONF_PASSWORD),
                    port=int(user_input.get(CONF_PORT)),
                    site_id=DEFAULT_SITE_ID,
                    verify_ssl=user_input.get(CONF_VERIFY_SSL, False),
                )
                self.sites = await client.get_sites()
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
                # Input is valid, set data and options
                self.data = {
                    CONF_HOST: user_input.get(CONF_HOST),
                    CONF_USERNAME: user_input.get(CONF_USERNAME),
                    CONF_PASSWORD: user_input.get(CONF_PASSWORD),
                    CONF_PORT: int(user_input.get(CONF_PORT)),
                    CONF_SITE_ID: DEFAULT_SITE_ID,
                    CONF_VERIFY_SSL: user_input.get(CONF_VERIFY_SSL, False),
                }
                self.options = {
                    CONF_WLAN_NAME: "",
                }
                # Reauth
                if (
                    self.reauth_config_entry
                    and self.reauth_config_entry.unique_id is not None
                    and self.reauth_config_entry.unique_id in self.sites
                ):
                    return await self.async_step_site(
                        {
                            CONF_SITE_ID: self.reauth_config_entry.unique_id
                        }
                    )
                # Go to site selection, if user has access to more than one site
                return await self.async_step_site()

        _default_host = DEFAULT_HOST
        if await _async_discover_unifi(self.hass):
            _default_host = "unifi"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=(user_input or {}).get(CONF_HOST, _default_host),
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
                            type=selector.TextSelectorType.PASSWORD
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
            unique_id = user_input.get(CONF_SITE_ID, "")

            if not self.sites.get(unique_id):
                errors["base"] = "site_invalid"

            config_entry = await self.async_set_unique_id(unique_id)
            abort_reason = "configuration_updated"

            if self.reauth_config_entry:
                config_entry = self.reauth_config_entry
                abort_reason = "reauth_successful"
            else:
                # Abort if site is already configured
                self._async_abort_entries_match(
                    {
                        CONF_HOST: self.data[CONF_HOST],
                        CONF_SITE_ID: self.sites[unique_id].name,
                    }
                )

            if config_entry:
                self.hass.config_entries.async_update_entry(
                    config_entry, data=self.data
                )
                await self.hass.config_entries.async_reload(
                    config_entry.entry_id
                )
                return self.async_abort(
                    reason=abort_reason
                )

            if not errors:
                # Input is valid, set data.
                self.title = self.sites[unique_id].description
                self.data.update(
                    {
                        CONF_SITE_ID: self.sites[unique_id].name
                    }
                )
                return await self.async_step_options()

        # Only one site is available, skip selection
        if len(self.sites.values()) == 1:
            return await self.async_step_site(
                {
                    CONF_SITE_ID: next(iter(self.sites)),
                }
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
                                    value=_unique_id,
                                    label=_site.description,
                                )
                                for _unique_id, _site in self.sites.items()
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

    async def async_step_options(
        self,
        user_input: dict[str, any] | None = None,
    ) -> FlowResult:
        """Third step in config flow to save options."""
        errors: dict[str, str] = {}
        if user_input is not None:
            qrcode_logo_path = user_input.get(CONF_QRCODE_LOGO_PATH, "").strip()

            if qrcode_logo_path and not os.path.isfile(qrcode_logo_path):
                errors["base"] = "path_invalid"

            if not errors:
                # Input is valid, set data.
                self.options.update(
                    {
                        CONF_WLAN_NAME: user_input.get(CONF_WLAN_NAME, "").strip(),
                        CONF_VOUCHER_NUMBER: _set_option(user_input, CONF_VOUCHER_NUMBER),
                        CONF_VOUCHER_QUOTA: _set_option(user_input, CONF_VOUCHER_QUOTA),
                        CONF_VOUCHER_DURATION: _set_option(user_input, CONF_VOUCHER_DURATION),
                        CONF_VOUCHER_USAGE_QUOTA: _set_option(user_input, CONF_VOUCHER_USAGE_QUOTA),
                        CONF_VOUCHER_RATE_MAX_UP: _set_option(user_input, CONF_VOUCHER_RATE_MAX_UP),
                        CONF_VOUCHER_RATE_MAX_DOWN: _set_option(user_input, CONF_VOUCHER_RATE_MAX_DOWN),
                        CONF_CREATE_IF_NONE_EXISTS: user_input.get(CONF_CREATE_IF_NONE_EXISTS, False),
                        CONF_QRCODE_LOGO_PATH: qrcode_logo_path,
                    }
                )
                # User is done, create the config entry.
                return self.async_create_entry(
                    title=self.title,
                    data=self.data,
                    options=self.options,
                )

        _default_wlan_name = ""
        try:
            client = UnifiVoucherApiClient(
                self.hass,
                host=self.data.get(CONF_HOST),
                username=self.data.get(CONF_USERNAME),
                password=self.data.get(CONF_PASSWORD),
                port=self.data.get(CONF_PORT),
                site_id=self.data.get(CONF_SITE_ID),
                verify_ssl=self.data.get(CONF_VERIFY_SSL),
            )
            if (wlans := await client.get_guest_wlans()) is not None:
                _default_wlan_name = wlans[0]
        except Exception:
            LOGGER.info(
                "Could not access the UniFi Network guest WLANs. Perhaps the user does not have admin rights.",
            )

        return self.async_show_form(
            step_id="options",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_WLAN_NAME,
                        description={
                            "suggested_value": (user_input or {}).get(CONF_WLAN_NAME, _default_wlan_name),
                        },
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Optional(
                        CONF_VOUCHER_NUMBER,
                        default=DEFAULT_VOUCHER[CONF_VOUCHER_NUMBER].get("default", 0),
                        description={
                            "suggested_value": _get_option((user_input or {}), CONF_VOUCHER_NUMBER),
                        },
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=DEFAULT_VOUCHER[CONF_VOUCHER_NUMBER].get("min", 0),
                            max=DEFAULT_VOUCHER[CONF_VOUCHER_NUMBER].get("max", 10000),
                            step=DEFAULT_VOUCHER[CONF_VOUCHER_NUMBER].get("step", 1),
                        )
                    ),
                    vol.Optional(
                        CONF_VOUCHER_QUOTA,
                        default=DEFAULT_VOUCHER[CONF_VOUCHER_QUOTA].get("default", 0),
                        description={
                            "suggested_value": _get_option((user_input or {}), CONF_VOUCHER_QUOTA),
                        },
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=DEFAULT_VOUCHER[CONF_VOUCHER_QUOTA].get("min", 0),
                            max=DEFAULT_VOUCHER[CONF_VOUCHER_QUOTA].get("max", 10000),
                            step=DEFAULT_VOUCHER[CONF_VOUCHER_QUOTA].get("step", 1),
                        )
                    ),
                    vol.Optional(
                        CONF_VOUCHER_DURATION,
                        default=DEFAULT_VOUCHER[CONF_VOUCHER_DURATION].get("default", 24),
                        description={
                            "suggested_value": _get_option((user_input or {}), CONF_VOUCHER_DURATION),
                        },
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=DEFAULT_VOUCHER[CONF_VOUCHER_DURATION].get("min", 1),
                            max=DEFAULT_VOUCHER[CONF_VOUCHER_DURATION].get("max", 1000000),
                            step=DEFAULT_VOUCHER[CONF_VOUCHER_DURATION].get("step", 1),
                            unit_of_measurement=UnitOfTime.HOURS,
                        )
                    ),
                    vol.Optional(
                        CONF_VOUCHER_USAGE_QUOTA,
                        default=DEFAULT_VOUCHER[CONF_VOUCHER_USAGE_QUOTA].get("default", 0),
                        description={
                            "suggested_value": _get_option((user_input or {}), CONF_VOUCHER_USAGE_QUOTA),
                        },
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=DEFAULT_VOUCHER[CONF_VOUCHER_USAGE_QUOTA].get("min", 0),
                            max=DEFAULT_VOUCHER[CONF_VOUCHER_USAGE_QUOTA].get("max", 1048576),
                            step=DEFAULT_VOUCHER[CONF_VOUCHER_USAGE_QUOTA].get("step", 1),
                            unit_of_measurement=UnitOfInformation.MEGABYTES,
                        )
                    ),
                    vol.Optional(
                        CONF_VOUCHER_RATE_MAX_UP,
                        default=DEFAULT_VOUCHER[CONF_VOUCHER_RATE_MAX_UP].get("default", 0),
                        description={
                            "suggested_value": _get_option((user_input or {}), CONF_VOUCHER_RATE_MAX_UP),
                        },
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=DEFAULT_VOUCHER[CONF_VOUCHER_RATE_MAX_UP].get("min", 0),
                            max=DEFAULT_VOUCHER[CONF_VOUCHER_RATE_MAX_UP].get("max", 100000),
                            step=DEFAULT_VOUCHER[CONF_VOUCHER_RATE_MAX_UP].get("step", 1),
                            unit_of_measurement=UnitOfDataRate.KILOBITS_PER_SECOND,
                        )
                    ),
                    vol.Optional(
                        CONF_VOUCHER_RATE_MAX_DOWN,
                        default=DEFAULT_VOUCHER[CONF_VOUCHER_RATE_MAX_DOWN].get("default", 0),
                        description={
                            "suggested_value": _get_option((user_input or {}), CONF_VOUCHER_RATE_MAX_DOWN),
                        },
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=DEFAULT_VOUCHER[CONF_VOUCHER_RATE_MAX_DOWN].get("min", 0),
                            max=DEFAULT_VOUCHER[CONF_VOUCHER_RATE_MAX_DOWN].get("max", 100000),
                            step=DEFAULT_VOUCHER[CONF_VOUCHER_RATE_MAX_DOWN].get("step", 1),
                            unit_of_measurement=UnitOfDataRate.KILOBITS_PER_SECOND,
                        )
                    ),
                    vol.Optional(
                        CONF_CREATE_IF_NONE_EXISTS,
                        default=(user_input or {}).get(CONF_CREATE_IF_NONE_EXISTS, False),
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_QRCODE_LOGO_PATH,
                        description={
                            "suggested_value": (user_input or {}).get(CONF_QRCODE_LOGO_PATH, ""),
                        },
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                }
            ),
            errors=errors,
            last_step=True,
        )

    async def async_step_reauth(
        self,
        entry_data: dict[str, any],
    ) -> FlowResult:
        """Trigger a reauthentication flow."""
        config_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        assert config_entry
        self.reauth_config_entry = config_entry

        self.context["title_placeholders"] = {
            CONF_HOST: config_entry.data[CONF_HOST],
            CONF_SITE_ID: config_entry.title,
        }

        self.reauth_schema = {
            vol.Required(
                CONF_HOST,
                default=config_entry.data[CONF_HOST],
            ): selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.TEXT
                ),
            ),
            vol.Required(
                CONF_USERNAME,
                default=config_entry.data[CONF_USERNAME],
            ): selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.TEXT
                ),
            ),
            vol.Required(
                CONF_PASSWORD,
            ): selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.PASSWORD
                ),
            ),
            vol.Required(
                CONF_PORT,
                default=config_entry.data[CONF_PORT],
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    mode=selector.NumberSelectorMode.BOX,
                    min=1,
                    max=65535,
                )
            ),
            vol.Required(
                CONF_VERIFY_SSL,
                default=config_entry.data[CONF_VERIFY_SSL],
            ): selector.BooleanSelector(),
        }
        return await self.async_step_user()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> UnifiVoucherOptionsFlowHandler:
        """Get the options flow for this handler."""
        return UnifiVoucherOptionsFlowHandler(config_entry)

class UnifiVoucherOptionsFlowHandler(OptionsFlow):
    """Handle Unifi Network options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize UniFi Network options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(
        self, user_input: dict[str, any] | None = None
    ) -> FlowResult:
        """Options flow to save configurable options."""
        errors: dict[str, str] = {}
        if user_input is not None:
            qrcode_logo_path = user_input.get(CONF_QRCODE_LOGO_PATH, "").strip()

            if qrcode_logo_path and not os.path.isfile(qrcode_logo_path):
                errors["base"] = "path_invalid"

            if not errors:
                # Input is valid, set data.
                self.options.update(
                    {
                        CONF_WLAN_NAME: user_input.get(CONF_WLAN_NAME, "").strip(),
                        CONF_VOUCHER_NUMBER: _set_option(user_input, CONF_VOUCHER_NUMBER),
                        CONF_VOUCHER_QUOTA: _set_option(user_input, CONF_VOUCHER_QUOTA),
                        CONF_VOUCHER_DURATION: _set_option(user_input, CONF_VOUCHER_DURATION),
                        CONF_VOUCHER_USAGE_QUOTA: _set_option(user_input, CONF_VOUCHER_USAGE_QUOTA),
                        CONF_VOUCHER_RATE_MAX_UP: _set_option(user_input, CONF_VOUCHER_RATE_MAX_UP),
                        CONF_VOUCHER_RATE_MAX_DOWN: _set_option(user_input, CONF_VOUCHER_RATE_MAX_DOWN),
                        CONF_CREATE_IF_NONE_EXISTS: user_input.get(CONF_CREATE_IF_NONE_EXISTS, False),
                        CONF_QRCODE_LOGO_PATH: qrcode_logo_path,
                    }
                )
                # User is done, update the config entry.
                return self.async_create_entry(
                    title="",
                    data=self.options,
                )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_WLAN_NAME,
                        description={
                            "suggested_value": (user_input or self.options or {}).get(CONF_WLAN_NAME, ""),
                        },
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Optional(
                        CONF_VOUCHER_NUMBER,
                        default=DEFAULT_VOUCHER[CONF_VOUCHER_NUMBER].get("default", 0),
                        description={
                            "suggested_value": _get_option((user_input or self.options or {}), CONF_VOUCHER_NUMBER),
                        },
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=DEFAULT_VOUCHER[CONF_VOUCHER_NUMBER].get("min", 0),
                            max=DEFAULT_VOUCHER[CONF_VOUCHER_NUMBER].get("max", 10000),
                            step=DEFAULT_VOUCHER[CONF_VOUCHER_NUMBER].get("step", 1),
                        )
                    ),
                    vol.Optional(
                        CONF_VOUCHER_QUOTA,
                        default=DEFAULT_VOUCHER[CONF_VOUCHER_QUOTA].get("default", 0),
                        description={
                            "suggested_value": _get_option((user_input or self.options or {}), CONF_VOUCHER_QUOTA),
                        },
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=DEFAULT_VOUCHER[CONF_VOUCHER_QUOTA].get("min", 0),
                            max=DEFAULT_VOUCHER[CONF_VOUCHER_QUOTA].get("max", 10000),
                            step=DEFAULT_VOUCHER[CONF_VOUCHER_QUOTA].get("step", 1),
                        )
                    ),
                    vol.Optional(
                        CONF_VOUCHER_DURATION,
                        default=DEFAULT_VOUCHER[CONF_VOUCHER_DURATION].get("default", 24),
                        description={
                            "suggested_value": _get_option((user_input or self.options or {}), CONF_VOUCHER_DURATION),
                        },
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=DEFAULT_VOUCHER[CONF_VOUCHER_DURATION].get("min", 1),
                            max=DEFAULT_VOUCHER[CONF_VOUCHER_DURATION].get("max", 1000000),
                            step=DEFAULT_VOUCHER[CONF_VOUCHER_DURATION].get("step", 1),
                            unit_of_measurement=UnitOfTime.HOURS,
                        )
                    ),
                    vol.Optional(
                        CONF_VOUCHER_USAGE_QUOTA,
                        default=DEFAULT_VOUCHER[CONF_VOUCHER_USAGE_QUOTA].get("default", 0),
                        description={
                            "suggested_value": _get_option((user_input or self.options or {}), CONF_VOUCHER_USAGE_QUOTA),
                        },
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=DEFAULT_VOUCHER[CONF_VOUCHER_USAGE_QUOTA].get("min", 0),
                            max=DEFAULT_VOUCHER[CONF_VOUCHER_USAGE_QUOTA].get("max", 1000000),
                            step=DEFAULT_VOUCHER[CONF_VOUCHER_USAGE_QUOTA].get("step", 1),
                            unit_of_measurement=UnitOfInformation.MEGABYTES,
                        )
                    ),
                    vol.Optional(
                        CONF_VOUCHER_RATE_MAX_UP,
                        default=DEFAULT_VOUCHER[CONF_VOUCHER_RATE_MAX_UP].get("default", 0),
                        description={
                            "suggested_value": _get_option((user_input or self.options or {}), CONF_VOUCHER_RATE_MAX_UP),
                        },
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=DEFAULT_VOUCHER[CONF_VOUCHER_RATE_MAX_UP].get("min", 0),
                            max=DEFAULT_VOUCHER[CONF_VOUCHER_RATE_MAX_UP].get("max", 100000),
                            step=DEFAULT_VOUCHER[CONF_VOUCHER_RATE_MAX_UP].get("step", 1),
                            unit_of_measurement=UnitOfDataRate.KILOBITS_PER_SECOND,
                        )
                    ),
                    vol.Optional(
                        CONF_VOUCHER_RATE_MAX_DOWN,
                        default=DEFAULT_VOUCHER[CONF_VOUCHER_RATE_MAX_DOWN].get("default", 0),
                        description={
                            "suggested_value": _get_option((user_input or self.options or {}), CONF_VOUCHER_RATE_MAX_DOWN),
                        },
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=DEFAULT_VOUCHER[CONF_VOUCHER_RATE_MAX_DOWN].get("min", 0),
                            max=DEFAULT_VOUCHER[CONF_VOUCHER_RATE_MAX_DOWN].get("max", 100000),
                            step=DEFAULT_VOUCHER[CONF_VOUCHER_RATE_MAX_DOWN].get("step", 1),
                            unit_of_measurement=UnitOfDataRate.KILOBITS_PER_SECOND,
                        )
                    ),
                    vol.Optional(
                        CONF_CREATE_IF_NONE_EXISTS,
                        default=(user_input or self.options or {}).get(CONF_CREATE_IF_NONE_EXISTS, False),
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_QRCODE_LOGO_PATH,
                        description={
                            "suggested_value": (user_input or self.options or {}).get(CONF_QRCODE_LOGO_PATH, ""),
                        },
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                }
            ),
            errors=errors,
            last_step=True,
        )

async def _async_discover_unifi(hass: HomeAssistant) -> str | None:
    """Discover UniFi Network address."""
    try:
        return await hass.async_add_executor_job(socket.gethostbyname, "unifi")
    except socket.gaierror:
        return None

def _get_option(
    input: dict[str, any],
    option: str,
    fallback_default: int = 0
) -> int:
    _default = DEFAULT_VOUCHER[option].get("default", fallback_default)
    _value = input.get(option, _default)
    return int(_value)

def _set_option(
    input: dict[str, any],
    option: str,
    fallback_default: int = 0
) -> int:
    _default = DEFAULT_VOUCHER[option].get("default", fallback_default)
    _value = input.get(option, _default)
    return int(_value)
