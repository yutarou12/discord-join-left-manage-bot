import discord
from discord import app_commands, ui, Colour, ButtonStyle, SelectOption, Object
from discord.ext import commands

from libs.origin_handler import JoinLeftNoticeModel, JoinLeftNoticeEmbedMessageModel, JoinLeftNoticeTextMessageModel, HoneyPotModel


class Setting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='設定')
    @app_commands.checks.has_permissions(administrator=True)
    @commands.guild_only()
    async def cmd_setting(self, interaction: discord.Interaction):
        """各種設定を行います。"""
        await interaction.response.defer(ephemeral=True)
        view = SettingView(self.bot.db)

        return await interaction.followup.send(view=view, ephemeral=True)


class SettingView(ui.LayoutView):

    def __init__(self, db):
        super().__init__()
        container = ui.Container(
            ui.TextDisplay(content="# 設定画面"),
            ui.TextDisplay(content='### 各種機能の設定を行います。\n以下の各項目から設定を行ってください。'),
            ui.Separator(),
            ui.Section(
                ui.TextDisplay(content=f'➊ 入退室通知種類設定'),
                accessory=JoinLeftNoticeSettingButton(db)
            ),
            ui.Section(
                ui.TextDisplay(content='➋ 通知先チャンネルの設定'),
                accessory=JoinLeftNoticeChannelSettingButton(db)
            ),
            # ui.Section(
            #     ui.TextDisplay(content='➌ 通知する種類の設定'),
            #     accessory=NoticeTypeSetButton(db)
            # ),
            # ui.Section(
            #     ui.TextDisplay(content='➍ メンションするロールの設定'),
            #     accessory=NoticeRoleSetButton(db)
            # ),
            # ui.Section(
            #     ui.TextDisplay(content='➎ 除外するVCの設定'),
            #     accessory=NoticeExclusionSetButton(db)
            # ),
            # ui.Separator(),
            # ui.Section(
            #     ui.TextDisplay(content='⚠️ 設定の初期化'),
            #     accessory=NoticeSettingResetButtonOnView(db)
            # ),
            accent_color=Colour.green(),
        )

        self.add_item(container)


class BackToSettingButton(ui.Button):
    def __init__(self):
        super().__init__(label='最初に戻る', style=ButtonStyle.gray)

    async def callback(self, interaction: discord.Interaction):
        view = SettingView(interaction.client.db)
        await interaction.response.edit_message(view=view)


class JoinLeftNoticeSettingButton(ui.Button):
    def __init__(self, db):
        self.db = db
        super().__init__(label='切替', style=ButtonStyle.gray)

    async def callback(self, interaction: discord.Interaction):
        # 機能の有効化/無効化切替処理
        join_data = await self.db.get_join_notice(interaction.guild.id)
        left_data = await self.db.get_left_notice(interaction.guild.id)

        view = JoinLeftNoticeSettingView([join_data, left_data], self.db)
        await interaction.response.edit_message(view=view)


class JoinLeftNoticeSettingView(ui.LayoutView):
    row = ui.ActionRow()
    row.add_item(BackToSettingButton())

    def __init__(self, data: list[JoinLeftNoticeModel], db):
        super().__init__()
        # ここに通知種類設定のUI要素を追加
        join_data = data[0]
        left_data = data[1]

        container = ui.Container(
            ui.TextDisplay(content="# 通知種類設定"),
            ui.TextDisplay(content='### 通知する種類を設定します。'),
            ui.Separator(),
            ui.Section(
                ui.TextDisplay(content=f'・入室通知 - {"ON" if join_data.function else "OFF"}'),
                accessory=JoinLeftNoticeToggleButton(_type="join", db=db, data=left_data)
            ),
            ui.Separator(),
            ui.Section(
                ui.TextDisplay(content=f'・退室通知 - {"ON" if left_data.function else "OFF"}'),
                accessory=JoinLeftNoticeToggleButton(_type="leave", db=db, data=join_data)
            ),
            accent_color=Colour.green(),
        )
        self.add_item(container)
        self.remove_item(self.row)
        self.add_item(self.row)


