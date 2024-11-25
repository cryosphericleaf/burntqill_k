from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont
import io
import traceback

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .battle import Battle
    from .pokemon import DuelPokemon
    from .trainer import Trainer

def get_sprite_image(name: str) -> Image.Image:
    try:
        normalized_name = name.lower().replace("_", "-").replace(" ", "-")
        sprite_path = f"cogs/pokemonduel/nsprites/{normalized_name}.png"
        sprite_img = Image.open(sprite_path)
        return sprite_img
    except FileNotFoundError:
        prefix = normalized_name.split("-")[0]
        sprite_path = f"cogs/pokemonduel/nsprites/{prefix}.png"
        try:
            sprite_img = Image.open(sprite_path)
            return sprite_img
        except FileNotFoundError:
            print(f"Sprite not found at {sprite_path}, using default")
            fallback_path = "cogs/pokemonduel/nsprites/a.png"
            return Image.open(fallback_path)

def get_misc_image(name: str) -> Image.Image:
    try:
        image_path = f"cogs/pokemonduel/misc/{name}.png"
        sprite_img = Image.open(image_path)
        return sprite_img
    except FileNotFoundError:
        print(f"image not found at {image_path}, using default")
        fallback_path = "cogs/pokemonduel/nsprites/a.png"
        return Image.open(fallback_path)

def draw_monster(battlefield, monster: DuelPokemon, position, spec, size):
    try:
        if monster.substitute == 0:
            sprite_img = get_sprite_image(monster._name) 
        else:
            sprite_img = get_misc_image("substitute").convert("RGBA")
        width, height = sprite_img.size
        aspect_ratio = width / height
        new_width = size
        new_height = int(new_width / aspect_ratio)
        if spec == "b":
            sprite_img = sprite_img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        sprite_img = sprite_img.resize(
            (new_width, new_height), Image.Resampling.NEAREST
        )

        battlefield.paste(sprite_img, position, sprite_img)
    except Exception as e:
        print(f"Failed to draw monster: {e}")

