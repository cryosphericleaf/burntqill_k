from discord.ext import commands
import discord
from typing import Any, Optional, Literal
from .utils.testpages import PageView
from main import QillBot


class Jiken(commands.Cog):
    def __init__(self, bot: QillBot) -> None:
        self.bot: QillBot = bot
        self.tree = bot.tree  
        self.collection = self.bot.db['servers']
        self.betr = self.bot.db['betr']
        self.allowed_users = [771364000796508160, 846198992488628266] 


    async def cog_check(self, ctx: commands.Context):
        if ctx.author.id in self.allowed_users:
            return True
        return False


    @commands.command(name='synccc')
    async def synccc(self, ctx: commands.Context, spec: Optional[Literal["~"]] = None) -> None:
        try:
            if ctx.author.id == 771364000796508160 or 846198992488628266: 
                if spec == "~":
                    await ctx.bot.tree.sync(guild=ctx.guild)
                else:
                    await self.tree.sync()
                await ctx.send('done （￣︶￣）↗')
            else:
                await ctx.send('...')
        except Exception as e:
            print(e)




    @commands.command(name='reload')
    async def reload(self, ctx: commands.Context, cog: str) -> None:
        if ctx.author.id not in self.allowed_users:
            return
        try:
            await self.bot.reload_extension(name=f"{cog}")
            await ctx.send(f'reloaded `{cog}`')
        except Exception as e:
            await ctx.send(f"error\n ```py\n{e}```")


    @commands.Cog.listener()
    async def on_command(self, ctx: Any) -> None:
        if ctx.author.bot:
            return

        user_id: str = str(ctx.author.id)
        user_collection = self.bot.db["users"]
        user_doc = await user_collection.find_one({"_id": user_id})

        if not user_doc:
            new_user_document: dict = {"_id": user_id}
            await user_collection.insert_one(new_user_document)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        
        server_id = guild.id

 
        existing_server = await self.collection.find_one({"_id": server_id})
        if existing_server is None:
           
            await self.collection.insert_one({"_id": server_id})
            

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
       
        server_id = guild.id

        
        existing_server = await self.collection.find_one({"_id": server_id})
        if existing_server is not None:
         
            await self.collection.delete_one({"_id": server_id})
            await self.betr.insert_one({"_id": server_id})

async def setup(bot: QillBot) -> None:
    await bot.add_cog(Jiken(bot))
