from typing import Union

from discord import Guild, User, Member
from discord.ext import commands

from libs.database import ProductionDatabase


class BanEvent(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db: ProductionDatabase = bot.db

    @commands.Cog.listener()
    async def on_member_ban(self, guild: Guild, user: Union[Member, User]):
        await self.db.update_user_ban_count(user.id)


async def setup(bot):
    await bot.add_cog(BanEvent(bot))