def draw_hp_bar(draw, monster: DuelPokemon, position, size):
    try:
        hp_bar_height = 24
        bar_padding = 3
        font_size = 16

        percentage = monster.hp / monster.starting_hp
        bar_length = int(percentage * size)

        base_y = position[1]
        hp_bar_base = [position[0], base_y, position[0] + size, base_y + hp_bar_height]
        draw.rectangle(hp_bar_base, fill=(255, 255, 255))

        hp_bar = [
            position[0] + bar_padding,
            base_y + bar_padding,
            position[0] + bar_length - bar_padding,
            base_y + hp_bar_height - bar_padding,
        ]
        hp_color = (
            (230, 28, 28)
            if percentage < 0.3
            else (232, 199, 14) if percentage < 0.6 else (0, 255, 0)
        )
        draw.rectangle(hp_bar, fill=hp_color)
        hp_text = f"{monster.hp}/{monster.starting_hp}"
        font = ImageFont.truetype("cogs/pokemonduel/misc/poppinsb.ttf", font_size)

        text_bbox = draw.textbbox((0, 0), hp_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        text_position = (
            position[0] + (size - text_width) // 2,  # center horizontally
            base_y + (hp_bar_height - text_height) // 2,  # center vertically
        )

        draw.text(text_position, hp_text, font=font, fill=(0, 0, 0))
    except Exception as e:
        print(f"Failed to draw HP bar: {e}")

SPRITE_WIDTH = 80
SPRITE_HEIGHT = 60

def draw_teams(base_image, indices, direction):
    try:
        width, height = base_image.size
        x_pos, y_pos = ((width - SPRITE_WIDTH, 0) if direction == "r" else (0, height - SPRITE_HEIGHT))
        for name in indices:
            sprite_img = get_sprite_image(name).resize((80, 60), Image.Resampling.NEAREST)
            base_image.paste(sprite_img, (x_pos, y_pos), sprite_img)

            if direction == "r":
                y_pos += SPRITE_HEIGHT
                if y_pos >= height:
                    y_pos = 0
                    x_pos -= SPRITE_WIDTH
            else:
                y_pos -= SPRITE_HEIGHT
                if y_pos < 0:
                    y_pos = height - SPRITE_HEIGHT
                    x_pos += SPRITE_WIDTH

            if (direction == "r" and x_pos < 0) or (
                direction == "l" and x_pos >= width
            ):
                print("Not enough space to add more sprites.")
                break
    except Exception as e:
        print(f"Failed to draw teams: {e}")

def get_weather_image(weather):
    weather_map = {
        "sun": "cogs/pokemonduel/misc/weather-sunnyday.png",
        "h-sun": "cogs/pokemonduel/misc/weather-sunnyday.png",
        "rain": "cogs/pokemonduel/misc/weather-raindance.png",
        "h-rain": "cogs/pokemonduel/misc/weather-raindance.png",
        "hail": "cogs/pokemonduel/misc/weather-hail.png",
        "sandstorm": "cogs/pokemonduel/misc/weather-sandstorm.png",
        "h-wind": "cogs/pokemonduel/misc/weather-strongwind.png",
    }
    try:
        if weather in weather_map:
            return Image.open(weather_map[weather]).convert("RGBA")
    except FileNotFoundError:
        print(f"Weather image {weather_map[weather]} not found.")
    return None

def get_terrain_image(terrain):
    terrain_map = {
        "grassy": "cogs/pokemonduel/misc/weather-grassyterrain.png",
        "electric": "cogs/pokemonduel/misc/weather-electricterrain.png",
        "psychic": "cogs/pokemonduel/misc/weather-psychicterrain.png",
        "misty": "cogs/pokemonduel/misc/weather-mistyterrain.png",
    }
    try:
        if terrain in terrain_map:
            return Image.open(terrain_map[terrain]).convert("RGBA")
    except FileNotFoundError:
        print(f"Weather image {terrain_map[terrain]} not found.")
    return None

def draw_rectangle(image: Image.Image, position: tuple, size: tuple, color: tuple):
    top_left = position
    bottom_right = (position[0] + size[0], position[1] + size[1])
    transparent_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    transparent_draw = ImageDraw.Draw(transparent_layer)
    transparent_draw.rectangle([top_left, bottom_right], fill=color)
    return Image.alpha_composite(image, transparent_layer)

def generate_field_image(battle: Battle):
    try:
        trainer1: Trainer = battle.trainer1
        trainer2: Trainer = battle.trainer2
        mon1 = trainer1.current_pokemon
        mon2 = trainer2.current_pokemon
        p1am = [mon._name for mon in trainer1.party if mon.hp > 0]
        p2am = [mon._name for mon in trainer2.party if mon.hp > 0]

        extratext = ""
        battlefield = Image.open(f"cogs/pokemonduel/misc/{battle.bg}.png").convert("RGBA")
        draw_obj = ImageDraw.Draw(battlefield)

        if battle.terrain.item:
            timg = get_terrain_image(battle.terrain.item)
            battlefield = timg
            draw_obj = ImageDraw.Draw(battlefield)
            extratext += f"- {battle.terrain.item} terrain\n"
        if battle.weather._weather_type != "":
            wimg = get_weather_image(battle.weather._weather_type)
            battlefield = wimg
            draw_obj = ImageDraw.Draw(battlefield)
            extratext += f"- {battle.weather._weather_type} weather\n"

        if battle.trick_room.active():
            extratext += f"- trick room\n"
        if battle.magic_room.active():
            extratext += f"- magic room\n"
        if battle.wonder_room.active():
            extratext += f"- wonder room\n"
        if battle.gravity.active():
            extratext += f"- gravity\n"

        font = ImageFont.truetype("cogs/pokemonduel/misc/poppinsb.ttf", 16)
        if extratext != "":
            draw_obj.text((10, 5), extratext, font=font, fill=(0, 0, 0))

        if trainer1.reflect.active():
            battlefield = draw_rectangle(battlefield, position=(140, 250), size=(230, 140), color=(255, 215, 0, 128))
        if trainer1.light_screen.active():
            battlefield = draw_rectangle(battlefield, position=(160, 270), size=(230, 140), color=(231, 84, 128, 128))

        if trainer1.sticky_web:
            webimg = get_misc_image("web").convert("RGBA")
            battlefield.paste(webimg, (140, 370), webimg)
        if trainer1.stealth_rock:
            rockimg = get_misc_image("rock1").convert("RGBA")
            battlefield.paste(rockimg, (140, 400), rockimg)
            battlefield.paste(rockimg, (180, 440), rockimg)
            battlefield.paste(rockimg, (230, 400), rockimg)
        if trainer1.spikes > 0:
            spikeimg = get_misc_image("caltrop").convert("RGBA")
            battlefield.paste(spikeimg, (150, 400), spikeimg)
            if trainer1.spikes > 1:
                battlefield.paste(spikeimg, (190, 410), spikeimg)
                if trainer1.spikes > 2:
                    battlefield.paste(spikeimg, (240, 400), spikeimg)

        if trainer1.toxic_spikes > 0:
            spikeimg = get_misc_image("poisoncaltrop").convert("RGBA")
            battlefield.paste(spikeimg, (155, 410), spikeimg)
            if trainer1.toxic_spikes > 1:
                battlefield.paste(spikeimg, (185, 400), spikeimg)

        draw_monster(battlefield, mon1, (90, 250), "b", 250)

        draw_monster(battlefield, mon2, (420, 100), "f", 240)
        if trainer2.reflect.active():
            battlefield = draw_rectangle(battlefield, position =  (370, 140), size = (210, 120), color = (255, 215, 0, 128))
        if trainer2.light_screen.active():
            battlefield = draw_rectangle(battlefield, position = (390, 160), size = (210, 120), color = (231, 84, 128, 128))

        if trainer2.sticky_web:
            webimg = get_misc_image("web").convert("RGBA")
            battlefield.paste(webimg, (470, 210), webimg)
        if trainer2.stealth_rock:
            rockimg = get_misc_image("rock1").convert("RGBA")
            battlefield.paste(rockimg, (470, 240), rockimg)
            battlefield.paste(rockimg, (510, 280), rockimg)
            battlefield.paste(rockimg, (560, 240), rockimg)
        if trainer2.spikes > 0:
            spikeimg = get_misc_image("caltrop").convert("RGBA")
            battlefield.paste(spikeimg, (480, 240), spikeimg)
            if trainer2.spikes > 1:
                battlefield.paste(spikeimg, (520, 250), spikeimg)
                if trainer2.spikes > 2:
                    battlefield.paste(spikeimg, (570, 240), spikeimg)
        if trainer2.toxic_spikes > 0:
            spikeimg = get_misc_image("poisoncaltrop").convert("RGBA")
            battlefield.paste(spikeimg, (485, 250), spikeimg)
            if trainer2.toxic_spikes > 1:
                battlefield.paste(spikeimg, (515, 240), spikeimg)

        draw_obj = ImageDraw.Draw(battlefield)

        draw_hp_bar(draw_obj, mon1, (110, 220), 200)
        draw_hp_bar(draw_obj, mon2, (440, 80), 190)

        draw_teams(battlefield, p1am, "l")
        draw_teams(battlefield, p2am, "r")

        img_buffer = io.BytesIO()
        battlefield.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        return img_buffer
    except Exception as e:
        print("error in FE")
        print(traceback.format_exc())
