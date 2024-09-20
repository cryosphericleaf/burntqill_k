
import asyncio
import datetime
import discord 
from discord.ext import commands
from discord import app_commands
from discord.ext.commands import Context, BadArgument


from main import QillBot
from .utils.timeutils import Timeconverter as Tc


class Tbuttons(discord.ui.View):
    def __init__(self):
        super().__init__()
    ...


class Time(commands.Cog):
    "Time related commands."

    def __init__(self, bot: QillBot) -> None:
        self.bot: QillBot = bot


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Time(bot))

