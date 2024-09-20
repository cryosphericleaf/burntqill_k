from __future__ import annotations

import discord 
from main import QillBot
from discord.ext import commands 


    


class Triggers(commands.Cog):

    def __init__(self, bot: QillBot):
        self.bot: QillBot = bot
        self.collection = self.bot.db['triggers']

    def is_allowed(self, user):
        allowed_users = [771364000796508160, 846198992488628266]  
        return user.id in allowed_users


    async def cog_check(self, ctx):
        if not self.is_allowed(ctx.author):
            return False
        return True
       
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        content = message.content.lower()
        server_id = str(message.guild.id)
        triggers = self.collection.find({"server_id": server_id})

        async for trigger_doc in triggers:
            trigger = trigger_doc['trigger']
            if ((trigger_doc['f_type'] == 'contains' and trigger in content) or
                (trigger_doc['f_type'] == 'startswith' and content.startswith(trigger)) or
                (trigger_doc['f_type'] == 'endswith' and content.endswith(trigger)) or
                (trigger_doc['f_type'] == 'strict' and trigger == content)):
                resp = trigger_doc["resp"]
                await message.channel.send(resp)
                break


async def setup(bot: QillBot):
    await bot.add_cog(Triggers(bot))

