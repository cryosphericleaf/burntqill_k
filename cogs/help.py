from __future__ import annotations

import discord
import contextlib
from discord.ext import commands, menus
from discord.ext.commands import Context
import itertools
from typing import Optional, List, TYPE_CHECKING, Any, Union
from discord.ext import commands, menus
from .utilities.pages import RoboPages, ButtonPaginator
import discord
from datetime import datetime 
import inspect
import itertools

if TYPE_CHECKING:
    from main import QillBot



import discord
import inspect
from discord.ext import commands, menus


class GroupHelpPageSource(menus.ListPageSource):
    def __init__(self, group: Union[commands.Group, commands.Cog], entries: list[commands.Command], *, prefix: str):
        super().__init__(entries=entries, per_page=6)
        self.group: Union[commands.Group, commands.Cog] = group
        self.prefix: str = prefix
        self.title: str = f'{self.group.qualified_name} Commands'
        self.description: str = self.group.description

    async def format_page(self, menu: RoboPages, commands: list[commands.Command]):
        embed = discord.Embed(title=self.title, description=self.description, colour=discord.Colour(0xffebf8))

        for command in commands:
            signature = f'{command.qualified_name} {command.signature}'
            embed.add_field(name=signature, value=command.short_doc or 'No help given...', inline=False)

        maximum = self.get_max_pages()
        if maximum > 1:
            embed.set_author(name=f'Page {menu.current_page + 1}/{maximum} ({len(self.entries)} commands)')

        embed.set_footer(text=f'Use "{self.prefix}help command" for more info on a command.')
        return embed

emojies: dict = {
    "Basic": '<:eee:1202188184809906207>',
    "Misc": '<:misccc:1202157483368386561>',
    "Search": '<:qsearch:1202143393845886996>',
    "ServerUtils": '<:utils:1202190964748193882>',
    "Time": '<:qtime:1202163673171513364>',
    "Images": '<:glitchh:1202204404267098154>'
}

class HelpSelectMenu(discord.ui.Select['HelpMenu']):
    def __init__(self, entries: dict[commands.Cog, list[commands.Command]], bot: QillBot):
        super().__init__(
            placeholder='Select a category...',
            min_values=1,
            max_values=1,
            row=0,
        )
        self.commands: dict[commands.Cog, list[commands.Command]] = entries
        self.bot: QillBot = bot
        self.__fill_options()

    def __fill_options(self) -> None:
        self.add_option(
            label='Index',
            emoji='<:qq:1202185279897874462>',
            value='__index',
            description='The help page showing how to use the bot.',
        )
        for cog, commands in self.commands.items():
            if not commands:
                continue
            description = cog.description.split('\n', 1)[0] or None
            emoji: str = emojies.get(cog.qualified_name, None)
            self.add_option(emoji=emoji ,label=cog.qualified_name, value=cog.qualified_name, description=description)

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        value = self.values[0]
        if value == '__index':
            await self.view.rebind(FrontPageSource(), interaction)
        else:
            cog = self.bot.get_cog(value)
            if cog is None:
                await interaction.response.send_message('Somehow this category does not exist?', ephemeral=True)
                return

            commands = self.commands[cog]
            if not commands:
                await interaction.response.send_message('This category has no commands for you', ephemeral=True)
                return

            source = GroupHelpPageSource(cog, commands, prefix=self.view.ctx.clean_prefix)
            await self.view.rebind(source, interaction)


class FrontPageSource(menus.PageSource):
    def is_paginating(self) -> bool:
        # This forces the buttons to appear even in the front page
        return True

    def get_max_pages(self) -> Optional[int]:
        # There's only one actual page in the front page
        # However we need at least 2 to show all the buttons
        return 2

    async def get_page(self, page_number: int) -> Any:
        # The front page is a dummy
        self.index = page_number
        return self

    def format_page(self, menu: HelpMenu, page: Any):
        
        embed = discord.Embed(title='Help <:eee:1202188184809906207>', colour=discord.Colour(0xffebf8))
        embed.description = inspect.cleandoc(
            f"""
            Hello :O

            > - Use `{menu.ctx.clean_prefix}help command` for more info on a command.
            > - Use `{menu.ctx.clean_prefix}help category` for more info on a category.
            > - Use the dropdown menu below to select a category.
            > - Use `/feedback` to give feedback to me.
        """
        )
        

       

        # created_at = Tc.format_dt(menu.ctx.bot.user.created_at, 'F')
        if self.index == 0:
            embed.add_field(
                name="What's up?",
                value=(
                "This is the part that I'll change frequently.\n"
                "Currently i have message logger, toxicity monitor, triggers and few other basic bot commands\n"
                "See next page for syntax help."
                ),
                inline=False,
            )
        elif self.index == 1:
            entries = (
                ('<argument>', 'This means the argument is __**required**__.'),
                ('[argument]', 'This means the argument is __**optional**__.'),
                ('[A|B]', 'This means that it can be __**either A or B**__.'),
                (
                    '[argument...]',
                    'This means you can have multiple arguments.\n'
                    'Now that you know the basics, it should be noted that...\n'
                    '__**You do not type in the brackets!**__',
                ),
            )

            

            for name, value in entries:
                embed.add_field(name=name, value=value, inline=False)

        return embed


