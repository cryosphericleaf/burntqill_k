from __future__ import annotations

from .dtypes import Monster, Move, MoveCat, Type
from .player import Player
from .zengo import ZenGo
import discord 
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from field import Field

struggle: Move = Move(id=000, identifier="struggle", move_type = Type.NORMAL, movecat=MoveCat.PHYSICAL, power= 40, priority=0 )

### idek whats happening here

class AskForSwitch(discord.ui.View):
    def __init__(self, field: Field, slot: Monster):
        super().__init__(timeout=300)
        self.field = field
        self.slot = slot
        self.m = None
        self.owner: Player = self.slot.owner

    async def start(self):
        embed = discord.Embed(description=f"{self.owner.nick} select pokemon to switch in place of {self.slot.name}", color=0xffebf8)
        m = await self.field.ch.send(embed=embed, view=self)
        self.m = m

    @discord.ui.button(label='Select to switch', style=discord.ButtonStyle.green)
    async def selecttoswi(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.clear_items()
        switchable_mons = self.owner.switchable_mons(self.slot)
        for switchable_mon in switchable_mons:
            self.add_item(AFSwitchButton(self.field, self.slot, switchable_mon, self.m))
       
        await interaction.response.send_message("Select a Pokemon", view=self, ephemeral=True)


    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != int(self.owner.user):
            await interaction.response.send_message("You cannot use this button :(", ephemeral=True)
            return False
        else:
            return True

    # async def on_timeout(self) -> None:
    #     embed = discord.Embed(description=f"{self.owner.nick} did not selected pokemon to switch the other player won!", color=0xffebf8)
    #     await self.field.ch.send(embed=embed)
    #     self.field.view.stop()
    #     self.stop() 

class AFSwitchButton(discord.ui.Button):
    def __init__(self, field: Field, slot: Monster, mon: Monster, mpre: discord.Message):
        super().__init__(style=discord.ButtonStyle.green, label=mon.name.capitalize(), row=0)
        self.slot = slot
        self.field = field
        self.mon =  mon
        self.mpre = mpre
        self.owner: Player = self.slot.owner
   

    async def callback(self, interaction: discord.Interaction):
        zengo = ZenGo(self.field)

        self.owner.set_mon_to_x(self.slot, self.mon)
        await self.mpre.edit(view=None)
        await interaction.response.edit_message(content=f"{self.mon.name} selected to switchin", view=None)
        if self.slot.turn_move_switch == True:
            text = await zengo.on_switch(self.mon, self.slot)
            await interaction.channel.send(embed=discord.Embed(description=text, color=0xffebf8))
        else:
            self.field.switch_mons.append(self.mon)

        self.field.FSC -= 1
        self.field.event.set()
        if self.field.FSC == 0:
            try:
                if len(self.field.switch_mons) != 0:
                    text = " "
                    self.field.switch_mons = sorted(self.field.switch_mons, key=lambda x: (x.spe), reverse=True)
                    for mon in self.field.switch_mons:
                        text += await zengo.on_switch(mon)
                    await interaction.followup.send(embed=discord.Embed(description=text, color=0xffebf8))
                    await self.field.update_battle_screen(self.field.ch)
            except Exception as e:
                print(e)
        else:
            await self.field.handle_fainting()
       
class ActionsView(discord.ui.View):
    def __init__(self, field: Field):
        super().__init__(timeout=180)
        self.field = field
        
    @discord.ui.button(label='Select Action', style=discord.ButtonStyle.green)
    async def action(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            slots = []
            self.clear_items()
            player1_user_id = int(self.field.player1.user)
            if interaction.user.id == player1_user_id:
                slots = [self.field.player1.crrmon1, self.field.player1.crrmon2]
            else:
                slots = [self.field.player2.crrmon1, self.field.player2.crrmon2]

            remaining_pokemon = [slot for slot in slots if isinstance(slot, Monster) and slot.hp > 0]
            remaining_pokemon = [slot for slot in remaining_pokemon]

            for slot in remaining_pokemon:
                self.add_item(monButton(self.field, slot))  
            await interaction.response.send_message("Select a Pokemon", view=self, ephemeral=True)
        except Exception as e:
            print(e)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id  == int(self.field.player1.user) or int(self.field.player2.user):
           return True
        else:
            await interaction.response.send_message(content="you cannot use this button...", view=None, ephemeral=True)

    async def on_timeout(self) -> None:
        embed = discord.Embed(description=f"The battle was abondoned.", color=0xffebf8)
        await self.field.ch.send(embed=embed)
        self.field.view.stop()
        self.stop()

        
class monButton(discord.ui.Button):
    def __init__(self, field: Field, mon: Monster, *, disabled=False, row=0):
        label = f"{mon.name.capitalize()}"
        super().__init__(style=discord.ButtonStyle.green, label=label, disabled=disabled, row=row)
        self.mon = mon
        self.field = field

    async def callback(self, interaction):

        if (self.mon.crrmv is not None and self.mon.crrtar is not None) or (self.mon.switch is not None) or (self.mon.crrmv is not None and self.mon.req_charge_rec is not None and self.mon.req_charge_rec.id in [307, 795, 338, 416, 308, 63, 794, 711, 459, 439]):
            await interaction.response.send_message("You have already set up a move and target or switch for this Pokémon. You cannot select it again.", ephemeral=True)
            return
        
                                                                            ### Moves that require recharge 
        if self.mon.req_charge_rec != None and self.mon.req_charge_rec.id in [307, 795, 338, 416, 308, 63, 794, 711, 459, 439]:
            self.mon.crrmv = self.mon.req_charge_rec
            await self.field.increment_selection_counter()
            await interaction.response.edit_message(content=f"{self.mon.crrmv.identifier} needs to be recharged.", view=None)
            return 

        moves = [move for move in self.mon.moves if move.pp > 0]

        if not moves:
            moves = [struggle]
        view = movesView(self.field, self.mon)
        for move in moves:
            await view.add_move_buttons(move)
        await interaction.response.edit_message(content=f"selected {self.mon.name}", view=None)
        await interaction.followup.send(content="Select move", view=view, ephemeral=True)

class movesView(discord.ui.View):
    def __init__(self, field: Field, mon: Monster):
        super().__init__(timeout=180)
        self.field = field
        self.mon = mon
        self.player: Player = self.mon.owner
    
    async def add_move_buttons(self, move: Move):
        self.add_item(moveButton(self.field, self.mon, move))

    @discord.ui.button(label='Switch', style=discord.ButtonStyle.green, row=2)
    async def switch(self, interaction: discord.Interaction, button: discord.ui.Button):
        switchable_mons = self.player.switchable_mons(self.mon)
        if switchable_mons == []:
            await interaction.response.send_message(content='No pokemon left to switch',view=None, ephemeral=True)
        else:
            await interaction.response.edit_message(content="selected to switch", view=None)
            view = SwitchableView(self.field, self.mon)
            await view.add_switchable_buttons()
            await interaction.followup.send(content='select to switch',view=view, ephemeral=True)


class moveButton(discord.ui.Button):
    def __init__(self, field: Field, mon: Monster, move: Move, *, disabled=False, row=0):
        label = f"{move.identifier.capitalize()} pp: {move.pp}"
        super().__init__(style=discord.ButtonStyle.grey, label=label, disabled=disabled, row=row)
        self.move = move 
        self.field = field 
        self.mon = mon
        self.disabled = True if self.mon.choice_locked_move is not None and self.mon.choice_locked_move != self.move else False 

    async def callback(self, interaction: discord.Interaction):
        if self.mon.crrmv:
            await interaction.response.send_message("You have already selected a move for this Pokémon. You cannot select another move.", ephemeral=True)
            return
      
        if self.mon.switch:
            await interaction.response.send_message("You have already selected to switch this Pokémon. You cannot select a move now.", ephemeral=True)
            return 

        await interaction.response.edit_message(content=f"move selected {self.move.identifier}", view=None)
        # if self.move.target != "self" and self.move.target != "adj" and self.move.target != "all_adj":
        if self.move.target == None:
            view = tarView(self.field, self.mon, self.move)
            await view.add_target_buttons()
            await interaction.followup.send(content="select target pokemon", view=view, ephemeral=True)
        else:
            self.mon.crrmv = self.move
            await self.field.increment_selection_counter()


class tarView(discord.ui.View):
    def __init__(self, field: Field, source_monster: Monster, mv: Move):
        super().__init__()
        self.field = field
        self.source_monster = source_monster
        self.mv = mv
    
    async def add_target_buttons(self):
        for slot in self.field.get_slot_list(pure=True):
            if slot and slot != self.source_monster:
                self.add_item(Tarbutton(self.field, self.source_monster, slot, self.mv))


class Tarbutton(discord.ui.Button):
    def __init__(self, field: Field, source_mon: Monster, target_mon: Monster, mv: Move, disabled=False, row=0):
        label = f"{target_mon.name.capitalize()}"
        super().__init__(style=discord.ButtonStyle.grey, label=label, disabled=disabled, row=row)
        self.target_monster = target_mon
        self.field = field
        self.source_mon = source_mon
        self.mv = mv

    async def callback(self, interaction: discord.Interaction):
        self.source_mon.crrmv = self.mv
      
        tar_slot_num = self.target_monster.owner.get_crrmon_num(self.target_monster)
        self.source_mon.crrtar = tar_slot_num
        await interaction.response.edit_message(content=f"target selected {self.target_monster.name}", view=None)
        await self.field.increment_selection_counter()

class SwitchableView(discord.ui.View):
    def __init__(self, field: Field, mon: Monster):
        super().__init__()
        self.field = field
        self.mon = mon
        self.player: Player = self.mon.owner

    async def add_switchable_buttons(self):
        switchable_mons = self.player.switchable_mons(self.mon)
        for switchable_mon in switchable_mons: 
            self.add_item(SwitchableMonButton(self.field, self.mon, switchable_mon))
            

class SwitchableMonButton(discord.ui.Button):
    def __init__(self, field: Field, mon: Monster, switch_mon: Monster, *, disabled=False, row=0):
        label = f"{switch_mon.name.capitalize()}"
        super().__init__(style=discord.ButtonStyle.green, label=label, disabled=disabled, row=row)
        self.field = field
        self.mon = mon
        self.switch_mon = switch_mon

    async def callback(self, interaction: discord.Interaction):
        if self.mon.crrmv:
            await interaction.response.send_message("You have already selected a move for this Pokémon. You can't switch now.", ephemeral=True)
            return

        self.mon.switch = self.switch_mon
        await interaction.response.edit_message(content=f"{self.switch_mon.name} selected to switch", view=None)
        await self.field.increment_selection_counter()