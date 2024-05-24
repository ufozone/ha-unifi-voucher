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
    Platform.IMAGE,
    Platform.NUMBER,
    Platform.SENSOR,
]

UPDATE_INTERVAL = 300

CONF_SITE_ID = "site_id"
CONF_WLAN_NAME = "wlan_name"
CONF_VOUCHER_NUMBER = "voucher_number"
CONF_VOUCHER_QUOTA = "voucher_quota"
CONF_VOUCHER_DURATION = "voucher_duration"
CONF_VOUCHER_USAGE_QUOTA = "voucher_usage_quota"
CONF_VOUCHER_RATE_MAX_UP = "voucher_rate_max_up"
CONF_VOUCHER_RATE_MAX_DOWN = "voucher_rate_max_down"
CONF_CREATE_IF_NONE_EXISTS = "create_if_none_exists"
CONF_QRCODE_LOGO_PATH = "qrcode_logo_path"

ATTR_EXTRA_STATE_ATTRIBUTES = "extra_state_attributes"
ATTR_LAST_PULL = "last_pull"
ATTR_AVAILABLE = "available"
ATTR_VOUCHER = "voucher"
ATTR_QR_CODE = "qr_code"

DEFAULT_IDENTIFIER_STRING = "HA-generated"
DEFAULT_SITE_ID = "default"
DEFAULT_HOST = ""
DEFAULT_USERNAME = ""
DEFAULT_PASSWORD = ""
DEFAULT_PORT = 443
DEFAULT_VERIFY_SSL = False
DEFAULT_VOUCHER = {
    CONF_VOUCHER_NUMBER: {
        "default": 1,
        "min": 1,
        "max": 10000,
    },
    CONF_VOUCHER_QUOTA: {
        "default": 1,
        "min": 0,
        "max": 10000,
    },
    CONF_VOUCHER_DURATION: {
        "default": 24,
        "min": 1,
        "max": 1000000,
    },
    CONF_VOUCHER_USAGE_QUOTA: {
        "default": 0,
        "min": 0,
        "max": 1048576,
    },
    CONF_VOUCHER_RATE_MAX_UP: {
        "default": 0,
        "min": 0,
        "max": 100000,
    },
    CONF_VOUCHER_RATE_MAX_DOWN: {
        "default": 0,
        "min": 0,
        "max": 100000,
    },
}
