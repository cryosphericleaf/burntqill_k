import re
import sympy
import discord
from discord.ext import commands
from main import QillBot

class Maths(commands.Cog):
    """Server utility commands"""

    def __init__(self, bot: QillBot):
        self.bot: QillBot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:

        if message.author == self.bot.user:
            return

        if message.reference is not None:

            if (await message.channel.fetch_message(message.reference.message_id)).author == self.bot.user:

                a_id: int = message.reference.message_id
                a: discord.Message = await message.channel.fetch_message(a_id)
                b: discord.Message = message
                expr: str = str(a.content) + str(b.content)
             

                try:
                    if re.match(r'^[\d+\-*/().\s]*[\+\-\*/][\d+\-*/().\s]*$', expr):
                        
                        result = sympy.sympify(expr)
                        await message.channel.send(f'{round(result, 2)}')
                    else:
                        return
                except Exception:
                    return  
            else:
                return
        else:
            if re.match(r'^[\d+\-*/().\s]*[\+\-\*/][\d+\-*/().\s]*$', message.content):
                expression: str = str(message.content)
                result = sympy.sympify(expression)
                await message.channel.send(f'{round(result, 2)}')
            else:
                return

async def setup(bot: QillBot) -> None:
    await bot.add_cog(Maths(bot))
