from discord import Embed, Colour, Message
from discord.ext import commands

from libs.origin_handler import icon_convert
from libs.database import ProductionDatabase


class HoneyPot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db: ProductionDatabase = bot.db

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        """
        ハニーポット機能：指定したチャンネルにメッセージが送信されると、強制的にBanされる機能。
        スパムユーザーが入室後、詐欺のメッセージ等を全チャンネルに送信するために、それを検知してBanするための機能。
        """
        if message.author.bot:
            return None

        data = await self.db.get_honey_pot_channel(message.guild.id)
        if not data.function:
            return None

        if not data.channel_id:
            return None

        if data.channel_id != message.channel.id:
            return None

        data = await self.db.get_honey_pot_log_channel(message.guild.id)
        if data.function:
            if bool(data.channel_id):
                channel = message.guild.get_channel(data.channel_id)
                if channel is None:
                    channel = await message.guild.fetch_channel(data.channel_id)

                if channel is not None:
                    embed = Embed(title="ハニーポット 検知", description=f"```\n{message.author.display_name} をBanしました。\n```",
                                  colour=Colour.red())
                    embed.set_thumbnail(url=icon_convert(message.author.avatar))
                    embed.add_field(name="ユーザーID", value=f"`{message.author.id}`", inline=False)
                    embed.add_field(name="メッセージ内容ログID", value=f"`{message.id}`", inline=False)

                    embed_log = Embed(title="ハニーポット ログ", colour=Colour.red())
                    if not message.attachments:
                        if len(message.content) > 4000:
                            log_msg = message.content[:4000] + "..."
                        else:
                            log_msg = message.content
                        embed_log.description = f"```\n{log_msg}\n```"
                    else:
                        if message.content:
                            log_msg = f"```\n{message.content}\n```"
                        else:
                            log_msg = ""
                        for attachment in message.attachments:
                            log_msg += f"\n- [{attachment.filename}]({attachment.url})"
                        embed_log.description = log_msg
                        embed_log.set_image(url=message.attachments[0].url)
                    embed_log.set_footer(text=f"ログID：{message.id}", icon_url=icon_convert(message.author.avatar))

                    await channel.send(embeds=[embed,embed_log])

        return await message.guild.ban(message.author, delete_message_days=1, reason="ハニーポットチャンネルにメッセージを送信したため。")


async def setup(bot):
    await bot.add_cog(HoneyPot(bot))