class JoinLeftNoticeToggleButton(ui.Button):
    def __init__(self, _type: str, db, data):
        self._type = _type
        self.db = db
        self.data = data
        super().__init__(label='🔄️', style=ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        if self._type == "join":
            # VC参加通知の切替処理
            new = await self.db.toggle_join_notice(interaction.guild.id)
            return_data = [new, self.data]
        else:
            # VC退出通知の切替処理
            new = await self.db.toggle_left_notice(interaction.guild.id)
            return_data = [self.data, new]

        view = JoinLeftNoticeSettingView(return_data, self.db)
        await interaction.response.edit_message(view=view)


class JoinLeftNoticeChannelSettingButton(ui.Button):
    def __init__(self, db):
        self.db = db
        super().__init__(label='設定', style=ButtonStyle.gray)

    async def callback(self, interaction: discord.Interaction):
        # 通知先チャンネルの設定処理
        join_data = await self.db.get_join_notice(interaction.guild.id)
        left_data = await self.db.get_left_notice(interaction.guild.id)

        view = JoinLeftNoticeChannelSettingView([join_data, left_data], self.db)
        await interaction.response.edit_message(view=view)


class JoinLeftNoticeChannelSettingView(ui.LayoutView):
    row = ui.ActionRow()
    row.add_item(BackToSettingButton())

    def __init__(self, data: list[JoinLeftNoticeModel], db):
        super().__init__()

        container = ui.Container(
            ui.TextDisplay(content="# 通知先チャンネル設定"),
            ui.TextDisplay(content="### 通知先のチャンネルを設定します。"),
            ui.Separator(),
            ui.TextDisplay(content="設定方法"),
            OriginalActionRow(SettingTypeSelect(data, db)),
            accent_colour=Colour.green(),
        )
        self.add_item(container)
        self.remove_item(self.row)
        self.add_item(self.row)


class JoinLeftNoticeChannelSettingBatchView(ui.LayoutView):
    row = ui.ActionRow()
    row.add_item(BackToSettingButton())

    def __init__(self, data: list[JoinLeftNoticeModel], db):
        super().__init__()
        join_data = data[0]
        left_data = data[1]

        container = ui.Container(
            ui.TextDisplay(content="# 通知先チャンネル設定"),
            ui.TextDisplay(content="### 通知先のチャンネルを設定します。"),
            ui.Separator(),
            ui.TextDisplay(content="設定方法"),
            OriginalActionRow(LockedSettingTypeSelect(type="batch")),
            ui.TextDisplay(content="この設定では、入室通知と退室通知の両方が同じチャンネルに送信されます。"),
            ui.Separator(),
            ui.TextDisplay(content="通知先チャンネル"),
                OriginalActionRow(ui.ChannelSelect(
                    placeholder='通知先チャンネルを選択してください。',
                    channel_types=[discord.ChannelType.text],
                    min_values=1,
                    max_values=1,
                )),
            accent_colour=Colour.green(),
        )
        self.add_item(container)
        self.remove_item(self.row)
        self.add_item(self.row)


class JoinLeftNoticeChannelSelect(ui.ChannelSelect):
    def __init__(self, _type, data, db):
        self._type = _type
        self.db = db
        if _type == "single":
            super().__init__(
                placeholder='通知を送信するチャンネルを選択してください。',
                channel_types=[discord.ChannelType.text],
                custom_id='notice_channel_select',
                min_values=1,
                max_values=1,
                disabled=False if data else True,
                default_values=[Object(data.get('single_channel_id'))] if data and data.get('single_channel_id') else None,
            )


class JoinLeftNoticeChannelSettingSingleView(ui.LayoutView):
    row = ui.ActionRow()
    row.add_item(BackToSettingButton())

    def __init__(self, data: list[JoinLeftNoticeModel], db):
        super().__init__()
        join_data = data[0]
        left_data = data[1]

        container = ui.Container(
            ui.TextDisplay(content="# 通知先チャンネル設定"),
            ui.TextDisplay(content="### 通知先のチャンネルを設定します。"),
            ui.Separator(),
            ui.TextDisplay(content="設定方法"),
            OriginalActionRow(LockedSettingTypeSelect(type="single")),
            accent_colour=Colour.green(),
        )
        self.add_item(container)
        self.remove_item(self.row)
        self.add_item(self.row)


class OriginalActionRow(ui.ActionRow):
    def __init__(self, select: ui.Select | ui.ChannelSelect):
        super().__init__()
        self.add_item(select)


class SettingTypeSelect(ui.Select):
    def __init__(self, data, db):
        self.data: list[JoinLeftNoticeModel] = data
        self.db = db
        options = [
            SelectOption(label='一括設定', description='入退室どちらも同じ設定にします。', value='batch'),
            SelectOption(label='個別設定', description='入室/退室の通知先チャンネルを分けて設定します。', value='single'),
        ]
        super().__init__(placeholder='通知先を選択してください。', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_value = self.values[0]

        if selected_value == 'single':
            view = JoinLeftNoticeChannelSettingSingleView(self.data, self.db)
        else:
            view = JoinLeftNoticeChannelSettingBatchView(self.data, self.db)

        await interaction.response.edit_message(view=view)


class LockedSettingTypeSelect(ui.Select):
    def __init__(self, type: str):
        if type == 'single':
            options = [
                SelectOption(label='個別設定', description='入室/退室の通知先チャンネルを分けて設定します。',
                             value='single', default=True),
            ]
        else:
            options = [
                SelectOption(label='一括設定', description='入室/退室どちらも同じ設定にします。',
                             value='batch', default=True),
            ]
        super().__init__(placeholder='通知先を選択してください。', min_values=1, max_values=1, options=options, disabled=True)

async def setup(bot):
    await bot.add_cog(Setting(bot))