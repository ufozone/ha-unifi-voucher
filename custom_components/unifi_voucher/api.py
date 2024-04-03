"""UniFi Hotspot Manager API Client."""
from __future__ import annotations

import asyncio

from aiohttp import CookieJar

import aiounifi
from aiounifi.models.configuration import Configuration
from aiounifi.models.api import (
    ApiRequest,
    TypedApiResponse,
)

from homeassistant.core import (
    callback,
    HomeAssistant,
)
from homeassistant.helpers import aiohttp_client

from .const import (
    LOGGER,
)

RETRY_TIMER = 15

class UnifiVoucherApiError(Exception):
    """Exception to indicate a general API error."""


class UnifiVoucherApiConnectionError(UnifiVoucherApiError):
    """Exception to indicate a connection error."""


class UnifiVoucherApiAccessError(UnifiVoucherApiError):
    """Exception to indicate an access error."""


class UnifiVoucherApiAuthenticationError(UnifiVoucherApiError):
    """Exception to indicate an authentication error."""


class UnifiVoucherApiClient:
    """API Client."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        username: str,
        password: str,
        port: int,
        site_id: str,
        verify_ssl: bool,
    ) -> None:
        """Initialize the system."""
        self.hass = hass
        self.host = host

        if verify_ssl:
            session = aiohttp_client.async_get_clientsession(
                hass,
            )
        else:
            session = aiohttp_client.async_create_clientsession(
                hass,
                verify_ssl=False,
                cookie_jar=CookieJar(unsafe=True),
            )
        self.controller = aiounifi.Controller(
            Configuration(
                session,
                host=host,
                username=username,
                password=password,
                port=port,
                site=site_id,
                ssl_context=verify_ssl,
            )
        )
        self.available = True

    @callback
    def reconnect(self) -> None:
        """Prepare to reconnect UniFi session."""
        LOGGER.info("Will try to reconnect to UniFi Network")
        self.hass.loop.create_task(self.async_reconnect())

    async def async_reconnect(self) -> None:
        """Try to reconnect UniFi Network session."""
        try:
            async with asyncio.timeout(5):
                await self.controller.login()
        except (
            TimeoutError,
            aiounifi.BadGateway,
            aiounifi.ServiceUnavailable,
            aiounifi.AiounifiException,
        ):
            self.hass.loop.call_later(RETRY_TIMER, self.reconnect)

    async def get_sites(
        self,
    ) -> dict[str, any]:
        """Check the given API user."""
        _sites = {}
        try:
            async with asyncio.timeout(10):
                await self.controller.login()
                await self.controller.sites.update()
                for _unique_id, _site in self.controller.sites.items():
                    # User must have admin or hotspot permissions
                    if _site.role in ("admin", "hotspot"):
                        _sites[_unique_id] = _site

                # No site with the required permissions found
                if len(_sites) == 0:
                    LOGGER.warning(
                        "Connected to UniFi Network at %s but no access.",
                        self.host,
                    )
                    raise UnifiVoucherApiAccessError
                return _sites
        except (
            aiounifi.LoginRequired,
            aiounifi.Unauthorized,
            aiounifi.Forbidden,
        ) as err:
            LOGGER.warning(
                "Connected to UniFi Network at %s but login required: %s",
                self.host,
                err,
            )
            raise UnifiVoucherApiAuthenticationError from err
        except (
            TimeoutError,
            aiounifi.BadGateway,
            aiounifi.ServiceUnavailable,
            aiounifi.RequestError,
            aiounifi.ResponseError,
        ) as err:
            LOGGER.error(
                "Error connecting to the UniFi Network at %s: %s",
                self.host,
                err,
            )
            raise UnifiVoucherApiConnectionError from err
        except (
            aiounifi.AiounifiException,
            Exception,
        ) as err:
            LOGGER.exception(
                "Unknown UniFi Network communication error occurred: %s",
                err,
            )
            raise UnifiVoucherApiError from err
        return False

    async def get_guest_wlans(
        self,
    ) -> list[str] | None:
        """Check the given API user."""
        _wlans = []
        try:
            async with asyncio.timeout(10):
                await self.controller.login()
                await self.controller.wlans.update()
                for _wlan in self.controller.wlans.values():
                    # Is flagged as guest WLAN
                    if _wlan.is_guest:
                        _wlans.append(_wlan.name)

                # No guest WLAN found
                if len(_wlans) == 0:
                    return None
                return _wlans
        except (
            aiounifi.LoginRequired,
            aiounifi.Unauthorized,
            aiounifi.Forbidden,
        ) as err:
            LOGGER.warning(
                "Connected to UniFi Network at %s but login required: %s",
                self.host,
                err,
            )
            raise UnifiVoucherApiAuthenticationError from err
        except (
            TimeoutError,
            aiounifi.BadGateway,
            aiounifi.ServiceUnavailable,
            aiounifi.RequestError,
            aiounifi.ResponseError,
        ) as err:
            LOGGER.error(
                "Error connecting to the UniFi Network at %s: %s",
                self.host,
                err,
            )
            raise UnifiVoucherApiConnectionError from err
        except (
            aiounifi.AiounifiException,
            Exception,
        ) as err:
            LOGGER.exception(
                "Unknown UniFi Network communication error occurred: %s",
                err,
            )
            raise UnifiVoucherApiError from err
        return False

    async def request(
        self,
        api_request: ApiRequest,
    ) -> TypedApiResponse:
        """Make a request to the API, retry login on failure."""
        return await self.controller.request(api_request)
