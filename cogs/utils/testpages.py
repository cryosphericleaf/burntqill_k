import discord 
from discord.ext.commands import Context

"""
Minimal pages nav
Usage:
        view = PageView(ctx, pages)
        await view.start()

pages: list of strings or embeds
"""

class PageView(discord.ui.View):
    def __init__(self,
                ctx: Context,
                pages: list) -> None:
        super().__init__(timeout=60) 
        self.ctx: Context = ctx 
        self.pages: list = pages
        self.current_page = 0
        self.mfrmsg: discord.Message = None
        if len(self.pages) == 1:
            for button in self.children:
                button.disabled = True
        else:
            self.children[0].disabled = self.children[1].disabled = (self.current_page == 0)
            self.children[2].disabled = self.children[3].disabled = (self.current_page == len(self.pages) - 1)
            self.children[5].disabled = (len(self.pages) < 4)

    async def update_message(self, interaction: discord.Interaction):
        try:
            if self.current_page < 0:
                self.current_page = 0
            elif self.current_page >= len(self.pages):
                self.current_page = len(self.pages) - 1

            if len(self.pages) == 1:
                for button in self.children:
                    button.disabled = True
            else:
                self.children[0].disabled = self.children[1].disabled = (self.current_page == 0)
                self.children[3].disabled = self.children[4].disabled = (self.current_page >= len(self.pages) - 1)
                self.children[5].disabled = (len(self.pages) < 4)

            
            page = self.pages[self.current_page]
            
            if isinstance(page, discord.Embed):
                if interaction.message:
                    await interaction.message.edit(content=None, embed=page, view=self)
                else:
                    await interaction.response.edit_message(content=None, embed=page, view=self)
            else:
                if interaction.message:
                    await interaction.message.edit(content=page, embed=None, view=self)
                else:
                    await interaction.response.edit_message(content=page, embed=None, view=self)

        except discord.NotFound:
            await self.ctx.send(f"Message with ID {self.ctx.message.id} not found")
       

    @discord.ui.button(label="|<", style=discord.ButtonStyle.green)
    async def first_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 0
        await self.update_message(interaction)

    @discord.ui.button(label="<", style=discord.ButtonStyle.grey)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        await self.update_message(interaction)

    @discord.ui.button(label='Quit', style=discord.ButtonStyle.red)
    async def stop_pages(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.delete_original_response()
        self.stop()

    @discord.ui.button(label=">", style=discord.ButtonStyle.grey)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        await self.update_message(interaction)

    @discord.ui.button(label=">|", style=discord.ButtonStyle.green)
    async def last_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = len(self.pages) - 1
        await self.update_message(interaction)

    @discord.ui.button(label="Go To", style=discord.ButtonStyle.blurple, custom_id="gotob")
    async def goto_button(self, interaction: discord.Interaction, button: discord.ui.Button):
       
            gomodal = Gotomodal(view=self, interaction=interaction)  
            await interaction.response.send_modal(gomodal)
            timed_out = await gomodal.wait()
            if timed_out:
                await interaction.followup.send('Took too long', ephemeral=True)
            return
    

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You cannot use this button :(", ephemeral=True)
            return False
        else:
            if interaction.data['custom_id'] != 'gotob':  
                await interaction.response.defer(ephemeral=True)
            return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

        await self.mfrmsg.edit(view=self)

    async def start(self):
        page = self.pages[self.current_page]
        
        if len(self.pages) == 1:
            if isinstance(page, discord.Embed):
                self.mfrmsg = await self.ctx.send(embed=page)
            else:
                self.mfrmsg = await self.ctx.send(content=page)
        else:
            if isinstance(page, discord.Embed):
                self.mfrmsg = await self.ctx.send(embed=page, view=self)
            else:
                self.mfrmsg = await self.ctx.send(content=page, view=self)


class Gotomodal(discord.ui.Modal, title='Go To'):
    pageno = discord.ui.TextInput(label='Enter the page number.', style=discord.TextStyle.short)

    def __init__(self, view: PageView, interaction: discord.Interaction):
        super().__init__(timeout=300)
        self.view = view
        self.interaction = interaction

    async def on_submit(self, interaction: discord.Interaction):
        page = self.pageno.value
        await interaction.response.defer()
        if not page.isdigit():
            await interaction.followup.send(f'Expected a number not {page!r}', ephemeral=True)
            return
        else:
            self.view.current_page = int(page) - 1
            await self.view.update_message(interaction)
          
