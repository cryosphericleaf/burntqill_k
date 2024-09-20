# user_target_moves / self
### moves that do not have a single target

# adj_foe_moves / adj
### moves that include both foe

# all_adj_tar_moves / all adj 
### moves that includes all mons except the user 


from .dtypes import Type
tclr = {
    Type.NORMAL: 0xe6e8e6,
    Type.GRASS: 0x1fd11f,
    Type.WATER: 0x0477db,
    Type.FIRE: 0xdb2104,
    Type.DRAGON: 0x6707e6,
    Type.FLYING: 0xa8edec,
    Type.FIGHTING: 0x9c0000,
    Type.ELECTRIC: 0xf7e00c,
    Type.ICE: 0x25faef,
    Type.GROUND: 0xab4903,
    Type.GHOST: 0x5b3075,
    Type.PSYCHIC: 0xfc1287,
    Type.ROCK: 0xc96328,
    Type.POISON: 0x410754,
    Type.STEEL: 0x7d81b5,
    Type.DARK: 0x170e08,
    Type.FAIRY: 0xed82ed,
    Type.BUG: 0x7cb33e,
    Type.VOID: 0xe6e8e6
}

switch_moves = [
    "baton-pass", "chilly-reception", "flip-turn", "parting-shot", "shed-tail", "teleport", "u-turn", "volt-switch"
]

flinch_moves = {
    403: 30,
    310: 30,
    44: 30,
    125: 10,
    399: 20,
    407: 20,
    326: 10,
    252: 100,
    29: 30,
    531: 20,
    158: 10,
    556: 30,
    442: 30,
    302: 30,
    157: 30,
    27: 30,
    143: 30,
    173: 30,
    537: 30,
    23: 30,
    422: 10,#todo
    239: 20,
    127: 20,
    428: 20
}

pre_charge_moves = [
    340, 91, 291, 905, 19, 553, 601, 554, 800, 566, 13, 467, 130, 143, 507, 76, 669
]
