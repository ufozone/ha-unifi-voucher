"""DataUpdateCoordinator for UniFi Hotspot Manager."""
from __future__ import annotations

import asyncio

from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
)
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
import homeassistant.util.dt as dt_util

from aiounifi.interfaces.vouchers import Vouchers
from aiounifi.models.voucher import (
    VoucherCreateRequest,
    VoucherDeleteRequest,
)

from .const import (
    DOMAIN,
    LOGGER,
    UPDATE_INTERVAL,
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
    DEFAULT_IDENTIFIER_STRING,
    DEFAULT_VOUCHER,
)
from .api import (
    UnifiVoucherApiClient,
    UnifiVoucherApiAuthenticationError,
    UnifiVoucherApiAccessError,
    UnifiVoucherApiError,
)


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class UnifiVoucherCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the UniFi Hotspot Manager."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        update_interval: timedelta = timedelta(seconds=UPDATE_INTERVAL),
    ) -> None:
        """Initialize."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.hass = hass
        self.config_entry = config_entry
        self.client = UnifiVoucherApiClient(
            hass,
            host=config_entry.data.get(CONF_HOST),
            username=config_entry.data.get(CONF_USERNAME),
            password=config_entry.data.get(CONF_PASSWORD),
            port=int(config_entry.data.get(CONF_PORT)),
            site_id=config_entry.data.get(CONF_SITE_ID),
            verify_ssl=config_entry.data.get(CONF_VERIFY_SSL),
        )
        self.vouchers = {}
        self.latest_voucher_id = None
        self._last_pull = None
        self._available = False

        self._loop = asyncio.get_event_loop()
        self._scheduled_update_listeners: asyncio.TimerHandle | None = None
        self._scheduled_update_entry: asyncio.TimerHandle | None = None

    async def __aenter__(self):
        """Return Self."""
        return self

    async def _async_update_data(self):
        """Update data via library."""
        self._available = False
        try:
            # Update vouchers.
            await self.async_fetch_vouchers()

            LOGGER.debug("_async_update_data")
            LOGGER.debug(self.vouchers)

            return self.vouchers
        except (
            UnifiVoucherApiAuthenticationError,
            UnifiVoucherApiAccessError,
        ) as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except UnifiVoucherApiError as exception:
            raise UpdateFailed(exception) from exception

    async def _async_update_listeners(self) -> None:
        """Schedule update all registered listeners after 1 second."""
        if self._scheduled_update_listeners:
            self._scheduled_update_listeners.cancel()

        self._scheduled_update_listeners = self.hass.loop.call_later(
            1,
            lambda: self.async_update_listeners(),
        )

    def get_entry_id(
        self,
    ) -> str:
        """Get unique id for config entry."""
        if self.config_entry.unique_id is not None:
            return self.config_entry.unique_id

        _host = self.config_entry.data.get(CONF_HOST)
        _site_id = self.config_entry.data.get(CONF_SITE_ID)
        return f"{_host}_{_site_id}"

    def get_entry_title(
        self,
    ) -> str:
        """Get title for config entry."""
        return self.config_entry.title

    def get_configuration_url(
        self,
    ) -> str:
        """Get configuration url for config entry."""
        _host = self.config_entry.data.get(CONF_HOST)
        _port = self.config_entry.data.get(CONF_PORT)
        _site_id = self.config_entry.data.get(CONF_SITE_ID)
        return f"https://{_host}:{_port}/network/{_site_id}/hotspot"

    def get_wlan_name(
        self,
    ) -> str:
        """Get guest WLAN name."""
        return self.config_entry.options.get(CONF_WLAN_NAME, "")

    def get_qrcode_logo_path(
        self,
    ) -> str:
        """Get QR code logo path."""
        return self.config_entry.options.get(CONF_QRCODE_LOGO_PATH, "")

    def get_entry_option(
        self,
        conf_key: str,
    ) -> any:
        """Get config entry option with default value as fallback."""
        _default_value = DEFAULT_VOUCHER.get(conf_key, {}).get("default")
        return self.config_entry.options.get(conf_key, _default_value)

    async def async_set_entry_option(
        self,
        key: str,
        value: any,
    ) -> None:
        """Set config entry option and update config entry after 3 second."""
        _options = dict(self.config_entry.options)
        _options.update(
            {
                key: value
            }
        )
        if self._scheduled_update_entry:
            self._scheduled_update_entry.cancel()
        self._scheduled_update_entry = self.hass.loop.call_later(
            3,
            lambda: self.hass.config_entries.async_update_entry(
                self.config_entry, options=_options
            ),
        )

    async def initialize(self) -> None:
        """Set up a UniFi Network instance."""
        await self.client.controller.login()

    async def async_fetch_vouchers(
        self,
    ) -> None:
        """Fetch data for all vouchers."""
        _vouchers = {}
        _latest_voucher_id = None

        vouchers = Vouchers(self.client.controller)
        await vouchers.update()

        self._last_pull = dt_util.now()
        self._available = True
        for voucher in vouchers.values():
            # No HA generated voucher
            if not voucher.note.startswith(DEFAULT_IDENTIFIER_STRING):
                continue
            # Voucher is full used
            if voucher.quota > 0 and voucher.quota <= voucher.used:
                continue

            _voucher = {
                "id": voucher.id,
                "note": voucher.note,
                "code": voucher.code,
                "quota": voucher.quota,
                "duration": voucher.duration,
                "qos_overwrite": voucher.qos_overwrite,
                "qos_usage_quota": voucher.qos_usage_quota,
                "qos_rate_max_up": voucher.qos_rate_max_up,
                "qos_rate_max_down": voucher.qos_rate_max_down,
                "used": voucher.used,
                "create_time": voucher.create_time,
                "start_time": voucher.start_time,
                "end_time": voucher.end_time,
                "status": voucher.status,
                "status_expires": voucher.status_expires,
            }
            _vouchers[voucher.id] = _voucher

        for _i, _v in _vouchers.items():
            if (
                _latest_voucher_id is None or
                _vouchers.get(_latest_voucher_id, {}).get("create_time") < _v.get("create_time")
            ):
                _latest_voucher_id = _i

        self.vouchers = _vouchers
        self.latest_voucher_id = _latest_voucher_id

        # If no voucher found, create a new one
        if _latest_voucher_id is None and self.config_entry.options.get(CONF_CREATE_IF_NONE_EXISTS, False):
            LOGGER.info("No voucher found, create a new one")
            await self.async_create_voucher()

    async def async_create_voucher(
        self,
        number: int | None = None,
        quota: int | None = None,
        duration: int | None = None,
        usage_quota: int | None = None,
        rate_max_up: int | None = None,
        rate_max_down: int | None = None,
        note: str | None = None,
    ) -> None:
        """Create new voucher."""
        try:
            if number is None:
                number = int(self.get_entry_option(CONF_VOUCHER_NUMBER))

            if quota is None:
                quota = int(self.get_entry_option(CONF_VOUCHER_QUOTA))

            if duration is None:
                duration = int(self.get_entry_option(CONF_VOUCHER_DURATION))

            if usage_quota is None:
                usage_quota = int(self.get_entry_option(CONF_VOUCHER_USAGE_QUOTA))

            if rate_max_up is None:
                rate_max_up = int(self.get_entry_option(CONF_VOUCHER_RATE_MAX_UP))

            if rate_max_down is None:
                rate_max_down = int(self.get_entry_option(CONF_VOUCHER_RATE_MAX_DOWN))

            if note:
                note = DEFAULT_IDENTIFIER_STRING + ': ' + note
            else:
                note = DEFAULT_IDENTIFIER_STRING

            await self.client.controller.request(
                VoucherCreateRequest.create(
                    number=number,
                    quota=quota,
                    expire_number=duration,
                    expire_unit=60,
                    usage_quota=usage_quota,
                    rate_max_up=rate_max_up,
                    rate_max_down=rate_max_down,
                    note=note,
                )
            )
            await self.async_update_vouchers()
        except Exception as exception:
            LOGGER.exception(exception)

    async def async_delete_voucher(
        self,
        obj_id: str | None = None,
    ) -> None:
        """Remove voucher."""
        try:
            # No voucher ID given
            if obj_id is None:
                if (obj_id := self.latest_voucher_id) is None:
                    raise ValueError

            await self.client.controller.request(
                VoucherDeleteRequest.create(
                    obj_id=obj_id,
                )
            )
            await self.async_update_vouchers()
        except Exception as exception:
            LOGGER.exception(exception)

    async def async_update_vouchers(
        self,
    ) -> None:
        """Update vouchers."""
        try:
            await self.async_fetch_vouchers()

            # Always update HA states after a command was executed.
            # API calls that change the lawn mower's state update the local object when
            # executing the command, so only the HA state needs further updates.
            self.hass.async_create_task(
                self._async_update_listeners()
            )
        except Exception as exception:
            LOGGER.exception(exception)
