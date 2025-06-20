"""Constants used throughout the application."""

from enum import Enum

DEFAULT_TAX_RATE = 0.0825

GOOGDIT_PRICE_DIVISOR = 100_000_000

REQUEST_TIMEOUT = 10.0


class PlatformURLs:
    """URLs for different e-commerce platforms."""

    GOOGDIT = "https://googdit.heb-platform-interview.hebdigital-prd.com"
    APPEDIA = "https://appedia.heb-platform-interview.hebdigital-prd.com"
    MICROMAZON = "https://micromazon.heb-platform-interview.hebdigital-prd.com"


class PlatformType(Enum):
    """Enumeration of supported platforms."""

    GOOGDIT = "googdit"
    APPEDIA = "appedia"
    MICROMAZON = "micromazon"
