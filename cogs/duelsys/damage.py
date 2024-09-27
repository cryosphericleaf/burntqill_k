from __future__ import annotations

from .dtypes import Monster, Move, MoveCat, Status, Type, Weather
from .effects import WeatherEffect
import random

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from field import Field

# implementation for damage dealing moves

class Damage:
    def __init__(self, crrw: WeatherEffect, field: Field) -> None:
        super().__init__()
        self.crrw = crrw### making a separate attribute for clean code
        self.field = field
    
    def random_factor(self) -> int:
        random_int = random.randint(85, 100)
        random_factor = random_int / 100  
        return random_factor
    
    def is_stab(self, mon: Monster, move: Move) -> bool:
        if mon.type1 or mon.type2 == move.move_type:
            return True
        else:
            return False
        
    def calculate_effectiveness(self, move_type: Type, target_type1: Type, target_type2: Type = None) -> float:
        type_chart = {
            Type.NORMAL: {Type.NORMAL: 1, Type.FIRE: 1, Type.WATER: 1, Type.ELECTRIC: 1, Type.GRASS: 1, Type.ICE: 1, Type.FIGHTING: 1, Type.POISON: 1, Type.GROUND: 1, Type.FLYING: 1, Type.PSYCHIC: 1, Type.BUG: 1, Type.ROCK: 0.5, Type.GHOST: 0, Type.DRAGON: 1, Type.DARK: 1, Type.STEEL: 0.5, Type.FAIRY: 1},
            Type.FIRE: {Type.NORMAL: 1, Type.FIRE: 0.5, Type.WATER: 0.5, Type.ELECTRIC: 1, Type.GRASS: 2, Type.ICE: 2, Type.FIGHTING: 1, Type.POISON: 1, Type.GROUND: 1, Type.FLYING: 1, Type.PSYCHIC: 1, Type.BUG: 2, Type.ROCK: 0.5, Type.GHOST: 1, Type.DRAGON: 0.5, Type.DARK: 1, Type.STEEL: 2, Type.FAIRY: 1},
            Type.WATER: {Type.NORMAL: 1, Type.FIRE: 2, Type.WATER: 0.5, Type.ELECTRIC: 1, Type.GRASS: 0.5, Type.ICE: 1, Type.FIGHTING: 1, Type.POISON: 1, Type.GROUND: 2, Type.FLYING: 1, Type.PSYCHIC: 1, Type.BUG: 1, Type.ROCK: 2, Type.GHOST: 1, Type.DRAGON: 0.5, Type.DARK: 1, Type.STEEL: 1, Type.FAIRY: 1},
            Type.ELECTRIC: {Type.NORMAL: 1, Type.FIRE: 1, Type.WATER: 2, Type.ELECTRIC: 0.5, Type.GRASS: 0.5, Type.ICE: 1, Type.FIGHTING: 1, Type.POISON: 1, Type.GROUND: 0, Type.FLYING: 2, Type.PSYCHIC: 1, Type.BUG: 1, Type.ROCK: 1, Type.GHOST: 1, Type.DRAGON: 0.5, Type.DARK: 1, Type.STEEL: 1, Type.FAIRY: 1},
            Type.GRASS: {Type.NORMAL: 1, Type.FIRE: 0.5, Type.WATER: 2, Type.ELECTRIC: 1, Type.GRASS: 0.5, Type.ICE: 1, Type.FIGHTING: 1, Type.POISON: 0.5, Type.GROUND: 2, Type.FLYING: 0.5, Type.PSYCHIC: 1, Type.BUG: 0.5, Type.ROCK: 2, Type.GHOST: 1, Type.DRAGON: 0.5, Type.DARK: 1, Type.STEEL: 0.5, Type.FAIRY: 1},
            Type.ICE: {Type.NORMAL: 1, Type.FIRE: 0.5, Type.WATER: 0.5, Type.ELECTRIC: 1, Type.GRASS: 2, Type.ICE: 0.5, Type.FIGHTING: 1, Type.POISON: 1, Type.GROUND: 2, Type.FLYING: 2, Type.PSYCHIC: 1, Type.BUG: 1, Type.ROCK: 1, Type.GHOST: 1, Type.DRAGON: 2, Type.DARK: 1, Type.STEEL: 0.5, Type.FAIRY: 1},
            Type.FIGHTING: {Type.NORMAL: 2, Type.FIRE: 1, Type.WATER: 1, Type.ELECTRIC: 1, Type.GRASS: 1, Type.ICE: 2, Type.FIGHTING: 1, Type.POISON: 0.5, Type.GROUND: 1, Type.FLYING: 0.5, Type.PSYCHIC: 0.5, Type.BUG: 0.5, Type.ROCK: 2, Type.GHOST: 0, Type.DRAGON: 1, Type.DARK: 2, Type.STEEL: 2, Type.FAIRY: 0.5},
            Type.POISON: {Type.NORMAL: 1, Type.FIRE: 1, Type.WATER: 1, Type.ELECTRIC: 1, Type.GRASS: 2, Type.ICE: 1, Type.FIGHTING: 1, Type.POISON: 0.5, Type.GROUND: 0.5, Type.FLYING: 1, Type.PSYCHIC: 1, Type.BUG: 1, Type.ROCK: 0.5, Type.GHOST: 0.5, Type.DRAGON: 1, Type.DARK: 1, Type.STEEL: 0, Type.FAIRY: 2},
            Type.GROUND: {Type.NORMAL: 1, Type.FIRE: 2, Type.WATER: 1, Type.ELECTRIC: 2, Type.GRASS: 0.5, Type.ICE: 1, Type.FIGHTING: 1, Type.POISON: 2, Type.GROUND: 1, Type.FLYING: 0, Type.PSYCHIC: 1, Type.BUG: 0.5, Type.ROCK: 2, Type.GHOST: 1, Type.DRAGON: 1, Type.DARK: 1, Type.STEEL: 2, Type.FAIRY: 1},
            Type.FLYING: {Type.NORMAL: 1, Type.FIRE: 1, Type.WATER: 1, Type.ELECTRIC: 0.5, Type.GRASS: 2, Type.ICE: 1, Type.FIGHTING: 2, Type.POISON: 1, Type.GROUND: 1, Type.FLYING: 1, Type.PSYCHIC: 1, Type.BUG: 2, Type.ROCK: 0.5, Type.GHOST: 1, Type.DRAGON: 1, Type.DARK: 1, Type.STEEL: 0.5, Type.FAIRY: 1},
            Type.PSYCHIC: {Type.NORMAL: 1, Type.FIRE: 1, Type.WATER: 1, Type.ELECTRIC: 1, Type.GRASS: 1, Type.ICE: 1, Type.FIGHTING: 2, Type.POISON: 2, Type.GROUND: 1, Type.FLYING: 1, Type.PSYCHIC: 0.5, Type.BUG: 1, Type.ROCK: 1, Type.GHOST: 1, Type.DRAGON: 1, Type.DARK: 0, Type.STEEL: 0.5, Type.FAIRY: 1},
            Type.BUG: {Type.NORMAL: 1, Type.FIRE: 0.5, Type.WATER: 1, Type.ELECTRIC: 1, Type.GRASS: 2, Type.ICE: 1, Type.FIGHTING: 0.5, Type.POISON: 1, Type.GROUND: 0.5, Type.FLYING: 0.5, Type.PSYCHIC: 2, Type.BUG: 1, Type.ROCK: 1, Type.GHOST: 1, Type.DRAGON: 1, Type.DARK: 2, Type.STEEL: 0.5, Type.FAIRY: 0.5},
            Type.ROCK: {Type.NORMAL: 1, Type.FIRE: 2, Type.WATER: 1, Type.ELECTRIC: 1, Type.GRASS: 1, Type.ICE: 2, Type.FIGHTING: 0.5, Type.POISON: 1, Type.GROUND: 0.5, Type.FLYING: 2, Type.PSYCHIC: 1, Type.BUG: 2, Type.ROCK: 1, Type.GHOST: 1, Type.DRAGON: 1, Type.DARK: 1, Type.STEEL: 0.5, Type.FAIRY: 1},
            Type.GHOST: {Type.NORMAL: 0, Type.FIRE: 1, Type.WATER: 1, Type.ELECTRIC: 1, Type.GRASS: 1, Type.ICE: 1, Type.FIGHTING: 1, Type.POISON: 1, Type.GROUND: 1, Type.FLYING: 1, Type.PSYCHIC: 1, Type.BUG: 1, Type.ROCK: 1, Type.GHOST: 2, Type.DRAGON: 1, Type.DARK: 0.5, Type.STEEL: 1, Type.FAIRY: 1},
            Type.DRAGON: {Type.NORMAL: 1, Type.FIRE: 1, Type.WATER: 1, Type.ELECTRIC: 1, Type.GRASS: 1, Type.ICE: 1, Type.FIGHTING: 1, Type.POISON: 1, Type.GROUND: 1, Type.FLYING: 1, Type.PSYCHIC: 1, Type.BUG: 1, Type.ROCK: 1, Type.GHOST: 1, Type.DRAGON: 2, Type.DARK: 1, Type.STEEL: 0.5, Type.FAIRY: 0},
            Type.DARK: {Type.NORMAL: 1, Type.FIRE: 1, Type.WATER: 1, Type.ELECTRIC: 1, Type.GRASS: 1, Type.ICE: 1, Type.FIGHTING: 0.5, Type.POISON: 1, Type.GROUND: 1, Type.FLYING: 1, Type.PSYCHIC: 2, Type.BUG: 1, Type.ROCK: 1, Type.GHOST: 2, Type.DRAGON: 1, Type.DARK: 0.5, Type.STEEL: 1, Type.FAIRY: 0.5},
            Type.STEEL: {Type.NORMAL: 1, Type.FIRE: 0.5, Type.WATER: 0.5, Type.ELECTRIC: 0.5, Type.GRASS: 1, Type.ICE: 2, Type.FIGHTING: 1, Type.POISON: 1, Type.GROUND: 1, Type.FLYING: 1, Type.PSYCHIC: 1, Type.BUG: 1, Type.ROCK: 2, Type.GHOST: 1, Type.DRAGON: 1, Type.DARK: 1, Type.STEEL: 0.5, Type.FAIRY: 2},
            Type.FAIRY: {Type.NORMAL: 1, Type.FIRE: 0.5, Type.WATER: 0.5, Type.ELECTRIC: 1, Type.GRASS: 1, Type.ICE: 1, Type.FIGHTING: 2, Type.POISON: 0.5, Type.GROUND: 1, Type.FLYING: 1, Type.PSYCHIC: 1, Type.BUG: 1, Type.ROCK: 1, Type.GHOST: 1, Type.DRAGON: 2, Type.DARK: 2, Type.STEEL: 0.5, Type.FAIRY: 1}
        }

        effectiveness = 1
        if move_type in type_chart:
            effectiveness *= type_chart[move_type].get(target_type1, 1)
            if target_type2:
                effectiveness *= type_chart[move_type].get(target_type2, 1)
        return effectiveness



    def calc_dmg(self, source_mon: Monster, move: Move, target_mon: Monster):

        damage: int = None           
        text = ""
        glaive_rush = 1
        critical = 1.5 if random.randint(1, 24) == 1 else 1
        stab = 1.5 if self.is_stab(source_mon, move) else 1
        effectiveness = self.calculate_effectiveness(move.move_type, target_mon.type1, target_mon.type2)
        burn = 0.5 if source_mon.status == Status.burned else 1

       # for rain and sun
        wpmul = 1.5 if (move.move_type == Type.WATER and self.crrw.weather == Weather.rain) or \
                (move.move_type == Type.FIRE and self.crrw.weather == Weather.sun) else \
                (0.5 if (move.move_type == Type.WATER and self.crrw.weather == Weather.sun) or \
                (move.move_type == Type.FIRE and self.crrw.weather == Weather.rain) else 1)

        ### for sand and snow  
        sandmul = 1.5 if (target_mon.type1 == Type.ROCK or target_mon.type2 == Type.ROCK) and self.crrw.weather == Weather.sand else 1
        snowmul = 1.5 if (target_mon.type1 == Type.ICE or target_mon.type2 == Type.ICE) and self.crrw.weather == Weather.snow else 1
        knockoff = 1.5 if move.id == 282 and target_mon.item else 1
        cband = 1.5 if source_mon.item == "choice-band" else 1
        cspecs = 1.5 if source_mon.item == "choice-specs" else 1


        movepower = move.power * wpmul * knockoff
        if move.id == 76 and self.crrw.weather != Weather.clear or self.crrw.weather != Weather.sun:
            movepower *= 0.5#decrease by 50%(solar beam)

        if move.movecat == MoveCat.PHYSICAL:
            damage = ((((2 * source_mon.level) / 5 + 2) * (movepower) * (source_mon.atk * source_mon.stage.atk * cband) / (target_mon.defense * target_mon.stage.defense * snowmul)) / 50 + 2)
        elif move.movecat == MoveCat.SPECIAL:
            damage = ((((2 * source_mon.level) / 5 + 2) * (movepower) * (source_mon.spa * source_mon.stage.spa *cspecs) / (target_mon.spd * target_mon.stage.spd * sandmul)) / 50 + 2)

        if effectiveness == 0:
            text += f"\nIt doesn't affect {target_mon.name}."
        elif effectiveness == 0.25:
            text += f"\nIt's NOT very effective!"
        elif effectiveness == 0.5:
            text += f"\nIt's not very effective!"
        elif effectiveness == 1:
            text += f"\nIt's effective."
        elif effectiveness == 2:
            text += f"\nIt's super effective!"
       

        if critical == 1.5:
            text += "\nIts a critical hit!"
      
        rf = self.random_factor()
        damage *= rf * glaive_rush * critical * stab * effectiveness * burn
        #Pre Damage 
        #moves
        if move.id in [909, 389]:#sucker punch / thunderclap
            mv: Move | None = target_mon.crrmv
            if mv and mv.movecat != MoveCat.STATUS and target_mon.status != Status.asleep:
                pass
            else: 
                return "\nbut failed!"
            
            
        # failing if target is not in range 
        if any([target_mon.secstatus.bounced, target_mon.secstatus.fly, target_mon.secstatus.disappeared, target_mon.secstatus.underground, target_mon.secstatus.underwater]):
            if source_mon.ability == "no-guard":
                pass
            elif target_mon.secstatus.underground:
                if move.id == 89 or move.id == 222:#magnitude and earthquake
                    damage *= 2
                elif move.id == 90:# fissure
                    pass
            elif target_mon.secstatus.underwater:
                if move.id == 250 or move.id == 57:# whirlpool and surf
                    damage *= 2
                elif move.id == 67:# low-kick
                    pass
            elif target_mon.secstatus.bounced:
                if move.id == 16 or move.id == 239:
                    damage *= 2
                elif move.id == 87 or move.id == 327 or move.id == 497:
                    pass
            else:
                return "\nbut failed!"
                     
                
        #items(could be 2 in one calc so dont use elif)
        if target_mon.item == "focus-sash" and target_mon.hp == target_mon.maxhp:
            damage = (target_mon.maxhp - 1)
            target_mon.item = None
            text += f"{target_mon.name} held on it using its focus sash!"

        if damage != 0:
            text += f"\n{target_mon.name} took {round(damage)} Damage!"
        target_mon.hp -= round(damage)###

        #After Damage
        #moves

        # Status Effects | Maybe move this in field.. maybe not
        if move.effect is not None:
            if move.effect == "flinch" and random.randint(1, 100) <= move.eff_chance:
                if move.id == 252:
                    if source_mon.turns_after_switch:
                        target_mon.secstatus.flinch = True
                        text +=f"\n{target_mon.name} flinched!"
                    else:
                        return "\nbut failed!"
                else:
                    target_mon.secstatus.flinch = True
                    text += f"\n{target_mon.name} flinched!"
            elif move.effect == "burn" and random.randint(1, 100) <= move.eff_chance:
                text += target_mon.set_status(status=Status.burned)
            elif move.effect == "para" and random.randint(1, 100) <= move.eff_chance:
                text += target_mon.set_status(status=Status.paralyzed)
            elif move.effect == "poison" and random.randint(1, 100) <= move.eff_chance:
                text += target_mon.set_status(status=Status.poisoned)
            elif move.effect == "bad-poison" and random.randint(1, 100) <= move.eff_chance:
                text += target_mon.set_status(status=Status.badly_poisoned)
            elif move.effect == "sleep" and random.randint(1, 100) <= move.eff_chance:
                text += target_mon.set_status(status=Status.asleep)
            elif move.effect == "freeze" and random.randint(1,100) <= move.eff_chance and (target_mon.type1 != Type.ICE or target_mon.type2 != Type.ICE):
                text += target_mon.set_status(status=Status.frozen)

        #todo: para
      


        elif move.id == 370:#close combat
            t = source_mon.stage.increment("atk", -1)
            t += source_mon.stage.increment("defense", -1)
            text += t
        elif move.id == 282 and target_mon.item:#knock off
            text += f"\n{target_mon.name} lost it's {target_mon.item}!"
            target_mon.item = None
        #items(could be 2 in one calc so dont use elif)
        if target_mon.item == "rocky-helmet" and move.contact == True:
            source_mon.hp -= (source_mon.maxhp//6)
            text += f"\n{source_mon.name} took {source_mon.maxhp//6} damage from {target_mon.name}'s rocky helmet!"
        #abilities(could be 2 in one calc so dont use elif)
        if target_mon.ability == "rough-skin" and move.contact == True:
            source_mon.hp -= (source_mon.maxhp//8)
            text += f"\n{source_mon.name} took {source_mon.maxhp//8} damage from {target_mon.name}'s rough skin!"

        return text
