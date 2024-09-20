import discord 
import json 
from discord.ext import commands
from main import QillBot
from .utils.dtypes import Move, Monster, Type
from .utils.player import Player
from .utils.field import Field
import traceback

nature_effects = {
    "adamant": {"atk": 1.1, "defe": 1.0, "spa": 0.9, "spd": 1.0, "spe": 1.0, "hp": 1.0},
    "bashful": {"atk": 1.0, "defe": 1.0, "spa": 1.0, "spd": 1.0, "spe": 1.0, "hp": 1.0},  # Neutral nature
    "bold": {"atk": 0.9, "defe": 1.1, "spa": 1.0, "spd": 1.0, "spe": 1.0, "hp": 1.0},
    "brave": {"atk": 1.1, "defe": 1.0, "spa": 1.0, "spd": 1.0, "spe": 0.9, "hp": 1.0},
    "calm": {"atk": 0.9, "defe": 1.0, "spa": 1.0, "spd": 1.1, "spe": 1.0, "hp": 1.0},
    "careful": {"atk": 1.0, "defe": 1.0, "spa": 0.9, "spd": 1.1, "spe": 1.0, "hp": 1.0},
    "docile": {"atk": 1.0, "defe": 1.0, "spa": 1.0, "spd": 1.0, "spe": 1.0, "hp": 1.0},  # Neutral nature
    "gentle": {"atk": 1.0, "defe": 0.9, "spa": 1.0, "spd": 1.1, "spe": 1.0, "hp": 1.0},
    "hardy": {"atk": 1.0, "defe": 1.0, "spa": 1.0, "spd": 1.0, "spe": 1.0, "hp": 1.0},  # Neutral nature
    "hasty": {"atk": 1.0, "defe": 0.9, "spa": 1.0, "spd": 1.0, "spe": 1.1, "hp": 1.0},
    "impish": {"atk": 1.0, "defe": 1.1, "spa": 0.9, "spd": 1.0, "spe": 1.0, "hp": 1.0},
    "jolly": {"atk": 1.0, "defe": 1.0, "spa": 1.0, "spd": 1.0, "spe": 1.1, "hp": 1.0},
    "lax": {"atk": 1.0, "defe": 1.1, "spa": 1.0, "spd": 0.9, "spe": 1.0, "hp": 1.0},
    "lonely": {"atk": 1.1, "defe": 0.9, "spa": 1.0, "spd": 1.0, "spe": 1.0, "hp": 1.0},
    "mild": {"atk": 1.1, "defe": 0.9, "spa": 1.1, "spd": 1.0, "spe": 1.0, "hp": 1.0},
    "modest": {"atk": 0.9, "defe": 1.0, "spa": 1.1, "spd": 1.0, "spe": 1.0, "hp": 1.0},
    "naive": {"atk": 1.0, "defe": 0.9, "spa": 1.0, "spd": 1.0, "spe": 1.1, "hp": 1.0},
    "naughty": {"atk": 1.1, "defe": 0.9, "spa": 1.0, "spd": 1.0, "spe": 1.0, "hp": 1.0},
    "quiet": {"atk": 0.9, "defe": 1.0, "spa": 1.1, "spd": 1.0, "spe": 0.9, "hp": 1.0},
    "rash": {"atk": 1.0, "defe": 1.0, "spa": 1.1, "spd": 0.9, "spe": 1.0, "hp": 1.0},
    "relaxed": {"atk": 1.0, "defe": 1.1, "spa": 1.0, "spd": 1.0, "spe": 0.9, "hp": 1.0},
    "sassy": {"atk": 1.0, "defe": 1.0, "spa": 1.0, "spd": 1.1, "spe": 0.9, "hp": 1.0},
    "timid": {"atk": 0.9, "defe": 1.0, "spa": 1.0, "spd": 1.0, "spe": 1.1, "hp": 1.0},
}

