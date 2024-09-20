import discord
from discord.ext import commands
from main import QillBot
import json
from typing import Optional
from datetime import datetime

class AutoResponder(commands.Cog):
    """Commands for AutoResponders"""
    def __init__(self, bot: QillBot):
        self.bot: QillBot = bot
        self.embed_data = {}
        
    def is_allowed(self, user):
        allowed_users = [771364000796508160]  
        return user.id in allowed_users


    async def cog_check(self, ctx):
        if not self.is_allowed(ctx.author):
            return False
        return True
    

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author == self.bot.user or not isinstance(message.content, str):
            return

        if not message.content.startswith('{') or not message.content.endswith('}'):
            return
        try:
            embed_data: dict = json.loads(message.content)
            self.embed_data[message.id] = embed_data
        except json.JSONDecodeError:
            return

        if "title" not in embed_data and "description" not in embed_data:
            print("Invalid embed data, missing title or description.")
            return

        if message.guild and message.channel.permissions_for(message.author).manage_messages:
            await message.add_reaction("🛠️")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User) -> None:
        
        if user == reaction.message.author and str(reaction.emoji) == "🛠️" and reaction.me:
            embed_data = self.embed_data.get(reaction.message.id)
            if embed_data is None:
                return

            try:
                embed: discord.Embed = discord.Embed(
                    title=embed_data.get("title", ""),
                    description=embed_data.get("description", ""),
                    url=embed_data.get("url", ""),
                    timestamp=datetime.fromisoformat(embed_data.get("timestamp", "")) if "timestamp" in embed_data else None,
                    color=embed_data.get("color", None)
                )

                for field in embed_data.get("fields", []):
                    name: Optional[str] = field.get("name", "")
                    value: Optional[str] = field.get("value", "")
                    inline: bool = field.get("inline", False)
                    embed.add_field(name=name, value=value, inline=inline)

                embed.set_author(name=embed_data.get("author_name", ""), url=embed_data.get("author_url", ""), icon_url=embed_data.get("author_icon", ""))
                embed.set_image(url=embed_data.get("image", ""))
                embed.set_thumbnail(url=embed_data.get("thumbnail", ""))
                embed.set_footer(text=embed_data.get("footer_text", ""), icon_url=embed_data.get("footer_icon", ""))
                
                await reaction.message.channel.send(embed=embed)
                await reaction.remove(self.bot.user)
            except Exception as e:
                await reaction.message.channel.send(f"```{str(e)}```")
                print(f"Error creating embed: {e}")

async def setup(bot):
    await bot.add_cog(AutoResponder(bot))


