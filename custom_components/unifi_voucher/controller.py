"""Controller for UniFi WiFi Voucher."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import ssl
from types import MappingProxyType
from typing import Any

from aiohttp import CookieJar
import aiounifi
from aiounifi.interfaces.api_handlers import ItemEvent
from aiounifi.models.configuration import Configuration
from aiounifi.models.device import DeviceSetPoePortModeRequest

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    Platform,
)
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers import (
    aiohttp_client,
    device_registry as dr,
    entity_registry as er,
)
from homeassistant.helpers.device_registry import (
    DeviceEntry,
    DeviceEntryType,
    DeviceInfo,
)
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity_registry import async_entries_for_config_entry
from homeassistant.helpers.event import async_call_later, async_track_time_interval
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
from .errors import AuthenticationRequired, CannotConnect

async def get_unifi_controller(
    hass: HomeAssistant,
    config: MappingProxyType[str, Any],
) -> aiounifi.Controller:
    """Create a controller object and verify authentication."""
    ssl_context: ssl.SSLContext | bool = False

    if verify_ssl := config.get(CONF_VERIFY_SSL):
        session = aiohttp_client.async_get_clientsession(hass)
        if isinstance(verify_ssl, str):
            ssl_context = ssl.create_default_context(cafile=verify_ssl)
    else:
        session = aiohttp_client.async_create_clientsession(
            hass, verify_ssl=False, cookie_jar=CookieJar(unsafe=True)
        )

    controller = aiounifi.Controller(
        Configuration(
            session,
            host=config[CONF_HOST],
            username=config[CONF_USERNAME],
            password=config[CONF_PASSWORD],
            port=config[CONF_PORT],
            site=config[CONF_SITE_ID],
            ssl_context=ssl_context,
        )
    )

    try:
        async with asyncio.timeout(10):
            await controller.login()
        return controller

    except aiounifi.Unauthorized as err:
        LOGGER.warning(
            "Connected to UniFi Network at %s but not registered: %s",
            config[CONF_HOST],
            err,
        )
        raise AuthenticationRequired from err

    except (
        asyncio.TimeoutError,
        aiounifi.BadGateway,
        aiounifi.ServiceUnavailable,
        aiounifi.RequestError,
        aiounifi.ResponseError,
    ) as err:
        LOGGER.error(
            "Error connecting to the UniFi Network at %s: %s", config[CONF_HOST], err
        )
        raise CannotConnect from err

    except aiounifi.LoginRequired as err:
        LOGGER.warning(
            "Connected to UniFi Network at %s but login required: %s",
            config[CONF_HOST],
            err,
        )
        raise AuthenticationRequired from err

    except aiounifi.AiounifiException as err:
        LOGGER.exception("Unknown UniFi Network communication error occurred: %s", err)
        raise AuthenticationRequired from err