async def json_to_player(json_data):
    try:
        if isinstance(json_data, str):
            player_data = json.loads(json_data)
        elif isinstance(json_data, dict):
            player_data = json_data
        else:
            raise ValueError("Input must be a JSON string or a dictionary")

        monsters_data = player_data
        monsters = []

        for i in range(1, 5):
            monster_key = str(i)
            monster_value = monsters_data[monster_key]
            moves = []
            for move_identifier in monster_value["moves"]:
                move = Move.from_json(move_identifier) 
                if move:
                    moves.append(move)

            monster = Monster(
                monster_value["name"],
                monster_value["natdex"],
                monster_value["level"],
                moves,
                Type[monster_value["type1"].upper()],  
                Type[monster_value["type2"].upper()] if monster_value["type2"] else None, 
                monster_value["ability"],
                monster_value["item"],
                monster_value["hp"],
                monster_value["atk"],
                monster_value["defense"],
                monster_value["spa"],
                monster_value["spd"],
                monster_value["spe"],
            )
            monsters.append(monster)

        player = Player(
            player_data["nick"],
            player_data["user"],
            monsters
        )

        return player

    except Exception as e:
        traceback.print_exc()
        print("error in json_to_player:", e)
        return None


class Accview(discord.ui.View):
    def __init__(self, ctx: commands.Context, bot: QillBot, player1: int, player2: int):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.bot = bot 
        self.c = self.bot.db['player']
        self.player1 = player1
        self.player2 = player2

    @discord.ui.button(label='A', style=discord.ButtonStyle.green)
    async def e(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            p1 = None
            p2 = None
            if interaction.user.id == self.player2:
                p1_data = await self.c.find_one({"user": str(self.player1)})
                p2_data = await self.c.find_one({"user": str(self.player2)})
                if p1_data and p2_data:
                    p1 = await json_to_player(p1_data)
                    p2 = await json_to_player(p2_data)
                    ch = interaction.channel
                    await interaction.response.edit_message(content="ok", view=None)
                    field = Field(ch, p1, p2)
                    await field.start(ch)
            
        except Exception as e:
            traceback.print_exc()
            print("error:", e)

    

class Doubles(commands.Cog):
    def __init__(self, bot: QillBot):
        self.bot: QillBot = bot
        self.collection = self.bot.db['pokemon']
        self.collectionp = self.bot.db['player']

    def get_nature_multiplier(self, nature, stat):
        nature = nature.lower()  
        if nature in nature_effects and stat in nature_effects[nature]:
            return nature_effects[nature][stat]
        else:
            return 1.0  

    async def get_pokemon_stats(self,pokemon_name):
        pokemon_data = await self.collection.find_one({"pokemon": pokemon_name.lower()})
        if pokemon_data:
            base_stats = {
                "hp": pokemon_data.get("hp"),
                "atk": pokemon_data.get("atk"),
                "defe": pokemon_data.get("def"),
                "spa": pokemon_data.get("spatk"),
                "spd": pokemon_data.get("spdef"),
                "spe": pokemon_data.get("speed")
            }
            return base_stats
        else:
            return None
    
    @commands.command(name = 'testd')
    async def doubles(self, ctx: commands.Context, user: discord.User):
        p1 = ctx.author.id
        p2 = user.id 
        view = Accview(ctx, self.bot, p1, p2)
        await ctx.send("ready for testin?", view=view)

    @commands.command(name = 'load')
    async def load(self, ctx: commands.Context, *,teaM: str):
        
        try:
            pokemon_sections = teaM.strip().split('\n\n')
            processed_sections = [f"{section}\n end " for section in pokemon_sections[:-1]]
            processed_sections.append(pokemon_sections[-1])  

            team: str = '\n\n'.join(processed_sections)
            team_data = {}
            team =  team.strip().replace("\n", "").lower().split()
            for k in range(1, 5):
                name = None
                item = None
                ability = None
                move1 = None
                move2 = None
                move3 = None
                move4 = None
                name = team[0]
                if team[1] == "@":
                    item = team[2]+"-"+team[3] if team[4] == "ability:" else team[2]
                else:
                    item = "none"
                nature = "none"
                try:
                    nature = team[team.index("nature")-1] 
                except Exception as e:
                    nature = "bashful"
                
                abs = team.index("ability:")
                abe = team.index("tera")
                if abe - abs == 3:
                    ability = team[abs + 1] + "-" + team[abs + 2]
                else:
                    ability = team[abs + 1]
                
                try:
                    subev_array = team[team.index("evs:"):team.index("-")]
                except ValueError:
                    await ctx.send('did ya forgot to put evs?? or maybe there is some other problem in your data')
                    break
            
                hpev_index = subev_array.index("hp") - 1 if "hp" in subev_array else None
                atkev_index = subev_array.index("atk") - 1 if "atk" in subev_array else None
                defev_index = subev_array.index("def") - 1 if "def" in subev_array else None
                spaev_index = subev_array.index("spa") - 1 if "spa" in subev_array else None
                spdev_index = subev_array.index("spd") - 1 if "spd" in subev_array else None
                speev_index = subev_array.index("spe") - 1 if "spe" in subev_array else None

                hpev = int(subev_array[hpev_index]) if hpev_index is not None else 0
                atkev = int(subev_array[atkev_index]) if atkev_index is not None else 0
                defev = int(subev_array[defev_index]) if defev_index is not None else 0
                spaev = int(subev_array[spaev_index]) if spaev_index is not None else 0
                spdev = int(subev_array[spdev_index]) if spdev_index is not None else 0
                speev = int(subev_array[speev_index]) if speev_index is not None else 0
                if 'end' in team:
                    sub_moves = team[team.index("-"):team.index("end")]
                else:
                    sub_moves = team[team.index('-'):]
                dash_count = sub_moves.count('-')
                if dash_count != 4:
                    break
            
                i = 0
                while i < len(sub_moves):
                    move = sub_moves[i]
                    
                    if move == '-':
                        i += 1
                        continue  
                    
                    if i + 1 < len(sub_moves) and sub_moves[i + 1] != '-':
                        move = f"{move}-{sub_moves[i + 1]}"
                        i += 1  

                    if move1 is None:
                        move1 = move
                    elif move2 is None:
                        move2 = move
                    elif move3 is None:
                        move3 = move
                    elif move4 is None:
                        move4 = move
                    else:
                        break  

                    i += 1

                if 'end' in team:
                    eindex = team.index("end")
                    team = team[eindex + 1:]

                stats = await self.get_pokemon_stats(name)
                
                hp = 2 * stats.get("hp") + (110 + 31 +(hpev/4))
                atk = ((31 + 2 * stats.get("atk") + (atkev/4) * 100/100) + 5) * self.get_nature_multiplier(nature, "atk")
                defe = ((31 + 2 * stats.get("defe") + (defev/4) * 100/100) + 5) * self.get_nature_multiplier(nature, "defe")
                spa = ((31 + 2 * stats.get("spa") + (spaev/4) * 100/100) + 5) * self.get_nature_multiplier(nature, "spa")
                spd = ((31 + 2 * stats.get("spd") + (spdev/4) * 100/100) + 5) * self.get_nature_multiplier(nature, "spd")
                spe = ((31 + 2 * stats.get("spe") + (speev/4) * 100/100) + 5) * self.get_nature_multiplier(nature, "spe")

                data = await self.collection.find_one({"pokemon": name.lower()})
            
                dexno = data.get('dexno')
                types = data.get('types', [])
                type1 = types[0] if types else None
                type2 = types[1] if len(types) > 1 else None
                team_data[str(k)] = {
                    "natdex": int(dexno),
                    "name": name,
                    "level": 100,
                    "type1": type1,
                    "type2": type2,
                    "status": "healthy",
                    "ability": ability,
                    "item": item,
                    "moves": [move1, move2, move3, move4],
                    "hp": round(hp),
                    "atk": round(atk),
                    "defense": round(defe),
                    "spa": round(spa),
                    "spd": round(spd),
                    "spe": round(spe)
                }
                
            team_data["nick"] = ctx.author.name
            team_data["user"] = str(ctx.author.id)
            if ability:
                existing_user = await self.collectionp.find_one({"user": str(ctx.author.id)})
                if existing_user:
                    await self.collectionp.replace_one({"user": str(ctx.author.id)},team_data)
                    await ctx.send('loaded your new team')
                else:
                    await self.collectionp.insert_one(team_data)
                    await ctx.send('loaded your new team')
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            await ctx.send("error occured, theres some problem in your data")



async def setup(bot: QillBot) -> None:
    await bot.add_cog(Doubles(bot))
