import io
import json
import aiohttp
import discord
import inspect
from discord.ext import commands
from pathlib import Path
import json
from .buttons import BattlePromptView, PreviewPromptView

def bundled_data_path(cog_instance: commands.Cog) -> Path:
    """
    Get the path to the "data" directory bundled with this cog.

    The bundled data folder must be located alongside the ``.py`` file
    which contains the cog class.

    .. important::

        You should *NEVER* write to this directory.

    Parameters
    ----------
    cog_instance
        An instance of your cog. If calling from a command or method of
        your cog, this should be ``self``.

    Returns
    -------
    pathlib.Path
        Path object to the bundled data folder.

    Raises
    ------
    FileNotFoundError
        If no bundled data folder exists.

    """
    bundled_path = Path(inspect.getfile(cog_instance.__class__)).parent / "data"

    if not bundled_path.is_dir():
        raise FileNotFoundError("No such directory {}".format(bundled_path))

    return bundled_path

async def find(ctx, db, filter):
    """Fetch all matching rows from a data file."""
    path = str(bundled_data_path(ctx.cog) / db) + ".json"
    with open(path) as f:
        data = json.load(f)
    results = []
    for item in data:
        success = True
        for key, value in filter.items():
            if isinstance(value, dict):
                if "$nin" in value:
                    if item[key] in value["$nin"]:
                        success = False
                        break
            else:
                if item[key] != value:
                    success = False
                    break
        if success:
            results.append(item)
    return results

async def find_one(ctx, db, filter):
    """Fetch the first matching row from a data file."""
    results = await find(ctx, db, filter)
    if results:
        return results[0]
    return None

async def generate_team_preview(battle):
    """Generates a message for trainers to preview their team."""
    preview_view = PreviewPromptView(battle)
    await battle.channel.send("Select a lead pokemon:", view=preview_view)
    return preview_view

async def generate_main_battle_message(battle):
    """Generates a message representing the current state of the battle."""
    desc = ""
    
    if battle.weather._weather_type:
        desc += f"Weather: {battle.weather._weather_type.title()}\n" # TODO: pretty this output
    if battle.terrain.item:
        desc += f"Terrain: {battle.terrain.item.title()}\n" # TODO: pretty this output
    if battle.trick_room.active():
        desc += "Trick Room: Active\n"
    
    desc += "\n"
    desc += f"{battle.trainer1.name}'s {battle.trainer1.current_pokemon.name}\n"
    desc += f"  HP: {battle.trainer1.current_pokemon.hp}/{battle.trainer1.current_pokemon.starting_hp}\n"
    if battle.trainer1.current_pokemon.nv.current:
        desc += f"  Status: {battle.trainer1.current_pokemon.nv.current}\n"
    if battle.trainer1.current_pokemon.substitute:
        desc += "  Behind a substitute!\n"
    
    desc += "\n"
    desc += f"{battle.trainer2.name}'s {battle.trainer2.current_pokemon.name}\n"
    desc += f"  HP: {battle.trainer2.current_pokemon.hp}/{battle.trainer2.current_pokemon.starting_hp}\n"
    if battle.trainer2.current_pokemon.nv.current:
        desc += f"  Status: {battle.trainer2.current_pokemon.nv.current}\n"
    if battle.trainer2.current_pokemon.substitute:
        desc += "  Behind a substitute!\n"
    
    desc = f"```\n{desc.strip()}```"
    e = discord.Embed(
        title=f"Battle between {battle.trainer1.name} and {battle.trainer2.name}",
        description = desc,
    )
    e.set_footer(text="Who Wins!?")
    try: #aiohttp 3.7 introduced a bug in dpy which causes this to error when rate limited. This catch just lets the bot continue when that happens.
        img_data = await generate_field_picture(battle)
        battle_view = BattlePromptView(battle)
        if img_data:
            e = discord.Embed(title=f"Battle between {battle.trainer1.name} and {battle.trainer2.name}")
            file = discord.File(io.BytesIO(img_data), filename='field.png')
            e.set_image(url=f"attachment://{file.filename}")
            await battle.channel.send(embed=e, file=file,  view=battle_view)
        else:
            await battle.channel.send(embed=e, view=battle_view)
    except RuntimeError:
        pass
    return battle_view

async def generate_text_battle_message(battle):
    """
    Send battle.msg in a boilerplate embed.
    
    Handles the message being too long.
    """
    page = ""
    pages = []
    base_embed = discord.Embed()
    raw = battle.msg.strip().split("\n")
    for part in raw:
        if len(page + part) > 2000:
            embed = base_embed.copy()
            embed.description = page.strip()
            pages.append(embed)
            page = ""
        page += part + "\n"
    page = page.strip()
    if page:
        embed = base_embed.copy()
        embed.description = page
        pages.append(embed)
    for page in pages:
        await battle.channel.send(embed=page)
    battle.msg = ""


async def generate_field_picture(battle):
    try:
        mon1 = battle.trainer1.current_pokemon
        mon2 = battle.trainer2.current_pokemon
        p1am = []
        for mon in battle.trainer1.party:
            if mon.hp > 0:
                p1am.append(mon._name.lower())
        p2am = []
        for mon in battle.trainer2.party:
            if mon.hp > 0:
                p2am.append(mon._name.lower())
        payload = {
            "player1": {
                "alive_mons": p1am,
                "mon": {
                    "name": mon1._name,
                    "max_hp": int(mon1.starting_hp),
                    "current_hp": int(mon1.hp)
                }
            },
            "player2": {
                "alive_mons": p2am,
                "mon": {
                    "name": mon2._name,
                    "max_hp": int(mon2.starting_hp),
                    "current_hp": int(mon2.hp)
                }
            },
            "weather": battle.weather._weather_type
        }
        async with aiohttp.ClientSession() as session:
            async with session.post('http://localhost:3680/generate-field-image', json=payload) as response:
                if response.status == 200:
                    img_data = await response.read()
                    return img_data
                else:
                    print(f"Error: {response.status} - {await response.text()}")
                    return None
    except Exception as e:
        print("g-f-p", e)