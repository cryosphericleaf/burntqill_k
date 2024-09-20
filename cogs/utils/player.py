from __future__ import annotations
from .dtypes import Monster, Status
from typing import List
from typing import Any


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from field import Field

class Player:
    def __init__(self, nick, user, monsters: List[Monster]):
        self.nick = nick
        self.user = user
        self.monsters = monsters
        for mon in monsters:
            mon.owner = self
        self.crrmon1 = monsters[0]
        self.crrmon2 = monsters[1]

        self.stealth_rock = False

    def get_ally(self, mon: Monster) -> Monster:
        if mon == self.crrmon1:
            return self.crrmon2
        else:
            return self.crrmon1
        
    def set_mon_to_x(self, mon: Monster, x: Monster):
        if mon == self.crrmon1:
            self.crrmon1 = x
        else:
            self.crrmon2 = x

    def get_crrmon_num(self, mon: Monster) -> int:
        if mon == self.crrmon1:
            return 1
        else:
            return 2
        
    def get_crrmon(self, x: int) -> Monster:
        if x == 1:
            return self.crrmon1
        else:
            return self.crrmon2

    
    def switchable_mons(self, mon: Monster) -> List[Monster]:
        mons: List[Monster] = []
        for other_mon in self.monsters:
            if other_mon.status != Status.fainted and \
                    other_mon != self.crrmon1 and other_mon != self.crrmon2:
                if all(mon.switch != other_mon for mon in self.monsters):
                    mons.append(other_mon)
        return mons
