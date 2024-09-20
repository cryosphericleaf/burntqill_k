import discord
from typing import Optional
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands
from main import QillBot

class Feedback(discord.ui.Modal, title='Feedback'):
    
    def __init__(self, interaction: discord.Interaction):
        super().__init__()
        self.interaction = interaction


    expn = discord.ui.TextInput(
        label='Feedback',
        style=discord.TextStyle.long,
        placeholder='...',
        required=True,
        max_length=4000,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'Thanks for your feedback!', ephemeral=True)
       
        expn = self.expn.value

        f_channel: discord.TextChannel = self.interaction.client.get_channel(1132118143020585000)

        if f_channel:
            await f_channel.send(f"from: {interaction.user.mention}\n\n{expn}")
        else:
            print('where tf is f_ch??????????????????????????????????')
            

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message('Something went wrong...', ephemeral=True)
        print(error)

class Avban(discord.ui.View):

    def __init__(self, ctx: commands.Context, user: discord.User):
        super().__init__(timeout=180)
        
        self.ctx: commands.Context = ctx
        self._user: discord.User = user
        self.cmd_name = ctx.command.name 
        self.avban.label = "Banner" if self.cmd_name == "avatar" else "Avatar"
        
    @discord.ui.button(label="Any", style=discord.ButtonStyle.grey)
    async def avban(self, interaction: discord.Interaction, button: discord.ui.Button):
        try: 
            if self.cmd_name == "avatar":
                if self._user.banner:
                    await interaction.response.send_message(content=self._user.banner.url)
                else:
                    await interaction.response.send_message("This user doesn't have a banner.", ephemeral=True)
            else:
                if self._user.display_avatar:
                    await interaction.response.send_message(content=self._user.display_avatar.url)
                else:
                    await interaction.response.send_message("This user doesn't have an avatar", ephemeral=True)
        finally:
            await interaction.followup.edit_message(message_id=interaction.message.id, view=None )
            self.stop()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and interaction.user.id == self.ctx.author.id:
            return True
        await interaction.response.send_message('This button cannot be controlled by you.', ephemeral=True)
        return False

    async def on_timeout(self):
        self.stop()

