import asyncpg
from functools import wraps

import libs.env as env
from libs.origin_handler import JoinLeftNoticeModel


class ProductionDatabase:
    def __init__(self):
        self.pool: asyncpg.Pool | None = None

    async def setup(self):
        self.pool: asyncpg.Pool = await asyncpg.create_pool(f"postgresql://{env.POSTGRESQL_USER}:{env.POSTGRESQL_PASSWORD}@{env.POSTGRESQL_HOST_NAME}:{env.POSTGRESQL_PORT}/{env.POSTGRESQL_DATABASE_NAME}")

        async with self.pool.acquire() as conn:
            # Discordサーバーへの入室通知
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS join_notice_bool (guild_id bigint NOT NULL PRIMARY KEY, channel_id bigint)"
            )
            # Discordサーバーからの退室通知
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS left_notice_bool (guild_id bigint NOT NULL PRIMARY KEY, channel_id bigint)"
            )
            # 通知時のメッセージデータ
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS message_data (guild_id bigint NOT NULL PRIMARY KEY, join_message text, left_message text)"
            )

        return self.pool

    def check_connection(func):
        @wraps(func)
        async def inner(self, *args, **kwargs):
            self.pool = self.pool or (await self.setup())
            return await func(self, *args, **kwargs)

        return inner

    @check_connection
    async def execute(self, sql):
        async with self.pool.acquire() as con:
            await con.execute(sql)

    @check_connection
    async def fetch(self, sql):
        async with self.pool.acquire() as con:
            data = await con.fetch(sql)
        return data

    @check_connection
    async def get_join_notice(self, guild_id: int) -> JoinLeftNoticeModel:
        """
        Discordサーバーへの入室通知の設定を取得する関数

        Parameters
        ----------
        guild_id : :class:`int`
            サーバーID

        Returns
        -------
        data: JoinLeftNoticeModel, optional
            入室通知の設定データ
        """
        async with self.pool.acquire() as con:
            row = await con.fetchrow("SELECT * FROM join_notice_bool WHERE guild_id = $1", guild_id)
            data = JoinLeftNoticeModel()
            if row:
                data.function = True
                data.channel_id = 0 if row.get("channel_id") is None else row.get("channel_id")
            return data

    @check_connection
    async def get_left_notice(self, guild_id: int) -> JoinLeftNoticeModel:
        """
        Discordサーバーからの退室通知の設定を取得する関数

        Parameters
        ----------
        guild_id : int
            サーバーID

        Returns
        ----------
        JoinLeftNoticeModel
        """
        async with self.pool.acquire() as con:
            row = await con.fetchrow("SELECT * FROM left_notice_bool WHERE guild_id = $1", guild_id)
            data = JoinLeftNoticeModel()
            if row:
                data.function = True
                data.channel_id = 0 if row.get("channel_id") is None else row.get("channel_id")
            return data

    @check_connection
    async def add_join_notice(self, guild_id: int) -> None:
        """
        Discordサーバーへの入室通知の設定を有効にする関数

        Parameters
        ----------
        guild_id : :class:`int`
            サーバーID
        """
        async with self.pool.acquire() as con:
            await con.execute("INSERT INTO join_notice_bool (guild_id) VALUES ($1) ON CONFLICT (guild_id) DO NOTHING", guild_id)

    @check_connection
    async def add_left_notice(self, guild_id: int) -> None:
        """
        Discordサーバーからの退室通知の設定を有効にする関数

        Parameters
        ----------
        guild_id : :class:`int`
            サーバーID
        """
        async with self.pool.acquire() as con:
            await con.execute("INSERT INTO left_notice_bool (guild_id) VALUES ($1) ON CONFLICT (guild_id) DO NOTHING", guild_id)

    @check_connection
    async def remove_join_notice(self, guild_id: int) -> None:
        """
        Discordサーバーへの入室通知の設定を無効にする関数

        Parameters
        ----------
        guild_id : :class:`int`
            サーバーID
        """
        async with self.pool.acquire() as con:
            await con.execute("DELETE FROM join_notice_bool WHERE guild_id = $1", guild_id)

    @check_connection
    async def remove_left_notice(self, guild_id: int) -> None:
        """
        Discordサーバーからの退室通知の設定を無効にする関数

        Parameters
        ----------
        guild_id : :class:`int`
            サーバーID
        """
        async with self.pool.acquire() as con:
            await con.execute("DELETE FROM left_notice_bool WHERE guild_id = $1", guild_id)

    @check_connection
    async def update_join_notice_channel(self, guild_id: int, channel_id: int) -> None:
        """
        入室時の通知チャンネルを更新する関数

        Parameters
        ----------
        guild_id : :class:`int`
            サーバーID
        channel_id : :class:`int`
            通知先チャンネルID
        """
        async with self.pool.acquire() as con:
            await con.execute("UPDATE join_notice_bool SET channel_id = $1 WHERE guild_id = $2", channel_id, guild_id)

    @check_connection
    async def update_left_notice_channel(self, guild_id: int, channel_id: int) -> None:
        """
        退室時の通知チャンネルを更新する関数

        Parameters
        ----------
        guild_id : :class:`int`
            サーバーID
        channel_id : :class:`int`
            通知先チャンネルID
        """
        async with self.pool.acquire() as con:
            await con.execute("UPDATE left_notice_bool SET channel_id = $1 WHERE guild_id = $2", channel_id, guild_id)

