import logging
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta

from discord import Asset


class DatetimeFormatter(logging.Formatter):
    def formatTime(self, record: logging.LogRecord, datefmt=None):
        if datefmt is None:
            datefmt = "%Y-%m-%d %H:%M:%S,%03d"

        TZ_JST = timezone(timedelta(hours=+9), 'JST')
        created_time = datetime.fromtimestamp(record.created, tz=TZ_JST)
        s = created_time.strftime(datefmt)

        return s


class GuildDataModel(BaseModel):
    notice_bool: bool
    join_notice_channel_id: int
    left_notice_channel_id: int


def icon_convert(icon: Optional[Asset]) -> str:
    if not icon:
        return 'https://cdn.discordapp.com/embed/avatars/0.png'
    else:
        return icon.replace(format='png').url