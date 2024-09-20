from __future__ import annotations
from typing import Dict, Optional, Union, Any, TYPE_CHECKING, Sequence, Union

import discord
from discord.abc import Messageable
from discord.ext import commands, menus 
import traceback

if TYPE_CHECKING:
    from discord import Message, InteractionMessage, WebhookMessage

    Interaction = discord.Interaction[Any]
    Context = commands.Context[Any]

class NumberedPageModal(discord.ui.Modal, title='Go to page'):
    page = discord.ui.TextInput(label='Page', placeholder='Enter a number', min_length=1)

    def __init__(self, max_pages: Optional[int]) -> None:
        super().__init__()
        if max_pages is not None:
            as_string = str(max_pages)
            self.page.placeholder = f'Enter a number between 1 and {as_string}'
            self.page.max_length = len(as_string)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        self.interaction = interaction
        self.stop()

        


class RoboPages(discord.ui.View):
    def __init__(
        self,
        source: menus.PageSource,
        *,
        ctx: Context,
        check_embeds: bool = True,
        compact: bool = False,
    ):
        super().__init__()
        self.source: menus.PageSource = source
        self.check_embeds: bool = check_embeds
        self.ctx: Context = ctx
        self.message: Optional[discord.Message] = None
        self.current_page: int = 0
        self.compact: bool = compact
        self.clear_items()
        self.fill_items()

    def fill_items(self) -> None:
        if not self.compact:
            self.numbered_page.row = 1
            self.stop_pages.row = 1

        if self.source.is_paginating():
            max_pages = self.source.get_max_pages()
            use_last_and_first = max_pages is not None and max_pages >= 2
            if use_last_and_first:
                self.add_item(self.go_to_first_page)
            self.add_item(self.go_to_previous_page)
            if not self.compact:
                self.add_item(self.go_to_current_page)
            self.add_item(self.go_to_next_page)
            if use_last_and_first:
                self.add_item(self.go_to_last_page)
            if not self.compact:
                self.add_item(self.numbered_page)
            self.add_item(self.stop_pages)

    async def _get_kwargs_from_page(self, page: int) -> Dict[str, Any]:
        value = await discord.utils.maybe_coroutine(self.source.format_page, self, page)
        if isinstance(value, dict):
            return value
        elif isinstance(value, str):
            return {'content': value, 'embed': None}
        elif isinstance(value, discord.Embed):
            return {'embed': value, 'content': None}
        else:
            return {}

    async def show_page(self, interaction: discord.Interaction, page_number: int) -> None:
        page = await self.source.get_page(page_number)
        self.current_page = page_number
        kwargs = await self._get_kwargs_from_page(page)
        self._update_labels(page_number)
        if kwargs:
            if interaction.response.is_done():
                if self.message:
                    await self.message.edit(**kwargs, view=self)
            else:
                await interaction.response.edit_message(**kwargs, view=self)

    def _update_labels(self, page_number: int) -> None:
        self.go_to_first_page.disabled = page_number == 0
        if self.compact:
            max_pages = self.source.get_max_pages()
            self.go_to_last_page.disabled = max_pages is None or (page_number + 1) >= max_pages
            self.go_to_next_page.disabled = max_pages is not None and (page_number + 1) >= max_pages
            self.go_to_previous_page.disabled = page_number == 0
            return

        self.go_to_current_page.label = str(page_number + 1)
        self.go_to_previous_page.label = str(page_number)
        self.go_to_next_page.label = str(page_number + 2)
        self.go_to_next_page.disabled = False
        self.go_to_previous_page.disabled = False
        self.go_to_first_page.disabled = False

        max_pages = self.source.get_max_pages()
        if max_pages is not None:
            self.go_to_last_page.disabled = (page_number + 1) >= max_pages
            if (page_number + 1) >= max_pages:
                self.go_to_next_page.disabled = True
                self.go_to_next_page.label = '…'
            if page_number == 0:
                self.go_to_previous_page.disabled = True
                self.go_to_previous_page.label = '…'

    async def show_checked_page(self, interaction: discord.Interaction, page_number: int) -> None:
        max_pages = self.source.get_max_pages()
        try:
            if max_pages is None:
                # If it doesn't give maximum pages, it cannot be checked
                await self.show_page(interaction, page_number)
            elif max_pages > page_number >= 0:
                await self.show_page(interaction, page_number)
        except IndexError:
            # An error happened that can be handled, so ignore it.
            pass

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and interaction.user.id in (self.ctx.bot.owner_id, self.ctx.author.id):
            return True
        await interaction.response.send_message('This pagination menu cannot be controlled by you, sorry!', ephemeral=True)
        return False

    async def on_timeout(self) -> None:
        if self.message:
            await self.message.edit(view=None)

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        if interaction.response.is_done():
            await interaction.followup.send('An unknown error occurred, sorry', ephemeral=True)
        else:
            await interaction.response.send_message('An unknown error occurred, sorry', ephemeral=True)

        try:
            exc = ''.join(traceback.format_exception(type(error), error, error.__traceback__, chain=False))
            embed = discord.Embed(
                title=f'{self.source.__class__.__name__} Error',
                description=f'```py\n{exc}\n```',
                timestamp=interaction.created_at,
                colour=0xCC3366,
            )
            embed.add_field(name='User', value=f'{interaction.user} ({interaction.user.id})')
            embed.add_field(name='Guild', value=f'{interaction.guild} ({interaction.guild_id})')
            embed.add_field(name='Channel', value=f'{interaction.channel} ({interaction.channel_id})')
            await self.ctx.bot.stats_webhook.send(embed=embed)
        except discord.HTTPException:
            pass

    async def start(self, *, content: Optional[str] = None, ephemeral: bool = False) -> None:
        if self.check_embeds and not self.ctx.channel.permissions_for(self.ctx.me).embed_links:  # type: ignore
            await self.ctx.send('Bot does not have embed links permission in this channel.', ephemeral=True)
            return

        await self.source._prepare_once()
        page = await self.source.get_page(0)
        kwargs = await self._get_kwargs_from_page(page)
        if content:
            kwargs.setdefault('content', content)

        self._update_labels(0)
        self.message = await self.ctx.send(**kwargs, view=self, ephemeral=ephemeral)

    @discord.ui.button(label="|<", style=discord.ButtonStyle.green)
    async def go_to_first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """go to the first page"""
        await self.show_page(interaction, 0)

    @discord.ui.button(label='<', style=discord.ButtonStyle.grey)
    async def go_to_previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """go to the previous page"""
        await self.show_checked_page(interaction, self.current_page - 1)

    @discord.ui.button(label='Current', style=discord.ButtonStyle.grey, disabled=True)
    async def go_to_current_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label='Quit', style=discord.ButtonStyle.red)
    async def stop_pages(self, interaction: discord.Interaction, button: discord.ui.Button):
        """stops the pagination session."""
        await interaction.response.defer()
        await interaction.delete_original_response()
        self.stop()

    @discord.ui.button(label='>', style=discord.ButtonStyle.grey)
    async def go_to_next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """go to the next page"""
        await self.show_checked_page(interaction, self.current_page + 1)

    @discord.ui.button(label='>|', style=discord.ButtonStyle.green)
    async def go_to_last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """go to the last page"""
        # The call here is safe because it's guarded by skip_if
        await self.show_page(interaction, self.source.get_max_pages() - 1)  # type: ignore

    @discord.ui.button(label='Skip to page...', style=discord.ButtonStyle.grey)
    async def numbered_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """lets you type a page number to go to"""
        if self.message is None:
            return

        modal = NumberedPageModal(self.source.get_max_pages())
        await interaction.response.send_modal(modal)
        timed_out = await modal.wait()

        if timed_out:
            await interaction.followup.send('Took too long', ephemeral=True)
            return
        elif self.is_finished():
            await modal.interaction.response.send_message('Took too long', ephemeral=True)
            return

        value = str(modal.page.value)
        if not value.isdigit():
            await modal.interaction.response.send_message(f'Expected a number not {value!r}', ephemeral=True)
            return

        value = int(value)
        await self.show_checked_page(modal.interaction, value - 1)
        if not modal.interaction.response.is_done():
            error = modal.page.placeholder.replace('Enter', 'Expected')  # type: ignore # Can't be None
            await modal.interaction.response.send_message(error, ephemeral=True)


