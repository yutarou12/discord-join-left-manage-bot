import logging
import os
import math
import traceback

import discord
from discord import Embed, Interaction, mentions
from discord.app_commands import AppCommandError
from discord.ext import commands

import libs.env as env
from libs.database import ProductionDatabase
from libs.origin_handler import DatetimeFormatter, icon_convert

extensions_list = [f[:-3] for f in os.listdir("./cogs") if f.endswith(".py")]


def configure_logging(level_name: str) -> logging.Logger:
    level = getattr(logging, level_name, logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid adding duplicate handlers if this function is called multiple times.
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        handler = logging.StreamHandler()
        handler.setLevel(level)
        dt_fmt = "%Y-%m-%d %H:%M:%S"
        formatter = DatetimeFormatter(
            "[{asctime}] [{levelname:<8}] {name}: {message}",
            dt_fmt,
            style="{",
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    logging.getLogger("discord").setLevel(level)
    logging.getLogger("discord.http").setLevel(logging.INFO)

    return logging.getLogger("discord")


class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree.on_error = self.on_app_command_error

    async def on_app_command_error(self, interaction: Interaction, error: AppCommandError):
        traceback_channel = await bot.fetch_channel(env.TRACEBACK_CHANNEL_ID)
        error_channel = await bot.fetch_channel(env.ERROR_CHANNEL_ID)

        if not traceback_channel:
            logging.error("Not Found Traceback channel")
            return None

        if not error_channel:
            logging.error("Not Found Error Channel")
            return None

        tracebacks = getattr(error, 'traceback', error)
        tracebacks = ''.join(traceback.TracebackException.from_exception(tracebacks).format())
        tracebacks = discord.utils.escape_markdown(tracebacks)

        if len(tracebacks) > 4000:
            embed_traceback = []
            for i in range(math.ceil(len(tracebacks) / 4000)):
                tracebacks_cell = tracebacks[i * 4000:(i + 1) * 4000]
                embed_traceback.append(discord.Embed(title='Traceback Log', description=f'```{tracebacks_cell}```'))
        else:
            embed_traceback = [discord.Embed(title='Traceback Log', description=f'```{tracebacks}```')]
        msg_traceback = await traceback_channel.send(embeds=embed_traceback)


        embed_logs = Embed(title='Error Log')
        embed_logs.set_author(name=f'{interaction.user.display_name} ({interaction.user.id})',
                              icon_url=icon_convert(interaction.user.avatar))
        embed_logs.add_field(name='Command', value=interaction.command.name, inline=False)
        embed_logs.add_field(name='Error', value=f'```{error}```', inline=False)
        embed_logs.add_field(name='Traceback Id', value=f'```{msg_traceback.id}```')
        if interaction.channel.type == discord.ChannelType.text:
            embed_logs.set_footer(
                text=f'{interaction.channel.name} \nG:{interaction.guild_id} C:{interaction.channel_id}',
                icon_url=icon_convert(interaction.guild.icon))
        else:
            embed_logs.set_footer(text=f"{interaction.user}'s DM_CHANNEL C:{interaction.channel_id}")

        logging.error(tracebacks)
        return await error_channel.send(embed=embed_logs)

    async def setup_hook(self):
        await bot.load_extension('jishaku')
        for ext in extensions_list:
            await bot.load_extension(f'cogs.{ext}')

    async def get_context(self, message, *args, **kwargs):
        return await super().get_context(message, *args, **kwargs)


if __name__ == '__main__':
    logger = configure_logging("INFO")

    if not env.DISCORD_BOT_TOKEN:
        raise RuntimeError("DISCORD_BOT_TOKEN を .env に設定してください。")

    db = ProductionDatabase()

    bot = MyBot(
        command_prefix=commands.when_mentioned_or('lm.'),
        intents=discord.Intents.all(),
        allowed_mentions=discord.AllowedMentions(replied_user=False, everyone=False, users=False),
        help_command=None
    )

    bot.logger = logger
    bot.db = db

    bot.run(env.DISCORD_BOT_TOKEN, log_handler=None)
