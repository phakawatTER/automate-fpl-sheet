from dateutil.tz import gettz
from .config import Config

TIMEZONE = gettz("Asia/Bangkok")

__all__ = ["Config", "TIMEZONE"]
