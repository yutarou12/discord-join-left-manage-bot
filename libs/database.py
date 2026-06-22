import asyncpg
from functools import wraps

import libs.env as env
from libs.origin_handler import JoinLeftNoticeModel, JoinLeftNoticeEmbedMessageModel, JoinLeftNoticeTextMessageModel, HoneyPotModel


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
            # 導入サーバーでのBanデータの収集
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS ban_user_data (user_id bigint NOT NULL, count int NOT NULL, PRIMARY KEY (user_id))"
            )
            # ハニーポット機能のチャンネルID
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS honey_pot_channel (guild_id bigint NOT NULL PRIMARY KEY, channel_id bigint NOT NULL)"
            )
            # ハニーポットでBANした際のログチャンネルID
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS honey_pot_log_channel (guild_id bigint NOT NULL PRIMARY KEY, channel_id bigint NOT NULL)"
            )
            # ハニーポット機能の除外するロール
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS honey_pot_ignore_role (guild_id bigint NOT NULL, role_id bigint NOT NULL, PRIMARY KEY (guild_id, role_id))"
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
    async def toggle_join_notice(self, guild_id: int) -> JoinLeftNoticeModel | None:
        """
        Discordサーバーへの入室通知の設定を切り替える関数

        Parameters
        ----------
        guild_id : :class:`int`
            サーバーID
        """
        async with self.pool.acquire() as con:
            row = await self.get_join_notice(guild_id)
            if row.function:
                await con.execute("DELETE FROM join_notice_bool WHERE guild_id = $1", guild_id)
            else:
                await con.execute("INSERT INTO join_notice_bool (guild_id) VALUES ($1)", guild_id)
            new = await self.get_join_notice(guild_id)
            return new

    @check_connection
    async def toggle_left_notice(self, guild_id: int) -> JoinLeftNoticeModel | None:
        """
        Discordサーバーからの退室通知の設定を切り替える関数

        Parameters
        ----------
        guild_id : :class:`int`
            サーバーID
        """
        async with self.pool.acquire() as con:
            row = await self.get_left_notice(guild_id)
            if row.function:
                await con.execute("DELETE FROM left_notice_bool WHERE guild_id = $1", guild_id)
            else:
                await con.execute("INSERT INTO left_notice_bool (guild_id) VALUES ($1)", guild_id)
            new = await self.get_left_notice(guild_id)
            return new

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

    @check_connection
    async def get_honey_pot_channel(self, guild_id: int) -> HoneyPotModel:
        """
        ハニーポットチャンネルのIDを取得する関数

        Parameters
        ----------
        guild_id: :class:`int`
            サーバーID

        """
        async with self.pool.acquire() as con:
            row = await con.fetchrow("SELECT * FROM honey_pot_channel WHERE guild_id = $1", guild_id)
            data = HoneyPotModel()
            if not row:
                return data
            data.function = True
            data.channel_id = row.get("channel_id") or 0
            return data

    @check_connection
    async def add_honey_pot_channel(self, guild_id: int, channel_id: int) -> None:
        """
        ハニーポットチャンネルを追加する関数

        Parameters
        ----------
        guild_id: :class:`int`
            サーバーID
        channel_id: :class:`int`
            ハニーポットチャンネルのID
        """
        async with self.pool.acquire() as con:
            await con.execute("INSERT INTO honey_pot_channel (guild_id, channel_id) VALUES ($1, $2) ON CONFLICT (guild_id) DO NOTHING", guild_id, channel_id)

    @check_connection
    async def update_honey_pot_channel(self, guild_id: int, channel_id: int) -> None:
        """
        ハニーポットチャンネルを更新する関数

        Parameters
        ----------
        guild_id: :class:`int`
            サーバーID
        channel_id: :class:`int`
            ハニーポットチャンネルのID
        """
        async with self.pool.acquire() as con:
            await con.execute("UPDATE honey_pot_channel SET channel_id = $1 WHERE guild_id = $2", channel_id, guild_id)

    @check_connection
    async def remove_honey_pot_channel(self, guild_id: int) -> None:
        """
        ハニーポットチャンネルを削除する関数

        Parameters
        ----------
        guild_id: :class:`int`
            サーバーID
        """
        async with self.pool.acquire() as con:
            await con.execute("DELETE FROM honey_pot_channel WHERE guild_id = $1", guild_id)

    @check_connection
    async def get_honey_pot_log_channel(self, guild_id: int) -> HoneyPotModel:
        """
        ハニーポットでBANした際のログチャンネルのIDを取得する関数

        Parameters
        ----------
        guild_id: :class:`int`
            サーバーID

        """
        async with self.pool.acquire() as con:
            row = await con.fetchrow("SELECT * FROM honey_pot_log_channel WHERE guild_id = $1", guild_id)
            data = HoneyPotModel()
            if not row:
                return data
            data.function = True
            data.channel_id = row.get("channel_id") or 0
            return data

    @check_connection
    async def add_honey_pot_log_channel(self, guild_id: int, channel_id: int) -> None:
        """
        ハニーポットでBANした際のログチャンネルを追加する関数

        Parameters
        ----------
        guild_id: :class:`int`
            サーバーID
        channel_id: :class:`int`
            ハニーポットでBANした際のログチャンネルのID
        """
        async with self.pool.acquire() as con:
            await con.execute("INSERT INTO honey_pot_log_channel (guild_id, channel_id) VALUES ($1, $2) ON CONFLICT (guild_id) DO NOTHING", guild_id, channel_id)

    @check_connection
    async def update_honey_pot_log_channel(self, guild_id: int, channel_id: int) -> None:
        """
        ハニーポットでBANした際のログチャンネルを更新する関数

        Parameters
        ----------
        guild_id: :class:`int`
            サーバーID
        channel_id: :class:`int`
            ハニーポットでBANした際のログチャンネルのID
        """
        async with self.pool.acquire() as con:
            await con.execute("UPDATE honey_pot_log_channel SET channel_id = $1 WHERE guild_id = $2", channel_id, guild_id)

    @check_connection
    async def remove_honey_pot_log_channel(self, guild_id: int) -> None:
        """
        ハニーポットでBANした際のログチャンネルを削除する関数

        Parameters
        ----------
        guild_id: :class:`int`
            サーバーID
        """
        async with self.pool.acquire() as con:
            await con.execute("DELETE FROM honey_pot_log_channel WHERE guild_id = $1", guild_id)

    @check_connection
    async def get_honey_pot_ignore_roles(self, guild_id: int) -> list[int]:
        """
        ハニーポット機能の除外するロールのIDを取得する関数

        Parameters
        ----------
        guild_id: :class:`int`
            サーバーID

        Returns
        -------
        role_ids: list[:class:`int`]
            ハニーポット機能の除外するロールのIDのリスト
        """
        async with self.pool.acquire() as con:
            rows = await con.fetch("SELECT * FROM honey_pot_ignore_role WHERE guild_id = $1", guild_id)
            if not rows:
                return []
            return [row.get("role_id") for row in rows]

    @check_connection
    async def add_honey_pot_ignore_role(self, guild_id: int, role_ids: list[int]) -> None:
        """
        ハニーポット機能の除外するロールを追加する関数

        Parameters
        ----------
        guild_id: :class:`int`
            サーバーID
        role_ids: :class:`list[int]`
            除外するロールのID
        """
        async with self.pool.acquire() as con:
            for role_id in role_ids:
                await con.execute("INSERT INTO honey_pot_ignore_role (guild_id, role_id) VALUES ($1, $2) ON CONFLICT (role_id) DO NOTHING", guild_id, role_id)