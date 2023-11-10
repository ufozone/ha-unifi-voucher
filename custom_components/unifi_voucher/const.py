"""Constants for UniFi Hotspot Manager integration."""
from logging import getLogger

import voluptuous as vol
from homeassistant.const import (
    Platform,
    CONF_DEVICE_ID,
)
from homeassistant.helpers import config_validation as cv

LOGGER = getLogger(__package__)

DOMAIN = "unifi_voucher"
MANUFACTURER = "Ubiquiti Networks"

PLATFORMS = [
    Platform.BUTTON,
    Platform.SENSOR,
]

DEFAULT_SITE_ID = "default"
DEFAULT_VERSION = "UDMP-unifiOS"
DEFAULT_HOST = ""
DEFAULT_PORT = 443
DEFAULT_VERIFY_SSL = False

UPDATE_INTERVAL = 120

CONF_SITE_ID = "site"
CONF_VERSION = "version"

ATTR_EXTRA_STATE_ATTRIBUTES = "extra_state_attributes"
ATTR_AVAILABLE = "available"
ATTR_LAST_PULL = "last_pull"