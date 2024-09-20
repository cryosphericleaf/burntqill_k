from __future__ import annotations

from .dtypes import Monster, Move, Status, Weather, Type 
from .effects import WeatherEffect 
import random

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .field import Field

class NonDamage:
    def __init__(self, field: Field) -> None:
        self.field = field

    async def handle_tar_status_moves(self, mon: Monster, targetslot: Monster, move: Move) -> str:
        _text = ""
        if targetslot.secstatus.fly or targetslot.secstatus.disappeared or targetslot.secstatus.underground or targetslot.secstatus.underwater:
            if mon.ability == "no-guard":
                pass
            else:
                return "but failed!"
                # Status Effects 
        if move.effect is not None:
            if move.effect == "burn" and random.randint(1, 100) <= move.eff_chance:
                _text += targetslot.set_status(status=Status.burned)
            elif move.effect == "para" and random.randint(1, 100) <= move.eff_chance:
                _text += targetslot.set_status(status=Status.paralyzed)
            elif move.effect == "poison" and random.randint(1, 100) <= move.eff_chance:
                _text += targetslot.set_status(status=Status.poisoned)
            elif move.effect == "bad-poison" and random.randint(1, 100) <= move.eff_chance:
                _text += targetslot.set_status(status=Status.badly_poisoned)
            elif move.effect == "sleep" and random.randint(1, 100) <= move.eff_chance:
                if move.id in [147, 79] and (targetslot.type1 != Type.GRASS and targetslot.type2 != Type.GRASS):
                              #^^^^^^^ not affected on grass type | For moves like spore
                    _text += targetslot.set_status(status=Status.asleep)
                else:
                    _text += "\nbut failed!"
            #todo: confusion
        else:      
            return '\nhad no effect'

        
    async def handle_notar_moves(self, mon: Monster, move: Move):
        if mon.req_charge_rec is not None:
            if mon.req_charge_rec.id in [307, 795, 338, 416, 308, 63, 794, 711, 459, 439]:
                text = f"\n{mon.req_charge_rec.identifier} is recharging."
                mon.req_charge_rec = None
                return text
            
        protected_moves = ['protect', 'detect', 'wide-guard', 'quick-guard', 'spikey-shield', "king's-shield", "baneful-bunker", ]
        if move.identifier in protected_moves:
            if move.identifier == 'endure':#todo
                text = f"\n{mon.name} braced itself for an incoming attack!"
            elif move.identifier == 'wide-guard':#todo
                text =  f"\n{mon.name} protected its team from wide-ranging moves!"
            else:
                text =  f"\n{mon.name} protected itself!"
            exe_c = 100
            
            if mon.protected_turn != 0:
                for i in range(mon.protected_turn):
                    exe_c *= (0.33)
                if random.randint(1, 100) <= exe_c:
                    mon.protected = True
                    mon.protected_turn += 1
                    return text
                else:
                    mon.protected_turn = 0
                    return "\nbut failed"
            else:
                mon.protected = True
                mon.protected_turn += 1
                return text
        elif move.id == 14:
            t = mon.stage.increment("atk", 2)
            return t
        elif move.id == 156:
            mon.hp = mon.maxhp
            return mon.set_status(Status.asleep)
        elif move.id == 240 and self.crrw.weather != Weather.rain:
            turns = 8 if mon.item == "damp-rock" else 5
            self.crrw = WeatherEffect(weather=Weather.rain, turns=turns)  
            return f"\nIt started raining!" 
        elif move.id == 339:
            t = mon.stage.increment("atk", 1)
            t += mon.stage.increment("defense", 1)
            return t
        elif move.id == 334:
            return mon.stage.increment("defense", 2)
        elif move.identifier in ["roost", "slack-off", "synthesis", "recover", "soft-boiled", "moonlight", "milk-drink", "morning-sun", "heal-order", "shore-up", "lunar-blessing"]:
            healed_amount = min(mon.maxhp - mon.hp, mon.maxhp // 2)
            mon.hp += healed_amount
            return f"\n{mon.name} healed {healed_amount} hp!"
        elif move.id == 446:
            opponent = self.field.get_opponent(mon)
            opponent.stealth_rock = True
            return f"\nPointed stone floats around {opponent.nick}'s team!"
        elif move.id == 432:
            self.field.player1.stealth_rock = None
            self.field.player2.stealth_rock = None
            return f"\n{mon.name} blew away the fog!"
        else:
            mon.protected_turn = 0####
            return "\nhad no effect"
        


        