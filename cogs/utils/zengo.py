from __future__ import annotations

from .dtypes import Monster, Type, Status, Weather
from .player import Player
from .damage import Damage
from .effects import WeatherEffect
import discord

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .field import Field

class ZenGo:
    def __init__(self, field: Field ) -> None:
        self.field = field

    def handle_hazards(self, slot: Monster) -> str:
        dmg = Damage(self.field.crrw, self.field)
        player: Player =  slot.owner
        if player.stealth_rock == True:
            m = dmg.calculate_effectiveness(slot.type1, slot.type2)
            if m == 0.25:
                damage_amount = round(slot.maxhp * 0.03125)
            elif m == 0.5:
                damage_amount = round(slot.maxhp * 0.0625)
            elif m == 1:
                damage_amount = round(slot.maxhp * 0.125)
            elif m == 2:
                damage_amount = round(slot.maxhp * 0.25)
            elif m == 4:
                damage_amount = round(slot.maxhp * 0.5)
            slot.hp - damage_amount
            text = f"\n{slot.name} took {damage_amount} damage from stealth-rock!"
        else:
            text = ""
        if slot.hp <= 0:
            text += f"\n{slot.name} fainted!"
        return text



    async def on_switch(self, slot: Monster, prevslot: Monster = None) -> str:

        if prevslot is None:
            _text = f"\n{slot.name} switched in"
        else:     
            _text = f"{slot.name} switched in place of {prevslot.name}"

        _text += self.handle_hazards(slot)

        if prevslot:
            prevslot.stage.reset()
            prevslot.reset_on_switch()
        if slot.ability == "drizzle" and self.field.crrw.weather != Weather.rain:
            turns = 8 if slot.item == "damp-rock" else 5
            self.field.crrw = WeatherEffect(weather=Weather.rain, turns=turns)
            _text += "\nIt started raining!"
        elif slot.ability == "drought" and self.field.crrw.weather != Weather.sun:
            turns = 8 if slot.item == "heat-rock" else 5
            self.field.crrw = WeatherEffect(weather=Weather.sun, turns=turns)
            _text += f"\n{slot.name}'s drought intensified the sun's rays!"
        elif slot.ability == "snow-warning" and self.field.crrw.weather != Weather.snow:
            turns = 8 if slot.item == "icy-rock" else 5
            self.field.crrw = WeatherEffect(weather=Weather.snow, turns=turns)
            _text += "\nA hailstorm has started!"
        elif slot.ability == "sand-stream" and self.field.crrw.weather != Weather.sand:
            turns = 8 if slot.item == "smooth-rock" else 5
            self.field.crrw = WeatherEffect(weather=Weather.sand, turns=turns)
            _text += "\nA sandstorm kicked up!"
        elif slot.ability == "intimidate":
            _text += f"\n{slot.name} intimidates the foes"
            foes = self.field.get_adjacent_targets(slot)
            for foe in foes:
                foe: Monster
                _text += foe.stage.increment("atk", -1)

        if slot.hp <= 0:
            self.field.handle_fainting()
        if await self.field.end_battle_if_possible() == True:
            return
        
        return _text
            
    async def handle_aftermath(self):
        aff_text = ""
        wt = self.field.crrw.weather_tick()###
        if wt:
            aff_text = wt
    
        if await self.field.end_battle_if_possible() == True:
            return

        slots = self.field.get_slot_list(pure=True)
        sorted_slots = sorted(slots, key=lambda x: (x.spe * x.stage.spe), reverse=True)# could be more multipliers 
        for slot in sorted_slots:
            slot: Monster   
            if slot.hp > 0:
                if not slot.secstatus.bounced or not slot.secstatus.fly or not slot.secstatus.disappeared or not slot.secstatus.underground or not slot.secstatus.underwater:
                    if self.field.crrw.weather == Weather.sand and not (slot.type1 in [Type.ROCK, Type.STEEL, Type.GROUND] or slot.type2 in [Type.ROCK, Type.STEEL, Type.GROUND]):
                        slot.hp -= (slot.maxhp // 16)
                        aff_text += f"\n{slot.name} took {(slot.maxhp // 16)} from sandstorm!"
                if slot.status == Status.poisoned:
                    slot.hp -= (slot.maxhp // 8)
                    aff_text += f"\n{slot.name} took {(slot.maxhp // 8)} from its poision!"
                if slot.status == Status.burned:
                    slot.hp -= (slot.maxhp // 16)
                    aff_text += f"\n{slot.name} took {(slot.maxhp // 16)} from its burn!"
                if slot.status == Status.badly_poisoned:
                    aff_text += slot.badly_poison_tick()
                if slot.heal_block == False:
                    if slot.item == "leftovers" and slot.heal_block == False:
                        heal_amount = min(slot.maxhp - slot.hp, slot.maxhp // 16) 
                        slot.hp += heal_amount
                        aff_text += f"\n{slot.name} healed {heal_amount} from its {slot.item}!"
            aff_text += f"\n{slot.name} fainted!" if slot.hp <= 0 else ""
            if await self.field.end_battle_if_possible() == True:
                return
            
            
        if aff_text:
            embed = discord.Embed(description=aff_text.strip(), color=0xffebf8)
            await self.field.ch.send(embed=embed)
        else:
            pass