from enum import IntEnum
from typing import List
import random 
import json

stagemul = {
-6: 0.25,  # 8/2
-5: 0.375, # 7/2
-4: 0.5,   # 6/2
-3: 0.625, # 5/2
-2: 0.75,  # 4/2
-1: 0.875, # 3/2
0: 1.0,    # 2/2
1: 1.5,    # 3/2
2: 2.0,    # 4/2
3: 2.5,    # 5/2
4: 3.0,    # 6/2
5: 3.5,    # 7/2
6: 4.0     # 8/2
}
    
class terrain(IntEnum):
    electric = 1
    grassy = 2
    misty = 3
    psychic = 4

class ruin_ability(IntEnum):
    beads_of_ruin = 1
    tablets_of_ruin = 2
    sword_of_ruin = 3
    vessel_of_ruin = 4


class Weather(IntEnum):
    sun = 1
    rain = 2
    sand = 3
    snow = 4
    harsh_sunshine = 5
    heavy_rain = 6
    strong_winds = 7
    clear = 8


class Type(IntEnum):
    NORMAL = 1
    FIRE = 2
    WATER = 3
    ELECTRIC = 4
    GRASS = 5
    ICE = 6
    FIGHTING = 7
    POISON = 8
    GROUND = 9
    FLYING = 10
    PSYCHIC = 11
    BUG = 12
    ROCK = 13
    GHOST = 14
    DRAGON = 15
    DARK = 16
    STEEL = 17
    FAIRY = 18
    VOID = 19

class MoveCat(IntEnum):
    PHYSICAL = 1
    SPECIAL = 2
    STATUS = 3


class Move:
    def __init__(self, id, identifier, move_type, movecat, power, priority, accuracy=None, pp=None, effect=None, eff_chance=None, target = None, contact = False):
        self.id = id
        self.identifier = identifier
        self.move_type = move_type  
        self.movecat = movecat  
        self.power = power
        self.priority = priority
        self.accuracy = accuracy
        self.pp = pp
        self.effect = effect
        self.eff_chance = eff_chance 
        self.target = target
        self.contact = contact
        self.charge_counter = 0

    @classmethod
    def from_json(cls, identifier):
        with open(r"cogs\utils\moves.json", "r") as json_file:
            all_moves_data = json.load(json_file)
            for move_data in all_moves_data:
                if move_data['identifier'] == identifier:
                    return cls(
                        move_data['id'],
                        move_data['identifier'],
                        Type[move_data['type'].upper()],
                        MoveCat[move_data['category'].upper()],
                        move_data['power'],
                        move_data['priority'],
                        move_data.get('accuracy'), 
                        move_data.get('pp'),
                        move_data.get('effect'),
                        move_data.get('eff_chance'),
                        move_data.get('target'),
                        move_data.get('contact')
                        )
            return None

# class Ability:
#     def __init__(self, name, id) -> None:
#         self.name = name
#         self.id = id
#         self.nullified = False

class Status(IntEnum):
    healthy = 1
    paralyzed = 2
    burned = 3
    frozen = 4
    poisoned = 5
    badly_poisoned = 6
    asleep = 7
    fainted = 8

class SecondaryStatus:
    def __init__(self):
        self.flinch = False
        self.confused = False#todo
        self.infatuated = False#todo
        self.bounced = False
        self.underground = False 
        self.underwater = False
        self.fly = False
        self.disappeared = False

    def confusion_tick():
        ...

class Stage:
    def __init__(self) -> None:
        self.atk = 1
        self.defense = 1
        self.spa = 1
        self.spd = 1
        self.spe = 1

    def reset(self):
        self.atk = 1
        self.defense = 1
        self.spa = 1
        self.spd = 1
        self.spe = 1

    def increment(self, stat: str, n: int) -> str:
        if not hasattr(self, stat):
            return "Invalid stat in code"

        current_stage = getattr(self, stat)

        max_stage = 6
        min_stage = -6

        if current_stage == max_stage and n > 0:
            return f"Cannot raise {stat} any further."
        elif current_stage == min_stage and n < 0:
            return f"Cannot lower {stat} any further."

        possible_change = min(max_stage - current_stage, n) if n > 0 else max(min_stage - current_stage, n)

        setattr(self, stat, stagemul.get(current_stage + possible_change))

        if possible_change == 0:
            return "nothing happened..."
        elif abs(possible_change) == 1:
            change_desc = "slightly " + ("increased" if possible_change > 0 else "decreased")
        elif abs(possible_change) == 2:
            change_desc = "sharply " + ("increased" if possible_change > 0 else "decreased")
        else:
            change_desc = "drastically " + ("increased" if possible_change > 0 else "decreased")

        return f"\n{stat} {change_desc}."

