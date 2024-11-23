from __future__ import annotations
import asyncio 

import json
import re 
import math
import discord
import datetime
from discord import Webhook
from discord.ext import commands
from discord.ext.commands import Context
import aiohttp
from typing import List
from discord import app_commands
from typing import Optional
from discord.errors import Forbidden
from .utilities.testpages import PageView

from main import QillBot
from config import GOOGLE_KEY as GconsoleKey

class ServerUtils(commands.Cog):
    """Server utility commands"""

    def __init__(self, bot: QillBot):
        self.bot: QillBot = bot
        self.collection = self.bot.db['triggers']
       
    #TOSSIC
    async def add_monitoring_ch(self, guild_id, channel_id, log_channel_id):
        query = """
            INSERT INTO perspective (ch_id, server_id, log_ch_id) VALUES (?, ?, ?);
        """
        async with self.bot.conn.cursor() as cursor:
            await cursor.execute(query, (channel_id, guild_id, log_channel_id))
            await self.bot.conn.commit()

    async def remove_monitoring_ch(self, guild_id, channel_id):
        select_query = """
            SELECT ch_id FROM perspective WHERE ch_id = ? AND server_id = ?;
        """
        delete_query = """
            DELETE FROM perspective WHERE ch_id = ? AND server_id = ?;
        """
        async with self.bot.conn.cursor() as cursor:
            await cursor.execute(select_query, (channel_id, guild_id))
            existing_row = await cursor.fetchone()

            if existing_row:
                await cursor.execute(delete_query, (channel_id, guild_id))
                await self.bot.conn.commit()
                return True
            else:
                return False

    async def get_enabled_persp_ch(self, guild_id):
        query = """
            SELECT ch_id FROM perspective WHERE server_id = ?;
        """
        async with self.bot.conn.cursor() as cursor:
            await cursor.execute(query, (guild_id,))
            return await cursor.fetchall()


    @commands.hybrid_group(name="toxicitymonitor", invoke_without_command=True,
                            description="Manage toxicity monitoring.",
                            help="Manage toxicity monitoring, `This is AI so users can find ways around it.`")
    @app_commands.guild_only()
    async def toxicitymonitor(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @toxicitymonitor.command(name="enable", description="Enables toxicity monitoring in the specified text channel.", help="Enables toxicity monitoring in the specified text channel.")
    @app_commands.describe(channel="The text channel where toxicity monitoring will be enabled.", log_channel="The text channel where toxicity logs will be sent.")
    @commands.has_permissions(manage_channels=True)
    async def enable(self, ctx: Context, channel: discord.TextChannel, log_channel: discord.TextChannel):
        try:
            guild_id = ctx.guild.id
            channel_id = channel.id
            log_channel_id = log_channel.id
            await self.add_monitoring_ch(guild_id, channel_id, log_channel_id)
            await ctx.send(f"Toxicity monitor has been enabled in {channel.mention}.\n Logs will be sent to {log_channel.mention}.")

        except commands.BadArgument:
            await ctx.send("Invalid channel provided. Please mention valid text channel.")
        except commands.MissingPermissions:
            await ctx.send("You don't have the required permission (manage channels).")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @toxicitymonitor.command(name="disable", description="Disables toxicity monitoring in the specified text channel.", help="Disables toxicity monitoring in the specified text channel.")
    @app_commands.describe(channel="The text channel where toxicity monitoring will be disabled.")
    @commands.has_permissions(manage_channels=True)
    async def disable(self, ctx: Context, channel: discord.TextChannel):
        try:
            guild_id = ctx.guild.id
            channel_id = channel.id
            removed = await self.remove_monitoring_ch(guild_id, channel_id)

            if removed:
                await ctx.send(f"Toxicity monitor has been disabled in {channel.mention}.")
            else:
                await ctx.send(f"Toxicity monitor is not enabled in {channel.mention}.")

        except commands.BadArgument:
            await ctx.send("Invalid channel provided. Please mention a valid text channel.")
        except commands.MissingPermissions:
            await ctx.send("You don't have the required permissions (manage channels).")

    @toxicitymonitor.command(name="list", description="List the channels where toxicity monitoring is enabled.", help="List the channels where toxicity monitoring is enabled.")
    async def list_toxicity_monitor_channels_command(self, ctx: Context):
        try:
            await ctx.defer()

            server_id = ctx.guild.id

            enabled_channels = await self.get_enabled_persp_ch(server_id)
            if not enabled_channels:
                await ctx.send("Toxicity monitor is not enabled in any of the channels in this server.")
                return

            message = "Toxicity monitor is enabled in the following channels:\n"
            for record in enabled_channels:
                message += f"<#{record[0]}>\n"

            embed = discord.Embed(
                title="Enabled Channels",
                description=message,
                color=discord.Colour(0xffebf8)
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f'An error occurred while processing the command. \n {str(e)}')

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        try:
            if message.author == self.bot.user or not message.content:
                return

            channel_id = message.channel.id

            is_enabled = await self.is_toxicity_monitor_enabled(channel_id)
            if not is_enabled:
                return

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url='https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze',
                    json={
                        'comment': {'text': message.content},
                        'languages': ['en'],
                        'requestedAttributes': {'TOXICITY': {}}
                    },
                    params={'key': f'{GconsoleKey}'}
                ) as response:
                    data = await response.json()
                    if 'attributeScores' in data:
                        toxicity = data['attributeScores']['TOXICITY']['summaryScore']['value']
                        if toxicity > 0.90:
                            await self.handle_toxic_message(message, channel_id)
                    else:
                        print(f"'attributeScores' not found in API response: {data}")

        except Forbidden:
            await message.channel.send("Missing access to the log channel.")

    async def handle_toxic_message(self, message: discord.Message, channel_id: discord.TextChannel):
        await message.delete()
        await message.channel.send(
            f"{message.author.mention}, your message was flagged as toxic and has been deleted.",
            delete_after=10
        )
        time_period = datetime.timedelta(seconds=20)
        try:
            await message.author.timeout(time_period)
        except discord.Forbidden:
            await message.channel.send("Not able to timeout because I'm lower in role hierarchy")
        log_channel_id = await self.get_log_channel(channel_id)
        embed = discord.Embed(
            title="Message Deleted",
            description=f"A message from {message.author.mention} was deleted due to high toxicity.\nThe content of the message was: `{message.content}`",
            color=discord.Colour(0xffebf8)
        )
        await self.send_to_log_ch(embed, log_channel_id)

    async def send_to_log_ch(self, embed: discord.Embed, channel_id: int):
        log_channel = self.bot.get_channel(channel_id)
        await log_channel.send(embed=embed)

    async def is_toxicity_monitor_enabled(self, channel_id) -> bool:
        query = """
            SELECT EXISTS(SELECT 1 FROM perspective WHERE ch_id = ?);
        """
        async with self.bot.conn.cursor() as cursor:
            await cursor.execute(query, (channel_id,))
            result = await cursor.fetchone()
            return result[0] == 1

    async def get_log_channel(self, channel_id):
        query = """
            SELECT log_ch_id FROM perspective WHERE ch_id = ?;
        """
        async with self.bot.conn.cursor() as cursor:
            await cursor.execute(query, (channel_id,))
            row = await cursor.fetchone()
            return row['log_ch_id']


    @commands.hybrid_command(name='lock', description='Locks the channel.', help='Locks the channel.')
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @app_commands.describe(channel='The channel to lock.')
    async def lock(self, ctx: Context, channel: Optional[discord.TextChannel] = None):

        channel = channel or ctx.channel

        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.update(send_messages=False)
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

        bot_overwrite = channel.overwrites_for(ctx.guild.me)
        bot_overwrite.update(send_messages=True)
        await channel.set_permissions(ctx.guild.me, overwrite=bot_overwrite)

        await ctx.send(f'Locked. （￣︶￣）↗　')
        

    @commands.hybrid_command(name='unlock', description='Unlocks the channel.', help='Unlocks the channel.')
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @app_commands.describe(channel='The channel to unlock.')
    async def unlock(self, ctx: Context, channel: Optional[discord.TextChannel] = None):

        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.update(send_messages=True)

        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

        await ctx.send(f'Unlocked :>')

    @commands.hybrid_group(name="emoji", description="Manage emojies", help = 'Manage emojies')
    @commands.has_permissions(manage_emojis=True)
    @commands.cooldown(1, 2, commands.BucketType.user)
    @app_commands.guild_only()
    async def emoji(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @emoji.command(name = 'add', description="Add an emoji to the server", help = "Add an emoji to the server")
    @app_commands.describe(name="The name of the emoji", url="The URL of the emoji", attachment="The attachment of the emoji")
    async def emoji_add(self, ctx: Context, name: str, url: Optional[str] = None, attachment: Optional[discord.Attachment] = None):
        try:
            await ctx.defer()
            if not url and not attachment and len(ctx.message.attachments) == 1:
                attachment = ctx.message.attachments[0]
            if not url and attachment:
                url = attachment.url
            if not url:
                await ctx.send("Please provide an emoji URL or attachment.")
                return

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    image = await response.read()

            if len(image) > 256000: 
                await ctx.send("The attachment size is too large. Please provide an image smaller than 256 KB.")
                return

            _emoji = await ctx.guild.create_custom_emoji(name=name, image=image)
            await ctx.send(f"{_emoji} done!")
        except Exception as e:
            await ctx.send(str(e))
            print(e)

    @emoji.command(name = 'remove', description="Remove an emoji from the server", help = "Remove an emoji from the server")
    @app_commands.describe(name="The name of the emoji", emoji="The emoji to remove")
    async def emoji_remove(self, ctx: Context, emoji: Optional[str] = None, name: Optional[str] = None):
        if not emoji and name:
            emoji = name
        if not emoji:
            await ctx.send("Please provide an emoji name or a unicode emoji.")
            return

        if emoji.startswith("<:") and emoji.endswith(">"):
            emoji = emoji.strip("<:>").split(":")[0]

        _emoji = discord.utils.get(ctx.guild.emojis, name=emoji)
        if not _emoji:
            await ctx.send("Could not find the specified emoji.")
            return

        await _emoji.delete()
        await ctx.send(f"removed :<")


    @emoji.command(name='link', description="Get the URL of an emoji", help="Get the URL of an emoji")
    @app_commands.describe(emoji="The emoji to get the URL of")
    async def emoji_link(self, ctx: Context, emoji: str):
    
        if emoji.startswith("<:") and emoji.endswith(">"):
            emoji_name = emoji.strip("<:>").split(":")[0]
            for e in ctx.guild.emojis:
                if e.name == emoji_name:
                    await ctx.send(e.url)
                    return
        else:
            await ctx.send("Emoji not found.")

    #logging
            
    async def get_av_bytes(self) -> bytes:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.bot.user.display_avatar.url) as resp:
                avatar_bytes = await resp.read()
                return avatar_bytes

            
    async def get_or_create_webhook(self, log_channel: discord.TextChannel) -> str:
        webhooks = await log_channel.webhooks()
        webhook: discord.Webhook | None  = discord.utils.get(webhooks, name="petal logger")
        if webhook is None:
            avatar_bytes = await self.get_av_bytes()
            webhook = await log_channel.create_webhook(name="petal logger", avatar=avatar_bytes) 
        return webhook.url


    async def send_to_log_channel(self, server_id: int, embed: discord.Embed) -> None:
        log_ch_id = await self.get_log_channel_id(server_id)
        log_ch = self.bot.get_channel(log_ch_id)
        webhook_url = await self.get_or_create_webhook(log_ch)
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(webhook_url, session=session)
            await webhook.send(embed=embed)

    async def get_log_channel_id(self, server_id: int) -> Optional[int]:
        query = "SELECT log_channel FROM message_log WHERE server_id = ?"
        async with self.bot.conn.cursor() as cursor:
            await cursor.execute(query, (server_id,))
            row = await cursor.fetchone()
            return row[0] if row else None

    @commands.hybrid_group(name="logger", description="Manage logging.", help="Manage logging.")
    @app_commands.guild_only()
    async def logger(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @logger.command(name="enable", description="Enables message logging.", help="Enables message logging.")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(log_channel="The text channel where logs will be sent.")
    async def enable_logger(self, ctx: commands.Context, log_channel: discord.TextChannel) -> None:
        try:
            query = "SELECT * FROM message_log WHERE server_id = ?"
            async with self.bot.conn.cursor() as cursor:
                await cursor.execute(query, (ctx.guild.id,))
                result = await cursor.fetchone()

                if result:
                    await ctx.send("Logging is already enabled for this server.")
                else:
                    query = "INSERT INTO message_log (server_id, log_channel) VALUES (?, ?)"
                    await cursor.execute(query, (ctx.guild.id, log_channel.id))
                    await self.bot.conn.commit()
                    await ctx.send(f"This server is now configured for message logging in {log_channel.mention}.")
                    avatar_bytes = await self.get_av_bytes()
                    await log_channel.create_webhook(name="petal logger", avatar=avatar_bytes)
        except PermissionError:
            await ctx.send('You need administrator permissions to use this command.')

    @logger.command(name='disable', description='Disable message logging', help='Disable message logging')
    @commands.has_permissions(administrator=True)
    async def disable_logger(self, ctx: commands.Context) -> None:
        try:
            query = "SELECT * FROM message_log WHERE server_id = ?"
            async with self.bot.conn.cursor() as cursor:
                await cursor.execute(query, (ctx.guild.id))
                result = await cursor.fetchone()

                if not result:
                    await ctx.send("Logging is not enabled for this server.")
                else:
                    query = "DELETE FROM message_log WHERE server_id = ?"
                    await cursor.execute(query, (ctx.guild.id,))
                    await self.bot.conn.commit()
                    await ctx.send("Disabled message logging for this server.")
        except PermissionError:
            await ctx.send('You need administrator permissions to use this command.')

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        if message.guild and not message.author.bot:
            log_ch_id = await self.get_log_channel_id(message.guild.id)
            if log_ch_id:  
                embed = discord.Embed(
                    description=f"**Message deleted**\nContent: {message.content}\nChannel: {message.channel.mention}",
                    color=discord.Colour(0xffebf8)
                )
                embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar)
                embed.set_footer(text=f"Message ID: {message.id} | Author ID: {message.author.id} | Time: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
                await self.send_to_log_channel(message.guild.id, embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        if before.guild and before.content != after.content and not before.author.bot:
            log_ch_id = await self.get_log_channel_id(before.guild.id)
            if log_ch_id:
                embed = discord.Embed(
                description=f"**[Message](<{after.jump_url}>) edited**\nBefore: {before.content}\nAfter: {after.content}",
                color=discord.Colour(0xffebf8)
                )
                
                embed.set_author(name=before.author.display_name, icon_url=before.author.display_avatar)
                embed.set_footer(text=f"Message ID: {before.id} | Author ID: {before.author.id} | Time: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
                await self.send_to_log_channel(before.guild.id, embed)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: List[discord.Message]) -> None:
        if messages:
            message = messages[0]
            if message.guild:
                log_ch_id = await self.get_log_channel_id(message.guild.id)
                if log_ch_id:
                    embeds = []
                    embed = discord.Embed(
                        title="Messages Deleted",
                        description="",
                        color=discord.Colour(0xffebf8)
                    )
                    for msg in messages:
                        if not msg.author.bot:
                            line = f"**{msg.author.display_name}**: {msg.content}\n"
                            if len(embed.description) + len(line) > 2048:
                                embeds.append(embed)
                                embed = discord.Embed(
                                    title="Messages Deleted (cont.)",
                                    description="",
                                    color=discord.Colour(0xffebf8)
                                )
                            embed.description += line
                    embeds.append(embed)

                    for embed in embeds:
                        embed.set_footer(text=f"Messages: {len(messages)} | Time: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
                        await self.send_to_log_channel(message.guild.id, embed)

    #triggers 
                        
    @commands.hybrid_group(name = 'trigger', description = 'Manage triggers', help = 'Manage triggers')  
    @app_commands.guild_only()   
    async def trigger(self, ctx: Context):
        if ctx.invoked_subcommand is None:  
            await ctx.send_help(ctx.command)    

    @trigger.command(name="add", description="Add a trigger", help="Add a trigger")
    @commands.has_permissions(manage_messages = True)
    async def add_trigger(self, ctx: Context):
        try: 
            view = Tsetup(ctx, self.bot)
            await view.start()
        except commands.MissingPermissions:
            await ctx.send("You don't have manage messages permission to use this command.")

    @trigger.command(name="remove", description='Deletes the trigger.', help = 'Deletes the trigger.')
    @commands.has_permissions(manage_messages = True)
    @app_commands.describe(trigger='The trigger to delete')
    async def delete(self, ctx, trigger: str):
        await ctx.defer()
        server_id = str(ctx.guild.id)

        trigger_doc = await self.collection.find_one({"server_id": server_id, "trigger": trigger.lower()})

        if trigger_doc:
            await self.collection.delete_one({"_id": trigger_doc["_id"]})
            await ctx.send(f"Trigger `{trigger}` deleted successfully.")
        else:
            await ctx.send(f"Trigger `{trigger}` not found.")

    @trigger.command(name="remove_all", description='Deletes all triggers from the server.', help = 'Deletes all triggers in the server.')
    @commands.has_permissions(manage_guild = True)
    async def remove_all(self, ctx):
        await ctx.defer()
        server_id = str(ctx.guild.id)

        confirm_message = await ctx.send("Are you sure you want to delete all triggers? (y/n)")
        def check(m):
            return m.author == ctx.author and m.content.lower() in ['y', 'n']
        try:
            msg = await self.bot.wait_for('message', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await confirm_message.edit(content='operation has been cancelled.')
        else:
            if msg.content.lower() == 'y':

                result = await self.collection.delete_many({"server_id": server_id})

                if result.deleted_count > 0:
                    await ctx.send(f"All triggers have been successfully deleted.")
                else:
                    await ctx.send(f"No triggers found for this server.")
            else:
                await ctx.send("Deletion cancelled.")



    @trigger.command(name="list", description='Displays the list of triggers.', help = 'Displays the list of triggers in the server.')
    async def list(self, ctx: Context):
        await ctx.defer()
        server_id = str(ctx.guild.id)

        triggers = self.collection.find({"server_id": server_id})

        trigger_list = []
        async for trigger_doc in triggers:
            trigger_list.append(f"{trigger_doc['trigger']} ({trigger_doc['f_type']})")

        total_triggers = len(trigger_list)
        if trigger_list:
            embeds = []
            for i in range(0, total_triggers, 15):
                description = "\n".join(f"{j+1+i}. {trigger}" for j, trigger in enumerate(trigger_list[i:i + 15]))
                embed = discord.Embed(title=f"Triggers (Total: {total_triggers})", description=description, color=discord.Colour(0xffebf8))
                embed.set_footer(text=f"Page {i//15 + 1}/{math.ceil(total_triggers/15)}")
                embeds.append(embed)

            view = PageView(ctx, embeds)
            await view.start()

        else:
            await ctx.send("No triggers found.")

    @trigger.command(name="search", description='Searches for similar triggers.', help = 'Searches for similar triggers in the server.')
    @app_commands.describe(search_term='The trigger to search for')
    async def search(self, ctx, search_term: str):
        await ctx.defer()
        server_id = str(ctx.guild.id)
        
        pattern = re.compile(search_term, re.IGNORECASE)

        triggers = self.collection.find({"server_id": server_id, "trigger": pattern})

        trigger_list = []
        async for trigger_doc in triggers:
            trigger_list.append(f"{trigger_doc['trigger']} ({trigger_doc['f_type']})")

        total_triggers = len(trigger_list)
        if trigger_list:
            embeds = []
            for i in range(0, total_triggers, 15):
                description = "\n".join(f"{j+1+i}. {trigger}" for j, trigger in enumerate(trigger_list[i:i + 15]))
                embed = discord.Embed(title=f"Similar Triggers (Total: {total_triggers})", description=description, color=discord.Colour(0xffebf8))
                embed.set_footer(text=f"Page {i//15 + 1}/{math.ceil(total_triggers/15)}")
                embeds.append(embed)

            view = PageView(ctx, embeds)
            await view.start()
        else:
            await ctx.send("No similar triggers found.")


    

    

async def setup(bot: QillBot):
    await bot.add_cog(ServerUtils(bot))

class Tinfo(discord.ui.Modal, title='Trigger'):
    """Manage triggers"""
    def __init__(self, interaction: discord.Interaction, message: discord.Message):
        super().__init__()
    
        self.interaction = interaction
        self.message = message
        self.trigger = None
        self.response = None

    trigger_input = discord.ui.TextInput(
        label='Trigger',
        placeholder='Enter your trigger...',
        required=True,
        max_length=100,
    
    )

    response_input = discord.ui.TextInput(
        label='Response',
        style=discord.TextStyle.long,
        placeholder='Response of the trigger.',
        required=True,
        max_length=1500,
    )

    async def on_submit(self, interaction: discord.Interaction):
        self.trigger = self.trigger_input.value
        self.response = self.response_input.value
        await interaction.response.defer()

class TSelectMenu(discord.ui.Select['Tsetup']):
    def __init__(self):
     
        options = [
            discord.SelectOption(label='startswith', description='If the message startswith the trigger.'),
            discord.SelectOption(label='endswith', description='If the message endswith the trigger.'),
            discord.SelectOption(label='contains', description='If the message contains the trigger.'),
            discord.SelectOption(label='strict', description='If the message is equals to the trigger[default]'),
        ]
        super().__init__(placeholder='filter type', min_values=1, max_values=1, options=options)
    async def callback(self, interaction: discord.Interaction):
        
        self.view.filter_type = self.values[0] if self.values else 'strict'
        await self.view.update_embed(interaction)
      


class Tsetup(discord.ui.View):
    def __init__(self, ctx: commands.Context, bot: QillBot):
        super().__init__(timeout=300)
        self.bot = bot 
        self.collection = self.bot.db['triggers']
        self.ctx = ctx
        self.add_item(TSelectMenu())
        self.trigger: str = None  
        self.response: str = None
        self.filter_type: str = 'strict'  
        self.message: discord.Message | None

    async def update_embed(self, interaction: discord.Interaction):
        
        embed = discord.Embed(title='Trigger Setup', description='Enter your trigger details.', color=discord.Colour(0xffebf8))
        embed.add_field(name='Trigger', value=self.trigger or 'Not set', inline=False)
        embed.add_field(name='Response', value=self.response or 'Not set', inline=False)
        embed.add_field(name='Filter Type', value=self.filter_type or 'strict', inline=False)

        await interaction.message.edit(embed=embed, view=self)

    async def endembed(self, interaction: discord.Interaction):
        embed = discord.Embed(title=f'Trigger {self.trigger} added!', color=discord.Colour(0xffebf8))
        await interaction.message.edit(embed=embed, view=self)
        
      


    @discord.ui.button(label='Add', style=discord.ButtonStyle.green, custom_id='trinfo')
    async def trinfo(self, interaction: discord.Interaction, button: discord.ui.Button):
        tinfo_modal = Tinfo(interaction, interaction.message)
        await interaction.response.send_modal(tinfo_modal)

        await tinfo_modal.wait()

        self.trigger = tinfo_modal.trigger
        self.response = tinfo_modal.response
    

        self.children[1].disabled = False  
        await self.update_embed(interaction)
    
    async def start(self):
        embed = discord.Embed(title='Trigger Setup', description='Enter your trigger details.', color=discord.Colour(0xffebf8))
        embed.add_field(name='Trigger', value=self.trigger or 'Not set', inline=False)
        embed.add_field(name='Response', value=self.response or 'Not set', inline=False)
        embed.add_field(name='Filter Type', value=self.filter_type or 'strict', inline=False)
        
        self.message = await self.ctx.send(embed=embed, view=self)
        

    @discord.ui.button(label='confirm', style=discord.ButtonStyle.green, disabled=True)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        
        data = {
            'trigger': self.trigger.lower(),
            'f_type': self.filter_type,
            'resp': self.response
        }
        trigger_d = await self.collection.find_one({"server_id": str(interaction.guild.id), "trigger": self.trigger.lower()})

        if trigger_d:
            await interaction.followup.send(f"Trigger '{self.trigger}' already exists. ¯\_(ツ)_/¯", ephemeral=True)
            return

        trigger_count = await self.collection.count_documents({"server_id": str(interaction.guild.id)})
        if trigger_count >= 1000:
            await interaction.followup.send("You have reached the maximum limit of 1000 triggers per server.", ephemeral=True)
            return

        data["server_id"] = str(interaction.guild.id)

        await self.collection.insert_one(data)
        self.children[1].disabled = True
        await self.endembed(interaction)

    @discord.ui.button(label='cancel', style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.delete_original_response()
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You cannot use this button :(", ephemeral=True)
            return False
        else:
            if interaction.data['custom_id'] != 'trinfo':  
                await interaction.response.defer(ephemeral=True)
            return True
        
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)
