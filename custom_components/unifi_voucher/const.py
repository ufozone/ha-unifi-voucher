"""Constants for UniFi Hotspot Manager integration."""
from logging import getLogger

from homeassistant.const import (
    Platform,
)

LOGGER = getLogger(__package__)

DOMAIN = "unifi_voucher"
MANUFACTURER = "Ubiquiti Networks"

PLATFORMS = [
    Platform.BUTTON,
    Platform.SENSOR,
]

DEFAULT_SITE_ID = "default"
DEFAULT_HOST = ""
DEFAULT_USERNAME = ""
DEFAULT_PASSWORD = ""
DEFAULT_PORT = 443
DEFAULT_VERIFY_SSL = False
DEFAULT_VOUCHER_NUMBER = 1
DEFAULT_VOUCHER_QUOTA = 1
DEFAULT_VOUCHER_EXPIRE = 480

UPDATE_INTERVAL = 120

CONF_SITE_ID = "site_id"
CONF_DEFAULT_VOUCHER_NUMBER = "default_voucher_number"
CONF_DEFAULT_VOUCHER_QUOTA = "default_voucher_quota"
CONF_DEFAULT_VOUCHER_EXPIRE = "default_voucher_expire"

ATTR_EXTRA_STATE_ATTRIBUTES = "extra_state_attributes"
ATTR_LAST_PULL = "last_pull"
ATTR_AVAILABLE = "available"
ATTR_VOUCHER = "voucher"