class Monster:
    def __init__(self, name, natdex, level, moves: list[Move], type1: Type, type2: Type, ability, item, hp, atk, defense, spa, spd, spe):
        self.name = name
        self.natdex = natdex
        self.level = level
        self.moves = moves
        self.type1 = type1
        self.type2 = type2
        self.ability = ability
        self.item = item
        self.hp = hp
        self.atk = atk
        self.defense = defense
        self.spa = spa
        self.spd = spd
        self.spe = spe
        self.maxhp = hp
        self.owner = None

        self.stage = Stage()
        self.status = Status.healthy
        self.secstatus = SecondaryStatus()
        self.crrmv = None
        self.crrtar = None
        self.switch = None

        self.req_charge_rec = None
        self.choice_locked_move = None 

        self.protected = False
        self.heal_block = False
        self.protected_turn = 0
        self.sleep_turns = 0
        self.badly_poison_turns = 0
        self.turns_after_switch = 0
        self.turn_move_switch = False

    def reset(self):
        self.protected = False
        self.switch = None
        self.crrmv = None
        self.crrtar = None
        self.secstatus.flinch = False
        self.turn_move_switch = False

    def reset_on_switch(self):

        self.protected = False
        self.switch = None
        self.crrmv = None
        self.crrtar = None
        self.secstatus.flinch = False
        self.turn_move_switch = False


        self.req_charge_rec = None
        self.heal_block = False
        self.protected_turn = 0
        self.badly_poison_turns = 0
        self.turns_after_switch = 0
        self.choice_locked_move = None

        

    def set_status(self, status: Status):
        if status == Status.asleep:
            self.status = Status.asleep
            self.sleep_turns = random.randint(1, 4)  
            return f"\n{self.name} felt asleep!"
        elif self.status != Status.healthy:
            return f"\n{self.name} is already affected by {self.status.name.lower()} and cannot be {status.name.lower()}!"
        elif status == Status.paralyzed and (self.type1 == "Electric" or self.type2 == "Electric"):
            return f"\n{self.name} is immune to paralysis!"
        elif status == Status.burned and (self.type1 == "Fire" or self.type2 == "Fire"):
            return f"\n{self.name} is immune to burns!"
        elif (status == Status.poisoned or status == Status.badly_poisoned) and (self.type1 == "Steel" or self.type2 == "Steel"):
            return f"\n{self.name} is immune to poison!"
        elif (status == Status.poisoned or status == Status.badly_poisoned) and self.status == Status.burned:
            return f"\n{self.name} is already burned and cannot be poisoned!"
        elif status == Status.burned and self.status == Status.paralyzed:
            return f"\n{self.name} is already paralyzed and cannot be burned!"
        elif status == Status.paralyzed and (self.status == Status.poisoned or self.status == Status.badly_poisoned):
            return f"\n{self.name} is already poisoned and cannot be paralyzed!"
        else:
            self.status = status
            return f"\n{self.name} became {status.name}!"
        
        
    def sleep_tick(self) -> str:
        self.sleep_turns -= 1
        if self.sleep_turns <= 0:
            self.status = Status.healthy
            return f"\n{self.name} woke up!"
        else:
            return f"\n{self.name} is fast asleep!"
        
    def badly_poison_tick(self) -> str:
        self.badly_poison_turns += 1
        damage = self.maxhp * self.badly_poison_turns // 16 
        self.hp -= damage
        return f"\n{self.name} took {damage} from bad poison"


