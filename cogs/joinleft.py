import math
from datetime import datetime, timezone

from discord import Embed
from discord.ext import commands

from libs.origin_handler import JoinLeftNoticeModel
from libs.origin_handler import JoinLeftNoticeModel, icon_convert
def create_embed(member, notice_type: str, ban_count: int):
    if notice_type == 'join':
        title = '入室通知'
        time_text = '入室時間'
        color = 0x00ff00
        description = f'{member.mention} さんが入室しました'
    elif notice_type == 'left':
        title = '退室通知'
        time_text = '退室時間'
        color = 0xff0000
        description = f'{member.mention} さんが退出しました'
    else:
        raise ValueError('Invalid notice type')

    embed = Embed(title=title, description=description, color=color)
    embed.add_field(name='ユーザーID', value=f'`{member.id}`', inline=False)
    embed.add_field(name=time_text, value=f'<t:{math.floor(datetime.now(timezone.utc).timestamp())}:S>', inline=False)
    embed.add_field(name='アカウント作成日', value=f'<t:{math.floor(member.created_at.timestamp())}:S>', inline=False)
    embed.add_field(name=f'危険度 - {danger_level(member, ban_count, "level")}', value=danger_level(member, ban_count, "detail"), inline=False)
    embed.set_thumbnail(url=icon_convert(member.display_avatar))
    return embed


class JoinLeft(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    @commands.Cog.listener()
    async def on_member_join(self, member):
        _guild = member.guild

        data: JoinLeftNoticeModel = await self.db.get_join_notice(_guild.id)

        if not data.function:
            return None

        if bool(data.channel_id):
            channel = member.guild.get_channel(data.channel_id)
            if channel is None:
                channel = await member.guild.fetch_channel(data.channel_id)

                if channel is None:
                    return None
        else:
            if not _guild.system_channel:
                return None
            channel = _guild.system_channel

        embed_data = await self.db.get_message_embed_data(_guild.id)
        if embed_data.function:
            ban_count = await self.db.get_user_ban_count(member.id)
            embed = create_embed(member, 'join', ban_count)
            return await channel.send(embed=embed)
        else:
            text_data = await self.db.get_message_data(_guild.id)
            if text_data.function:
                text = text_data.join_message or f"> [ 📥 入室通知 ]{member.mention} ({member.id}) さんが入室しました"
            else:
                text = f"> 📥{member.mention} (`{member.id}`) さんが入室しました"
            return await channel.send(text)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        _guild = member.guild

        data: JoinLeftNoticeModel = await self.db.get_left_notice(_guild.id)

        if not data.function:
            return None

        if bool(data.channel_id):
            channel = member.guild.get_channel(data.channel_id)
            if channel is None:
                channel = await member.guild.fetch_channel(data.channel_id)

                if channel is None:
                    return None
        else:
            if not _guild.system_channel:
                return None
            channel = _guild.system_channel

        embed_data = await self.db.get_message_embed_data(_guild.id)
        if embed_data.function:
            ban_count = await self.db.get_user_ban_count(member.id)
            embed = create_embed(member, 'left', ban_count)
            return await channel.send(embed=embed)
        else:
            text_data = await self.db.get_message_data(_guild.id)
            if text_data.function:
                text = text_data.left_message or f"> [ 📤 退室通知 ]{member.mention} ({member.id}) さんが退出しました"
            else:
                text = f"> 📤{member.mention} (`{member.id}`) さんが退出しました"
            return await channel.send(text)


async def setup(bot):
    await bot.add_cog(JoinLeft(bot))