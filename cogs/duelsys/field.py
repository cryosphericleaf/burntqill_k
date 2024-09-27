from __future__ import annotations
from .dtypes import Monster, Move, MoveCat, Type, Status, Weather
from .player import Player
from .buttons import AskForSwitch, ActionsView
from .effects import WeatherEffect 
from .zengo import ZenGo
import discord 
from .fieldimg import FieldImg
from .damage import Damage
from .nondmg import NonDamage
from io import BytesIO       
import random   
from .fu import switch_moves, pre_charge_moves, tclr
import copy 
import asyncio

struggle: Move = Move(id=000, identifier="struggle", move_type = Type.NORMAL, movecat=MoveCat.PHYSICAL, power= 40, priority=0 )

  
class Field:
    def __init__(self, ch: discord.TextChannel, player1: Player, player2: Player):
        self.ch = ch
        self.turn_counter = 1
        self.current_terrain = None
        self.crrw = WeatherEffect(Weather.clear, 0)
        self.active_ruin_abilities = []
        self.player1 = player1
        self.player2 = player2

        self.selection_counter = 0 # selection counter for action execution
        self.FSC = 0
        self.view = None
        self.pokemon_fainted = False
        self.switch_mons = []
        self.nullified = False#not sure
        self.event = asyncio.Event()
        self.dmg = Damage(self.crrw, self)
        self.zengo = ZenGo(self)

    def get_opponent(self, mon: Monster) -> Player:
        if mon.owner == self.player1:
            return self.player2
        else:
            return self.player1
        
    def get_tarmon_from_num(self, mon: Monster, x: int) -> Monster:
        foe = self.get_opponent(mon)
        return foe.get_crrmon(x)

    def get_adjacent_targets(self, player: Player):
        if player == self.player1:
            return tuple(filter(lambda mon: isinstance(mon, Monster), (self.player2.crrmon1, self.player2.crrmon2)))
        else:
            return tuple(filter(lambda mon: isinstance(mon, Monster), (self.player1.crrmon1, self.player1.crrmon2)))

    def get_all_adj_mons(self, mon: Monster):
        mons = self.get_slot_list(pure=True)
        return [x for x in mons if x != mon]
        
    def get_slot_list(self, pure: bool = True) -> list:
        mons = [self.player1.crrmon1, self.player1.crrmon2, self.player2.crrmon1, self.player2.crrmon2]
        if pure:
            return [mon for mon in mons if mon != None]
        else:
            return mons

    async def end_battle_if_possible(self) -> bool:# cannot use in aftermath
        if all(mon.status == Status.fainted for mon in self.player1.monsters):
            embed = discord.Embed(description=f"{self.player2.nick} won!", color=0xffebf8)
            await self.ch.send(embed=embed)
            self.view.stop()
            return True
        if all(mon.status == Status.fainted for mon in self.player2.monsters):
            embed = discord.Embed(description=f"{self.player1.nick} Won!", color=0xffebf8)
            await self.ch.send(embed=embed)
            self.view.stop()
            return True
        return False
        
    async def increment_selection_counter(self):
        self.selection_counter += 1
        none_count = sum(1 for slot in [self.get_slot_list(pure=False)] if slot == None)
        required_count = 4 - none_count
        if self.selection_counter == required_count:
            await self.execute()

    async def update_battle_screen(self, ch: discord.TextChannel):
        self.selection_counter = 0
        self.FSC = 0
        self.switch_mons = []
        self.view.stop()
        slots = self.get_slot_list()
        for slot in slots:
            slot: Monster
            slot.reset()#attr that reset after every turn
        new_view = ActionsView(self)
        self.view = new_view
  
        imgbytes = await self.genzai()
        file = discord.File(imgbytes, filename='field.png')
        embed = discord.Embed(title=f'Battle between {self.player1.nick} and {self.player2.nick} (Turn {self.turn_counter})', color=0xffebf8)
        embed.set_image(url=f"attachment://{file.filename}")
        await ch.send(embed=embed, file=file, view=new_view)


    async def start(self, ch: discord.TextChannel):
        _text = " "
        slots = self.get_slot_list(pure=True)
        sorted_slots = sorted(slots, key=lambda x: (x.spe), reverse=True)
        for slot in sorted_slots:
           _text += await self.zengo.on_switch(slot=slot)
        await ch.send(embed= discord.Embed(description=_text, color=0xffebf8))
        view = ActionsView(self)
        self.view = view
        imgbytes = await self.genzai()
        file = discord.File(imgbytes, filename='field.png')
        embed = discord.Embed(title=f'Battle between {self.player1.nick} and {self.player2.nick} (Turn {self.turn_counter})', color=0xffebf8)
        embed.set_image(url=f"attachment://{file.filename}")
        await ch.send(embed=embed, file=file, view=view)

    async def genzai(self) -> BytesIO:
        img = FieldImg(self)
        imgbytes = await img.create_field_image()
        return imgbytes

    async def handle_switch_move(self, slot: Monster):
        view = AskForSwitch(self, slot)
        await view.start()
    
    async def execute(self):
        self.turn_counter += 1 
        ### reset execution the counter
        self.selection_counter = 0
        await self.handle_expl_switch()

        moves_to_execute = []

        slots = self.get_slot_list(pure=True)
        for slot in slots:
            if slot.crrmv != None:
                moves_to_execute.append((slot, slot.crrmv, slot.crrtar))
                
        # sortin of execution
        moves_to_execute = sorted(
            moves_to_execute,
            key=lambda x: (
                x[1].priority,
                (
                    x[0].spe * 
                    x[0].stage.spe * 
                    (1.5 if x[0].item == "choice-scarf" else 1) *
                    (0.5 if x[0].status == Status.paralyzed else 1) * 
                    (
                        2 if (self.crrw.weather == Weather.rain and x[0].ability == "swim-swift") or 
                            (self.crrw.weather == Weather.sun and x[0].ability == "chlorophyll") or 
                            (self.crrw.weather == Weather.sand and x[0].ability == "sand-rush")
                        else 1
                    )
                )
            ),
            reverse=True
        )

        for slot, move, target_slot in moves_to_execute:
            slot: Monster
            player: Player = slot.owner
            move: Move
            if target_slot:
                target_slot = self.get_tarmon_from_num(slot, target_slot)
            target_slot: Monster
            move_did_hit = False### for later u turn checking
            execution_text = f"{slot.name} used {move.identifier}!"
            if slot.status == Status.asleep:
                execution_text = slot.sleep_tick()
            is_paralyzed = slot.status == Status.paralyzed and random.randint(1, 4) == 1
            if is_paralyzed:
                execution_text = f"{slot.name} is paralyzed! it can't move! "
            if slot.secstatus.flinch == True:
                execution_text = f"\n{slot.name} flinched!"
            if slot.status == Status.frozen:
                if random.randint(1, 100) <= 20 or move.id in [503, 902, 592, 815]:
                    slot.status = Status.healthy
                    execution_text = f"{slot.name} thawed out!"
                else:
                    execution_text = f"{slot.name} is frozen solid!"

            # Pre-Charge moves 
            if move.id in pre_charge_moves:#TODO sky-drop
                if move.id == 905 and self.crrw.weather == Weather.rain:
                    pass
                elif move.id == 76 and self.crrw.weather == Weather.sun:
                    pass
                elif slot.item == "power-herb":
                    execution_text += f"\n{slot.name} used its power herb!"
                    slot.item = None
                elif move.charge_counter == 0:
                    if move.id == 340:
                        slot.secstatus.bounced = True
                    elif move.id == 91:
                        slot.secstatus.underground = True
                    elif move.id == 291:
                        slot.secstatus.underwater = True
                    elif move.id == 19:
                        slot.secstatus.fly = True
                    elif move.id == 566:
                        slot.secstatus.disappeared = True
                    elif move.id == 800:# meteor beam
                        execution_text += slot.stage.increment("spa", 1)
                    elif move.id == 130:# skull bash
                        execution_text += slot.stage.increment("defense", 1)
                    execution_text += "\nIts charging!"
                    move.charge_counter = 1
                elif move.charge_counter == 1:
                    move.charge_counter = 0
                    slot.secstatus.bounced = False
                    slot.secstatus.disappeared = False
                    slot.secstatus.underground = False
                    slot.secstatus.underwater = False
                    slot.secstatus.fly = False 


            if all([
                slot.hp > 0, slot.status != Status.asleep, slot.status != Status.frozen,
                not is_paralyzed, slot.secstatus.flinch == False
                ]):
                if move.pp is not None:
                    move.pp -= 1
                if move.charge_counter != 1:
                    if target_slot is None:
                            if move.target == "adj" or move.target == "all_adj":### 2 or 3 targets 
                                _text = await self.handle_adj_moves(slot, move)
                                execution_text += _text                      ### only for recharge moves 
                            elif move.target == "self" or move.id in [307, 795, 338, 416, 308, 63, 794, 711, 459, 439]:### self or all targets 
                                nondmg = NonDamage(self)
                                x = await nondmg.handle_notar_moves(slot, move)
                                execution_text += x
                    else:
                        if move.accuracy is None or random.randint(1, 100) <= move.accuracy:
                            move_did_hit = True
                        else:
                            move_did_hit = False

                        if move_did_hit:
                                execution_text = f"{slot.name} used {move.identifier} on {target_slot.name}!"
                                if move.movecat == MoveCat.STATUS:
                                    nondmg = NonDamage(self)
                                    x = await nondmg.handle_tar_status_moves(slot, target_slot, move)
                                    execution_text += x
                                else:
                                    if target_slot.protected == False:
                                        execution_text += self.dmg.calc_dmg(slot, move, target_slot)
                                    else:
                                        execution_text += f"\n{target_slot.name} protected itself"
                                slot.req_charge_rec = move
                        else:
                            execution_text += f"\nBut it missed!"
                if slot.item in ["choice-band", "choice-scarf", "choice-specs"]:
                    slot.choice_locked_move = move 

            if move == struggle:
                slot.hp -= (slot.maxhp // 4)
                execution_text += f"\n{slot.name} hurt itself and took {slot.maxhp // 4} Damage!"
                
            protected_moves = ['protect', 'detect', 'wide-guard', 'quick-guard', 'spikey-shield', "king's-shield", "baneful-bunker", ]
            if move not in protected_moves:
                    slot.protected_turn = 0 # to reset the acc drop of protect if not consc
            if slot.hp > 0:
                embed = discord.Embed(description=execution_text, color=tclr.get(move.move_type))
                await self.ch.send(embed=embed)
                if await self.end_battle_if_possible() == True:
                    return
                slot.turns_after_switch += 1
                if move_did_hit:
                    if move.identifier in switch_moves:
                        n = player.switchable_mons(slot)
                        if len(n) != 0:
                            await self.handle_switch_move(slot)
                            slot.turn_move_switch = True
                            await self.event.wait()
            
        
        await self.zengo.handle_aftermath()

        slots = self.get_slot_list()
        for slot in slots:
            if slot.hp <= 0:
                self.FSC += 1
        self.pokemon_fainted = any(slot.hp <= 0 for slot in slots)
        if self.pokemon_fainted == False:
            await self.update_battle_screen(self.ch)
            return
        else:
            await self.handle_fainting()####
      
    ### multi target moves
    async def handle_adj_moves(self, mon: Monster, move: Move) -> str:
        foes: tuple = self.get_adjacent_targets(mon.owner) if move.target == "adj" else self.get_all_adj_mons(mon)
        move_c = copy.deepcopy(move)### maybe make this without deepcopy in damage.py itself
        _text = " "
        move_did_hit = False
        if len([foe for foe in foes if isinstance(foe, Monster)]) > 1:
            move_c.power *= 0.75

        for foe in foes:
            if move.accuracy is None or random.randint(1, 100) <= move.accuracy:
                    move_did_hit = True
            else:
                move_did_hit = False
            if move_did_hit:
                if isinstance(foe, Monster) and foe.hp > 0:
                    if move.movecat == MoveCat.STATUS:

                        nondmg = NonDamage(self)
                        x = await nondmg.handle_tar_status_moves(mon, foe, move)
                        _text += x
                    else:
                        if not foe.protected:
                            eff_text = self.dmg.calc_dmg(mon, move_c, foe)
                            _text += f"{eff_text}"
                            if move == struggle:
                                mon.hp -= (mon.maxhp // 4)
                                _text += f"\n{mon.name} hurt itself and took {mon.maxhp // 4} damage!"
                        else:
                            _text += f"\n{foe.name} protected itself"
                mon.req_charge_rec = move
            else:
                _text +=  f"\nBut it missed!"
        return _text


    async def handle_expl_switch(self):
        #(the slotxswitch is the one to be switched)
        slots = self.get_slot_list(pure=True)
        slots = sorted(slots, key=lambda x: (x.spe * x.stage.spe), reverse=True)
        for slot in slots:
            player: Player =  slot.owner
            slot: Monster
            if slot.switch:
                old_pokemon = slot
                old_pokemon.heal_block = False

                player.set_mon_to_x(slot, slot.switch)
                text = await self.zengo.on_switch(slot.switch, old_pokemon)
                embed = discord.Embed(description=text, color=0xffebf8)
                await self.ch.send(embed=embed)
            else:
                pass

    async def handle_fainting(self):#DONOT TOUCH THIS(╯°□°）╯︵ ┻━┻(using break and recall cause asyncio event not working idk why, later gonna change it)
        slots = self.get_slot_list(pure=True)
        for slot in slots:
            player: Player = slot.owner
            if slot.hp <= 0:
                switchable_mons = player.switchable_mons(slot)
                if len(switchable_mons) == 0:
                    player.set_mon_to_x(slot, None)
        for slot in slots:
            if slot.hp <= 0:
                player: Player = slot.owner
                slot: Monster
                slot.status = Status.fainted
                switchable_mons = player.switchable_mons(slot)
                if len(switchable_mons) == 0:
                    if await self.end_battle_if_possible() == True:
                        return
                    else:
                        await self.update_battle_screen(self.ch)
                        return
                view = AskForSwitch(self, slot)
                await view.start()
                break