class HelpEmbed(discord.Embed):
    def __init__(self, **kwargs: any) -> None:
        super().__init__(**kwargs)
        self.timestamp: datetime = datetime.utcnow()
        text: str = "Use help [command] or help [category] for more information | <> is required | [] is optional"
        self.set_footer(text=text)
        self.color: discord.Colour = discord.Colour(0xffebf8)
        
        
    
        
        

class HelpMenu(RoboPages):
    def __init__(self, source: menus.PageSource, ctx: Context):
        super().__init__(source, ctx=ctx, compact=True)

    def add_categories(self, commands: dict[commands.Cog, list[commands.Command]]) -> None:
        self.clear_items()
        self.add_item(HelpSelectMenu(commands, self.ctx.bot))
        self.fill_items()

    async def rebind(self, source: menus.PageSource, interaction: discord.Interaction) -> None:
        self.source = source
        self.current_page = 0

        await self.source._prepare_once()
        page = await self.source.get_page(0)
        kwargs = await self._get_kwargs_from_page(page)
        self._update_labels(0)
        await interaction.response.edit_message(**kwargs, view=self)

class MyHelp(commands.HelpCommand):
    def __init__(self) -> None:
        super().__init__(
            command_attrs={
                "help": "The help command for the bot",
                "cooldown": commands.CooldownMapping.from_cooldown(1, 3.0, commands.BucketType.user),
                "aliases": ['commands']
            }
        )

    async def send(self, **kwargs: Any) -> None:
        
        await self.get_destination().send(**kwargs)
        

    async def send_bot_help(self, mapping):
        try:
            bot = self.context.bot

            def key(command) -> str:
                cog = command.cog
                return cog.qualified_name if cog else '\U0010ffff'

            entries: list[commands.Command] = await self.filter_commands(bot.commands, sort=True, key=key)

            all_commands: dict[commands.Cog, list[commands.Command]] = {}
            for name, children in itertools.groupby(entries, key=key):
                if name == '\U0010ffff':
                    continue

                cog = bot.get_cog(name)
                assert cog is not None
                all_commands[cog] = sorted(children, key=lambda c: c.qualified_name)

            menu = HelpMenu(FrontPageSource(), ctx=self.context)
            menu.add_categories(all_commands)
            await menu.start()
        except Exception as e:
            print(e)



    async def send_command_help(self, command: commands.Command) -> None:
        try:
            signature: str = self.get_command_signature(command)
            embed: HelpEmbed = HelpEmbed(title=signature, description=command.help or "No help found...")

            if cog := command.cog:
                embed.add_field(name="Category", value=cog.qualified_name, inline=False)

            can_run: str = "No"
            with contextlib.suppress(commands.CommandError):
                if await command.can_run(self.context):
                    can_run = "Yes"

            embed.add_field(name="Usable", value=can_run)

            if command._buckets and (cooldown := command._buckets._cooldown):
                embed.add_field(
                    name="Cooldown",
                    value=f"{cooldown.rate} per {cooldown.per:.0f} seconds",
                )

            await self.send(embed=embed)
        except Exception as e:
            print(f"Error in MyHelp.send_command_help: {e}")

    async def send_help_embed(self, title: str, description: Optional[str], commands: List[commands.Command]) -> None:
        ctx: commands.Context = self.context
        if filtered_commands := await self.filter_commands(commands):
            if len(filtered_commands) > 8:
                try:
                    embeds: List[HelpEmbed] = []
                    embed: HelpEmbed = HelpEmbed(title=title, description=description or "No help found...")
                    for i, command in enumerate(filtered_commands):
                        if i != 0 and i % 8 == 0:
                            embeds.append(embed)
                            embed = HelpEmbed(title=title, description=description or "No help found...")
                        embed.add_field(inline = False, name=self.get_command_signature(command), value=command.help or "No help found...")
                    embeds.append(embed)

                    paginator: ButtonPaginator = ButtonPaginator(embeds)
                    await paginator.start(ctx)
                except Exception as e:
                    print(e)
            else:
                embed: HelpEmbed = HelpEmbed(title=title, description=description or "No help found...")
                for command in filtered_commands:
                    embed.add_field(inline = False, name=self.get_command_signature(command), value=command.help or "No help found...")
                await self.send(embed=embed)

    async def send_group_help(self, group: commands.Group) -> None:
    
            title: str = self.get_command_signature(group)
            await self.send_help_embed(title, group.help, group.commands)
        

    async def send_cog_help(self, cog: commands.Cog) -> None:

            title: str = cog.qualified_name or "No"
            await self.send_help_embed(f'{title} Category', cog.description, cog.get_commands())