class Basic(commands.Cog):
    """Basic commands that every bot have."""
    def __init__(self, bot: QillBot) -> None:
        self.bot = bot
        

    @app_commands.command(name="feedback", description="Send feedback to me!")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def feedback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(Feedback(interaction))


    @commands.hybrid_command(name='userinfo', aliases=['info','about','user'], description = 'Get server info about the user.', help = 'Get server info about the user.')
    async def userinfo(self, ctx, member: Optional[discord.Member] = None):
        if not member:
            member = ctx.message.author  

        roles = [role for role in member.roles]
    
        embed = discord.Embed(colour=discord.Colour.dark_theme(), timestamp=ctx.message.created_at)

        embed.set_author(name=f"{member}", icon_url=member.display_avatar.url)
        embed.add_field(name="ID", value=member.id, inline=False)
        embed.add_field(name="Guild name", value=member.display_name, inline=False)

        embed.add_field(name="Created at", value=f"<t:{int(member.created_at.timestamp())}:F>", inline=False)
        embed.add_field(name="Joined at", value=f"<t:{int(member.joined_at.timestamp())}:F>", inline=False)

        embed.add_field(name=f"Roles ({len(roles)})", value=", ".join([role.name for role in roles]), inline=False)
        embed.add_field(name="Top role", value=member.top_role.name, inline=False)
      


        await ctx.send(embed=embed)

    @commands.hybrid_command(name="avatar", aliases=["av"], description="Displays the user avatar.", help="Displays the user avatar.")
    @app_commands.describe(user="The user whose avatar you want to display.")
    async def avatar(self, ctx: commands.Context, user: discord.User = None):
        
        if user is None:
            user = ctx.author

        view = Avban(ctx, user)
        if user.display_avatar:
            await ctx.send(content=user.display_avatar.url, view=view)
        else:
            await ctx.send("This user doesn't have an avatar.")
    
    @commands.hybrid_command(name="banner", aliases=["bnr"], description="Displays the user banner.", help="Displays the user banner.")
    @app_commands.describe(user="The user whose banner you want to display.")
    async def banner(self, ctx: commands.Context, user: discord.User = None):
        
        if user is None:
            user = ctx.author

        view = Avban(ctx, user)
        if user.banner:
            await ctx.send(content=user.banner.url, view=view)
        else:
            await ctx.send("This user doesn't have an banner.")


    @commands.hybrid_command(name="purge", description="Purge messages", help="Purge messages")
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(
        limit="The number of messages to delete.",
        user="The user to delete messages from.",
        attachments="Only delete messages with attachments",
        links="Only delete messages with links",
    )
    async def purge(
        self, ctx: Context, limit: int, user: Optional[discord.Member] = None, attachments: Optional[bool] = False,
        links: Optional[bool] = False
    ):
        await ctx.defer()
        
        limit = min(limit, 100)

        def check(message):
                if user and message.author != user:
                    return False
                if attachments and not message.attachments:
                    return False
                if links and "http" not in message.content:
                    return False
                return True
        try:
            deleted = await ctx.channel.purge(limit = limit + 1, check=check)
            await ctx.send(f'Deleted {len(deleted) - 1} message(s)', delete_after=3)
        except commands.MissingPermissions as e:
            raise e

    

    async def add_afk(self, user_id, guild_id, content=None):
        query = "SELECT * FROM afk WHERE user_id = ? AND guild_id = ?"
        async with self.bot.conn.cursor() as cursor:
            await cursor.execute(query, (user_id, guild_id))
            record = await cursor.fetchone()
        
            if record:
                query = "UPDATE afk SET reason = ? WHERE user_id = ? AND guild_id = ?"
                await cursor.execute(query, (content, user_id, guild_id))
            else:
                query = "INSERT INTO afk (user_id, guild_id, reason) VALUES (?, ?, ?)"
                await cursor.execute(query, (user_id, guild_id, content))
        
        await self.bot.conn.commit()

    async def remove_afk(self, user_id: int, guild_id: int):
        query = "DELETE FROM afk WHERE user_id = ? AND guild_id = ?"
        async with self.bot.conn.cursor() as cursor:
            await cursor.execute(query, (user_id, guild_id))
        
        await self.bot.conn.commit()

    @commands.hybrid_group(name='afk', description='Manage AFK status', help='Manage AFK status')
    @commands.cooldown(1, 2, commands.BucketType.user)
    @app_commands.guild_only()
    async def afk(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @afk.command(name='set', description='Set or remove AFK status', help='Set or remove AFK status')
    @app_commands.describe(content="The reason for being AFK")
    async def afk_(self, ctx: Context, *, content: str = None):
        user_id = ctx.author.id
        guild_id = ctx.guild.id

        if content:
            await ctx.send(f'{ctx.author.mention}, you are now AFK with the reason: {content}')
        else:
            await ctx.send(f'{ctx.author.mention}, you are now AFK.')

        await self.add_afk(user_id, guild_id, content)
    
    @afk.command(name='remove', description='Remove AFK status', help='Remove AFK status')
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(user='The user to remove AFK status from')
    async def afk_r(self, ctx: Context, user: discord.User):
        guild_id = ctx.guild.id

        await self.remove_afk(user.id, guild_id)
        await ctx.send(f'Removed AFK status from {user.name}. If they had one.')

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        async with self.bot.conn.cursor() as cursor:
            query = "SELECT * FROM afk WHERE user_id = ? AND guild_id = ?"
            await cursor.execute(query, (message.author.id, message.guild.id))
            afk_author = await cursor.fetchone()

            if afk_author:
                await self.remove_afk(message.author.id, message.guild.id)
                await message.channel.send("Back? Okay, I've removed your AFK status.")
                
            if message.mentions:
                for mentioned_user in message.mentions:
                    await cursor.execute(query, (mentioned_user.id, message.guild.id))
                    afk_c = await cursor.fetchone()
                    
                    if afk_c:
                        reason = afk_c[2] if afk_c else None  
                        if reason:
                            await message.channel.send(f'{mentioned_user.display_name} is currently AFK. \n{reason}')
                        else:
                            await message.channel.send(f'{mentioned_user.display_name} is currently AFK.')

async def setup(bot: QillBot):
    await bot.add_cog(Basic(bot))


