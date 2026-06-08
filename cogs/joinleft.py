from discord.ext import commands

from libs.origin_handler import GuildDataModel


class JoinLeft(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild_list = [881390536504799234, 1339605648975069287]
        self.guild_data: dict[int, GuildDataModel] = {}

    def setup(self, bot):
        self.guild_data.update({1339605648975069287:GuildDataModel(notice_bool=True, join_notice_channel_id=1513502054528712804, left_notice_channel_id=1513502054528712804)})

    @commands.Cog.listener()
    async def on_member_join(self, member):
        _guild = member.guild

        self.setup(self.bot)

        if _guild.id not in self.guild_list:
            # Handle member join logic for specific guilds
            return None

        if not self.guild_data.get(_guild.id):
            return None

        if not self.guild_data.get(_guild.id).notice_bool:
            return None

        guild_data = self.guild_data.get(_guild.id)

        channel = member.guild.get_channel(guild_data.join_notice_channel_id)
        if channel is None:
            channel = await member.guild.fetch_channel(guild_data.join_notice_channel_id)

        if channel is None:
            return None

        return await channel.send(f"> 📥{member.mention} さんが入室しました")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        _guild = member.guild

        self.setup(self.bot)

        if _guild.id not in self.guild_list:
            # Handle member remove logic for specific guilds
            return None

        if not self.guild_data.get(_guild.id):
            return None

        if not self.guild_data.get(_guild.id).notice_bool:
            return None

        guild_data = self.guild_data.get(_guild.id)

        channel = member.guild.get_channel(guild_data.left_notice_channel_id)
        if channel is None:
            channel = await member.guild.fetch_channel(guild_data.left_notice_channel_id)

        if channel is None:
            return None

        return await channel.send(f"> 📤{member.mention} さんが退出しました")


async def setup(bot):
    await bot.add_cog(JoinLeft(bot))