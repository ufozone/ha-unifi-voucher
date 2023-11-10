"""UniFi Hotspot Manager API Client."""
from __future__ import annotations

import asyncio
import ssl
from dataclasses import dataclass

from aiohttp import CookieJar
import aiounifi
from aiounifi.interfaces.api_handlers import ItemEvent
from aiounifi.interfaces.sites import Sites
from aiounifi.models.configuration import Configuration
from aiounifi.models.api import ApiItem, ApiRequest

from homeassistant.core import (
    callback,
    HomeAssistant,
)
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)

from .const import (
    LOGGER,
    DOMAIN,
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


@dataclass
class UnifiVoucherListRequest(ApiRequest):
    """Request object for device list."""

    @classmethod
    def create(
        cls
    ) -> Self:
        """Create voucher list request."""
        return cls(
            method="get",
            path="/stat/voucher",
        )

@dataclass
class UnifiVoucherCreateRequest(ApiRequest):
    """Request object for voucher create."""

    @classmethod
    def create(
        cls,
        number: int,
        quota: int,
        expire: int,
        up_bandwidth: int | None = None,
        down_bandwidth: int | None = None,
        byte_quota: int | None = None,
        note: str | None = None,
    ) -> Self:
        """
        Create voucher create request.

        :param number: number of vouchers
        :param quota: number of using; 0 = unlimited
        :param expire: expiration of voucher in minutes
        :param up_bandwidth: up speed allowed in kbps
        :param down_bandwidth: down speed allowed in kbps
        :param byte_quota: quantity of bytes allowed in MB
        :param note: description
        """
        params = {
            "n": number,
            "quota": quota,
            "expire": "custom",
            "expire_number": expire,
            "expire_unit": 1,
        }
        if up_bandwidth:
            params["up"] = up_bandwidth
        if down_bandwidth:
            params["down"] = down_bandwidth
        if byte_quota:
            params["bytes"] = byte_quota
        if note:
            params["note"] = note
        
        return cls(
            method="post",
            path="/cmd/hotspot",
            data={
                "cmd": "create-voucher",
                "params": params,
            },
        )

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
        self.api = aiounifi.Controller(
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
                await self.api.login()
        except (
            asyncio.TimeoutError,
            aiounifi.BadGateway,
            aiounifi.ServiceUnavailable,
            aiounifi.AiounifiException,
        ):
            self.hass.loop.call_later(RETRY_TIMER, self.reconnect)

    async def check_api_user(
        self,
    ) -> dict[str, any]:
        """Check the given API user."""
        _sites = {}
        try:
            async with asyncio.timeout(10):
                await self.api.login()
                
                await self.api.sites.update()
                for _id, _site in self.api.sites.items():
                    if _site.role in ("admin", "hotspot"):
                        _sites[_id] = _site.description
                if len(_sites) == 0:
                    LOGGER.warning(
                        "Connected to UniFi Network at %s but no access.",
                        self.host,
                    )
                    raise UnifiVoucherApiAccessError
                return _sites
        except (
            asyncio.TimeoutError,
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
        except aiounifi.AiounifiException as err:
            LOGGER.exception("Unknown UniFi Network communication error occurred: %s", err)
            raise UnifiVoucherApiError from err
        return False
