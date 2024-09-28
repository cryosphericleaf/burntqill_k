from __future__ import annotations

import traceback

import config
import discord 
from discord.ext import commands
from discord.ext.commands import Context
import motor.motor_asyncio
import logging
from cogs.help import MyHelp
import asqlite


log = logging.getLogger(__name__)

class QillBot(commands.AutoShardedBot):  
    conn: asqlite.Connection
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned_or(","),
            intents=discord.Intents.all(),
            help_command=MyHelp() 
        )
    
    async def setup_hook(self):
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="something"))
        self.mongoConnect = motor.motor_asyncio.AsyncIOMotorClient(config.MONGODB)
        self.db = self.mongoConnect['qill']
     
        print('Connected to MongoDB')

        extensions = [
            'cogs.basic',
            'cogs.jik',
            'cogs.images',
            'cogs.jisho',
            'cogs.autoresponder',
            'cogs.misc',
            'cogs.time',
            'cogs.serverutils',
            'cogs.maths',
            'cogs.triggerlistner',
            'cogs.doubles'
        ]

        for extension in extensions:
            try:
                await self.load_extension(extension)
            except Exception as e:
                traceback.print_exc()
                print(f'Error loading extension {extension}: {e}')

  
    async def on_command_error(self, ctx: Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.author.send('This command cannot be used in private messages.')
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(f"you are missing permissions.")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"This command is on cooldown. :)")
        elif isinstance(error, commands.DisabledCommand):
            await ctx.author.send('Sorry. This command is disabled and cannot be used.')
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.author.send(f'{str(error)}')
        elif isinstance(error, discord.Forbidden):
            try:
                await ctx.author.send(f'{str(error)}')
            except Exception:
                log.exception('In %s:', ctx.command.qualified_name)

        elif isinstance(error, commands.CommandInvokeError):
            original = error.original
            if not isinstance(original, discord.HTTPException):
                log.exception('In %s:', ctx.command.qualified_name, exc_info=original)

        elif isinstance(error, commands.ArgumentParsingError):
            await ctx.send(str(error))

    async def start(self):
        await super().start(config.BOT_TOKEN)
        
    async def close(self):
        await super().close()
        await self.conn.close()

    async def on_ready(self):
        print(f"i am up as {self.user.name} ({self.user.id})")




