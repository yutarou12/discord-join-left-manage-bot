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


class JoinLeftNoticeModel(BaseModel):
    """
    入室/退室通知のモデル

    Attributes
    ----------
    function : bool, default False
        入室/退室通知の機能が有効かどうか。
    channel_id : str, default 0
        入室/退室通知を送信するチャンネルのID。
    """
    function: bool = False
    channel_id: int = 0


def icon_convert(icon: Optional[Asset]) -> str:
    if not icon:
        return 'https://cdn.discordapp.com/embed/avatars/0.png'
    else:
        return icon.replace(format='png').url