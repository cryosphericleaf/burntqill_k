import re 
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import urllib
from typing import List
from .utils.testpages import PageView

class Search(commands.Cog):
    """Search based commands."""
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="define", help="Provides the definition of the given word from the dictionary.")
    @app_commands.describe(word="The word to search for.")
    async def define(self, ctx: commands.Context, *, word: str) -> None:
        wait_message = await ctx.send("Please wait...")

        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.dictionaryapi.dev/api/v2/entries/en/{word}') as response:
                data = await response.json()

        if 'title' in data:
            await wait_message.edit(content=f"Word not found: {word}")
        else:
            embed = discord.Embed(title=f"📚 Definitions for '{word}'", color=0x000000)
            for i, meaning in enumerate(data[0]['meanings'], start=1):
                definition = meaning['definitions'][0]['definition']
                example = meaning['definitions'][0].get('example', 'No example available')
                part_of_speech = meaning['partOfSpeech']
                embed.add_field(name=f"{i}. {part_of_speech}", value=f"**Definition:** {definition}\n**Example:** {example}", inline=False)
            embed.set_footer(text=f"Requested by {ctx.author.name}")
            await wait_message.edit(content='', embed=embed)

    @commands.hybrid_command(name='urban', help="Looks up a term on Urban Dictionary.")
    @app_commands.describe(term="The term to search for.")
    async def urban(self, ctx: commands.Context, *, term: str) -> None:
        await ctx.defer()

        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://api.urbandictionary.com/v0/define?term={term}') as response:
                data = await response.json()

        if not data['list']:
            await ctx.send(content='No results found.')
        else:
            embeds = []
            for index, item in enumerate(data['list'], start=1):
                embed = discord.Embed(title=item['word'], description=item['definition'], color=0x000000)
                embed.add_field(name='Author', value=item['author'], inline=False)
                embed.add_field(name='Upvotes', value=item['thumbs_up'], inline=True)
                embed.add_field(name='Downvotes', value=item['thumbs_down'], inline=True)
                embed.add_field(name='Example', value=item['example'], inline=False)

                embeds.append(embed)
                embed.set_footer(text=f'Page {index}/{len(data["list"])}')

            view = PageView(ctx, embeds)
            await view.start()



async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Search(bot))
