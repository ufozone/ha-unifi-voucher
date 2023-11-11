"""DataUpdateCoordinator for UniFi Hotspot Manager."""
from __future__ import annotations

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
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)
import homeassistant.util.dt as dt_util

from .const import (
    DOMAIN,
    LOGGER,
    UPDATE_INTERVAL,
    CONF_SITE_ID,
    ATTR_AVAILABLE,
    ATTR_LAST_PULL,
)
from .api import (
    UnifiVoucherApiClient,
    UnifiVouchers,
    UnifiVoucherCreateRequest,
    UnifiVoucherApiAuthenticationError,
    UnifiVoucherApiAccessError,
    UnifiVoucherApiConnectionError,
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
        self.last_voucher_id = None
        self._last_pull = None
        self._available = False
        self._scheduled_update_listeners: asyncio.TimerHandle | None = None

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

    async def initialize(self) -> None:
        """Set up a UniFi Network instance."""
        await self.client.controller.login()

    async def async_fetch_vouchers(
        self,
    ) -> None:
        _vouchers = {}
        _last_voucher_id = None

        vouchers = UnifiVouchers(self.client.controller)
        await vouchers.update()
        self._last_pull = dt_util.now()
        self._available = True
        for voucher in vouchers.values():
            # No HA generated voucher
            if not voucher.note.startswith("HA-generated"):
                continue
            # Voucher is full used
            if voucher.quota > 0 and voucher.quota <= voucher.used:
                continue

            _voucher = {
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
                _last_voucher_id is None or 
                _vouchers.get(_last_voucher_id, {}).get("create_time") < _v.get("create_time")
            ):
                _last_voucher_id = _i

        self.vouchers = _vouchers
        self.last_voucher_id = _last_voucher_id

    async def async_update_vouchers(
        self,
    ) -> None:
        """Create new voucher."""
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

    async def async_create_voucher(
        self,
        number: int = 1,
        quota: int = 1,
        expire: int = 480,
        up_bandwidth: int | None = None,
        down_bandwidth: int | None = None,
        byte_quota: int | None = None,
    ) -> None:
        """Create new voucher."""
        try:
            await self.client.controller.request(
                UnifiVoucherCreateRequest.create(
                    number=number,
                    quota=quota,
                    expire=expire,
                    up_bandwidth=up_bandwidth,
                    down_bandwidth=down_bandwidth,
                    byte_quota=byte_quota,
                    note="HA-generated",
                )
            )
            await self.async_update_vouchers()
        except Exception as exception:
            LOGGER.exception(exception)
