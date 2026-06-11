from discord.ext import commands

from libs.origin_handler import JoinLeftNoticeModel


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

        return await channel.send(f"> 📥{member.mention} ({member.id}) さんが入室しました")

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

        return await channel.send(f"> 📤{member.mention} ({member.id}) さんが退出しました")


async def setup(bot):
    await bot.add_cog(JoinLeft(bot))