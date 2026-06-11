import asyncpg
from functools import wraps

import libs.env as env
from libs.origin_handler import JoinLeftNoticeModel, JoinLeftNoticeEmbedMessageModel, JoinLeftNoticeTextMessageModel


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
            # 通知時の通常メッセージデータ
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS message_data  (guild_id bigint NOT NULL PRIMARY KEY, join_message text, left_message text)"
            )
            # 通知時の埋め込みメッセージデータ
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS message_embed_data (guild_id bigint NOT NULL PRIMARY KEY, join_message text, left_message text)"
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

    @check_connection
    async def get_message_data(self, guild_id: int) -> JoinLeftNoticeTextMessageModel:
        """
        通知の通常メッセージを取得する関数

        Parameters
        ----------
        guild_id : :class:`int`
            サーバーID

        Returns
        -------
        message_data: :class:`JoinLeftNoticeTextMessageModel`
            通知の通常メッセージデータのモデル
        """
        async with self.pool.acquire() as con:
            row = await con.fetchrow("SELECT * FROM message_data WHERE guild_id = $1", guild_id)
            data = JoinLeftNoticeTextMessageModel()
            if not row:
                return data
            data.function = True
            data.join_message = row.get("join_message")
            data.left_message = row.get("left_message")
            return data

    @check_connection
    async def add_message_data(self, guild_id: int, message_data: str) -> None:
        """
        通知の通常メッセージを追加する関数

        Parameters
        ----------
        guild_id : :class:`int`
            サーバーID
        message_data : :class:`str`
            通知の通常メッセージデータ
        """
        async with self.pool.acquire() as con:
            await con.execute("INSERT INTO message_data (guild_id, join_message) VALUES ($1, $2) ON CONFLICT (guild_id) DO NOTHING ", guild_id, message_data)

    @check_connection
    async def remove_message_data(self, guild_id: int) -> None:
        """
        通知の通常メッセージを削除する関数

        Parameters
        ----------
        guild_id : :class:`int`
            サーバーID
        """
        async with self.pool.acquire() as con:
            await con.execute("DELETE FROM message_data WHERE guild_id = $1", guild_id)

    @check_connection
    async def update_message_data(self, guild_id: int, message_data: str) -> None:
        """
        通知の通常メッセージを更新する関数

        Parameters
        ----------
        guild_id : :class:`int`
            サーバーID
        message_data : :class:`str`
            通知の通常メッセージデータ
        """
        async with self.pool.acquire() as con:
            await con.execute("UPDATE message_data SET join_message = $1 WHERE guild_id = $2", message_data, guild_id)

    @check_connection
    async def get_message_embed_data(self, guild_id: int) -> JoinLeftNoticeEmbedMessageModel:
        """
        通知の埋め込みメッセージを取得する関数

        Parameters
        ----------
        guild_id : :class:`int`
            サーバーID

        Returns
        -------
        message_data: :class:`JoinLeftNoticeEmbedMessageModel`
            通知の埋め込みメッセージデータのモデル
        """
        async with self.pool.acquire() as con:
            row = await con.fetchrow("SELECT * FROM message_embed_data WHERE guild_id = $1", guild_id)
            data = JoinLeftNoticeEmbedMessageModel()
            if not row:
                return data
            data.function = True
            data.join_message = row.get("join_message")
            data.left_message = row.get("left_message")
            return data

    @check_connection
    async def add_message_embed_data(self, guild_id: int, message_data: str) -> None:
        """
        通知の埋め込みメッセージを追加する関数

        Parameters
        ----------
        guild_id : :class:`int`
            サーバーID
        message_data : :class:`str`
            通知の埋め込みメッセージデータ
        """
        async with self.pool.acquire() as con:
            await con.execute("INSERT INTO message_embed_data (guild_id, join_message) VALUES ($1, $2) ON CONFLICT (guild_id) DO NOTHING ", guild_id, message_data)

    @check_connection
    async def remove_message_embed_data(self, guild_id: int) -> None:
        """
        通知の埋め込みメッセージを削除する関数

        Parameters
        ----------
        guild_id : :class:`int`
            サーバーID
        """
        async with self.pool.acquire() as con:
            await con.execute("DELETE FROM message_embed_data WHERE guild_id = $1", guild_id)

    @check_connection
    async def update_message_embed_data(self, guild_id: int, message_data: str) -> None:
        """
        通知の埋め込みメッセージを更新する関数

        Parameters
        ----------
        guild_id : :class:`int`
            サーバーID
        message_data : :class:`str`
            通知の埋め込みメッセージデータ
        """
        async with self.pool.acquire() as con:
            await con.execute("UPDATE message_embed_data SET join_message = $1 WHERE guild_id = $2", message_data, guild_id)

    @check_connection
    async def get_user_ban_count(self, user_id: int) -> int:
        """
        ユーザーのBanデータを取得する関数

        Parameters
        ----------
        user_id : :class:`int`
            ユーザーID

        Returns
        -------
        count: :class:`int`
            Banされた回数
        """
        async with self.pool.acquire() as con:
            row = await con.fetchrow("SELECT * FROM ban_user_data WHERE user_id = $1", user_id)
            if not row:
                return 0
            return row.get("count")

    @check_connection
    async def update_user_ban_count(self, user_id: int) -> None:
        """
        ユーザーのban回数を更新する関数

        Parameters
        ----------
        user_id: :class:`int`
            ユーザーID
        """

        data = await self.get_user_ban_count(user_id)
        data += 1
        async with self.pool.acquire() as con:
            await con.execute("INSERT INTO ban_user_data (user_id, count) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET count = $2", user_id, data)