class ButtonPaginator(discord.ui.View):
    message: Optional[Message] = None

    def __init__(
        self,
        pages: Sequence[Any],
        *,
        author_id: Optional[int] = None,
        timeout: Optional[float] = 180.0,
        delete_message_after: bool = True,
        per_page: int = 1,
    ):
        super().__init__(timeout=timeout)
        self.author_id: Optional[int] = author_id
        self.delete_message_after: bool = delete_message_after

        self.current_page: int = 0
        self.per_page: int = per_page
        self.pages: Any = pages
        total_pages, left_over = divmod(len(self.pages), self.per_page)
        if left_over:
            total_pages += 1
 
        self.max_pages: int = total_pages


        

    def stop(self) -> None:
        self.message = None
        super().stop()

    async def interaction_check(self, interaction: Interaction) -> bool:
        if not self.author_id:
            return True

        if self.author_id != interaction.user.id:
            await interaction.response.send_message(
                "You cannot interact with this menu.", ephemeral=True
            )
            return False

        return True

    def get_page(self, page_number: int) -> Any:
        if page_number < 0 or page_number >= self.max_pages:
            self.current_page = 0
            return self.pages[self.current_page]

        if self.per_page == 1:
            return self.pages[page_number]
        else:
            base = page_number * self.per_page
            return self.pages[base : base + self.per_page]

    def format_page(self, page: Any) -> Any:
        return page

    async def get_page_kwargs(self, page: Any) -> Dict[str, Any]:
        formatted_page = await discord.utils.maybe_coroutine(self.format_page, page)

        kwargs = {"content": None, "embeds": [], "view": self}
        if isinstance(formatted_page, str):
            kwargs["content"] = str(formatted_page)
        elif isinstance(formatted_page, discord.Embed):
            kwargs["embeds"] = [formatted_page]
        elif isinstance(formatted_page, list):
            if not all(isinstance(embed, discord.Embed) for embed in formatted_page):
                raise TypeError("All elements in the list must be of type Embed")

            kwargs["embeds"] = formatted_page
        elif isinstance(formatted_page, dict):
            return formatted_page
        else:
            raise TypeError(
                "Page content must be one of str, discord.Embed, list[discord.Embed], or dict"
            )

        return kwargs

    def update_buttons(self) -> None:
        self.previous_page.disabled = self.max_pages < 2 or self.current_page <= 0
        self.first_page_button.disabled = self.max_pages < 2 or self.current_page <= 1
        self.next_page.disabled = (
            self.max_pages < 2 or self.current_page >= self.max_pages - 1
        )
        self.last_page_button.disabled = (
            self.max_pages < 3 or self.current_page >= self.max_pages - 2
        )
        self.goto_button.disabled = self.max_pages < 4

    async def update_page(self, interaction: Interaction) -> None:
        if self.message is None:
            self.message = interaction.message

        if len(self.pages) > 0:
            self.current_page = self.pages[self.current_page]

            
          


        self.update_buttons()
        kwargs = await self.get_page_kwargs(self.get_page(self.current_page))
        await interaction.response.edit_message(**kwargs)

    @discord.ui.button(label="|<", style=discord.ButtonStyle.green, custom_id="firstb")
    async def first_page_button(
        self, interaction: Interaction, _: discord.ui.Button
    ) -> None:
        self.current_page = 0
        await self.update_page(interaction)

    @discord.ui.button(label="<", style=discord.ButtonStyle.grey, custom_id="prevb")
    async def previous_page(
        self, interaction: Interaction, _: discord.ui.Button
    ) -> None:
        self.current_page -= 1
        await self.update_page(interaction)


    @discord.ui.button(label='Quit', style=discord.ButtonStyle.red, custom_id="quitb")
    async def stop_paginator(
        self, interaction: Interaction, _: discord.ui.Button
    ) -> None:
        if self.delete_message_after:
            if self.message is not None:
                await self.message.delete()
        else:
            await interaction.response.send_message("Stopped the paginator.")
            
        self.stop()

    @discord.ui.button(label=">", style=discord.ButtonStyle.grey, custom_id="nextb")
    async def next_page(self, interaction: Interaction, _: discord.ui.Button) -> None:
        self.current_page += 1
        await self.update_page(interaction)

    @discord.ui.button(label=">|", style=discord.ButtonStyle.green, custom_id="lastb")
    async def last_page_button(self, interaction: Interaction, _: discord.ui.Button) -> None:
        self.current_page = len(self.pages) - 1
        await self.update_page(interaction)

    @discord.ui.button(label="Go To", style=discord.ButtonStyle.blurple, custom_id="gotob")
    async def goto_button(self, interaction: Interaction, _: discord.ui.Button) -> None:
        try:
            gomodal = Gotomodal(interaction, self)  
            await interaction.response.send_modal(gomodal)
            timed_out = await gomodal.wait()

            if timed_out:
                await interaction.followup.send('Took too long', ephemeral=True)
            return
        except Exception as e:
            print(f"error occurred while opening the modal: {str(e)}")
    

    async def start(
        self, obj: Union[Interaction, Messageable], **send_kwargs: Any
    ) -> Optional[Union[Message, InteractionMessage, WebhookMessage]]:
        self.update_buttons()
        kwargs = await self.get_page_kwargs(self.get_page(self.current_page))
        if self.max_pages < 2:
            self.stop()
            del kwargs["view"]

        if isinstance(obj, discord.Interaction):
            if obj.response.is_done():
                self.message = await obj.followup.send(**kwargs, **send_kwargs)
            else:
                await obj.response.send_message(**kwargs, **send_kwargs)
                self.message = await obj.original_response()

        elif isinstance(obj, Messageable):
            self.message = await obj.send(**kwargs, **send_kwargs)
        else:
            raise TypeError(
                f"Expected Interaction or Messageable, got {obj.__class__.__name__}"
            )

        return self.message


    async def on_timeout(self) -> None:
      for item in self.children:
            item.disabled = True
      await self.message.edit(view=self)

class Gotomodal(discord.ui.Modal, title='Go To'):
    pageno = discord.ui.TextInput(label='Enter the page number.', style=discord.TextStyle.short)

    def __init__(self, interaction, view):
        super().__init__(timeout=300)
        self.interaction = interaction
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        page = self.pageno.value
        if not page.isdigit():
            await interaction.followup.send(f'Expected a number, not {page!r}', ephemeral=True)
            return
        elif int(page) <= 0:
            await interaction.followup.send('Please enter a positive page number.', ephemeral=True)
            return
        else:
            try:
                self.view.current_page = int(page) - 1
                await self.view.update_page(interaction)
            except Exception as e:
                print(e)


        