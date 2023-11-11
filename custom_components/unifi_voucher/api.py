"""UniFi Hotspot Manager API Client."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import (
    Self,
    TypedDict,
)

from datetime import (
    timedelta,
    datetime,
)

from aiohttp import CookieJar
import aiounifi
from aiounifi.interfaces.api_handlers import APIHandler
from aiounifi.models.configuration import Configuration
from aiounifi.models.api import (
    ApiItem,
    ApiRequest,
    TypedApiResponse,
)

from homeassistant.core import (
    callback,
    HomeAssistant,
)
from homeassistant.helpers import aiohttp_client
import homeassistant.util.dt as dt_util

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


class UnifiTypedVoucher(TypedDict):
    """Voucher description."""

    _id: str
    site_id: str
    note: str
    code: str
    quota: int
    duration: int
    qos_overwrite: bool
    qos_usage_quota: str
    qos_rate_max_up: int
    qos_rate_max_down: int
    used: int
    create_time: datetime
    start_time: int
    end_time: int
    for_hotspot: bool
    admin_name: str
    status: str
    status_expires: int

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
        """Create voucher create request.

        :param number: number of vouchers
        :param quota: number of using; 0 = unlimited
        :param expire: expiration of voucher in minutes
        :param up_bandwidth: up speed allowed in kbps
        :param down_bandwidth: down speed allowed in kbps
        :param byte_quota: quantity of bytes allowed in MB
        :param note: description
        """
        data = {
            "cmd": "create-voucher",
            "n": number,
            "quota": quota,
            "expire": "custom",
            "expire_number": expire,
            "expire_unit": 1,
            "down": None,
            "up": None,
        }
        if up_bandwidth:
            data["up"] = up_bandwidth
        if down_bandwidth:
            data["down"] = down_bandwidth
        if byte_quota:
            data["bytes"] = byte_quota
        if note:
            data["note"] = note

        return cls(
            method="post",
            path="/cmd/hotspot",
            data=data,
        )


@dataclass
class UnifiVoucherRemoveRequest(ApiRequest):
    """Request object for voucher create."""

    @classmethod
    def create(
        cls,
        obj_id: int,
    ) -> Self:
        """Create voucher remove request."""
        data = {
            "cmd": "delete-voucher",
            "_id": obj_id,
        }
        return cls(
            method="post",
            path="/cmd/hotspot",
            data=data,
        )


class UnifiVoucher(ApiItem):
    """Represents a voucher."""

    raw: UnifiTypedVoucher

    @property
    def id(self) -> str:
        """ID of voucher."""
        return self.raw["_id"]

    @property
    def site_id(self) -> str:
        """Site ID."""
        return self.raw["_id"]

    @property
    def note(self) -> str:
        """Note."""
        return self.raw.get("note") or ""

    @property
    def code(self) -> str:
        """Code."""
        if len(c := self.raw.get("code", "")) > 5:
            return c[:5] + '-' + c[5:]
        return c

    @property
    def quota(self) -> int:
        """Nmber of vouchers."""
        return self.raw.get("quota", 0)

    @property
    def duration(self) -> timedelta:
        """Expiration of voucher."""
        return timedelta(
            minutes=self.raw.get("duration", 0)
        )

    @property
    def qos_overwrite(self) -> bool:
        """Used count."""
        return self.raw.get("qos_overwrite", False)

    @property
    def qos_usage_quota(self) -> int:
        """Quantity of bytes allowed in MB."""
        return int(self.raw.get("qos_usage_quota", 0))

    @property
    def qos_rate_max_up(self) -> int:
        """Up speed allowed in kbps."""
        return self.raw.get("qos_rate_max_up", 0)

    @property
    def qos_rate_max_down(self) -> int:
        """Down speed allowed in kbps."""
        return self.raw.get("qos_rate_max_down", 0)

    @property
    def used(self) -> int:
        """Number of using; 0 = unlimited."""
        return self.raw.get("used", 0)

    @property
    def create_time(self) -> datetime:
        """Create datetime."""
        return dt_util.as_local(
            datetime.fromtimestamp(self.raw["create_time"])
        )

    @property
    def start_time(self) -> datetime | None:
        """Start datetime."""
        if "start_time" in self.raw:
            return dt_util.as_local(
                datetime.fromtimestamp(self.raw["start_time"])
            )
        return None

    @property
    def end_time(self) -> datetime | None:
        """End datetime."""
        if "end_time" in self.raw:
            return dt_util.as_local(
                datetime.fromtimestamp(self.raw["end_time"])
            )
        return None

    @property
    def for_hotspot(self) -> bool:
        """For hotspot."""
        return self.raw.get("for_hotspot", False)

    @property
    def admin_name(self) -> str:
        """Admin name."""
        return self.raw.get("admin_name", "")

    @property
    def status(self) -> str:
        """Status."""
        return self.raw.get("status", "")

    @property
    def status_expires(self) -> int | None:
        """Status expires."""
        if self.raw.get("status_expires", 0) > 0:
            return timedelta(
                seconds=self.raw.get("status_expires")
            )
        return None


class UnifiVouchers(APIHandler[UnifiVoucher]):
    """Represent UniFi vouchers."""

    obj_id_key = "_id"
    item_cls = UnifiVoucher
    api_request = UnifiVoucherListRequest.create()

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
