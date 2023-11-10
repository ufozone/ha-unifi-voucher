"""DataUpdateCoordinator for UniFi WiFi Voucher."""
from __future__ import annotations

from datetime import timedelta
from pyunifi.controller import Controller

from homeassistant.core import HomeAssistant
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    ATTR_STATE,
    ATTR_TEMPERATURE,
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
    DEFAULT_SITE_ID,
    DEFAULT_VERSION,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_VERIFY_SSL,
    CONF_SITE_ID,
    CONF_VERSION,
    ATTR_AVAILABLE,
    ATTR_LAST_PULL,
)


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class UnifiVoucherCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the UniFi WiFi Voucher."""

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
        self.controller = Controller(
            config_entry.options.get(CONF_HOST, DEFAULT_HOST),
            config_entry.options.get(CONF_USERNAME, ""),
            config_entry.options.get(CONF_PASSWORD, ""),
            config_entry.options.get(CONF_PORT, DEFAULT_PORT),
            config_entry.options.get(CONF_VERSION, DEFAULT_VERSION),
            config_entry.options.get(CONF_SITE_ID, DEFAULT_SITE_ID),
            config_entry.options.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
        )
        vouchers = self.controller.list_vouchers()
        LOGGER.debug(vouchers)
        self.controller = None # TODO
        self._last_pull = None

    async def __aenter__(self):
        """Return Self."""
        return self

    async def __aexit__(self, *excinfo):
        """Close Session before class is destroyed."""
        await self.client._session.close()

    async def _async_update_data(self):
        """Update data via library."""
        _available = False
        _data = {}
        try:
            self._last_pull = dt_util.now()
            _available = True
        # TODO
        #except (UnifiVoucherClientTimeoutError, UnifiVoucherClientCommunicationError, UnifiVoucherClientAuthenticationError) as exception:
        #    LOGGER.error(str(exception))
        except Exception as exception:
            LOGGER.exception(exception)

        _data.update(
            {
                ATTR_LAST_PULL: self._last_pull,
                ATTR_AVAILABLE: _available,
            }
        )
        return _data
