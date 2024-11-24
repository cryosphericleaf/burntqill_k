
from PIL import Image, ImageDraw, ImageFont
import io

class Monster:
    def __init__(self, name, max_hp, current_hp):
        if max_hp <= 0 or current_hp < 0 or current_hp > max_hp:
            raise ValueError("Invalid HP values for Monster.")
        self.name = name
        self.max_hp = max_hp
        self.current_hp = current_hp


class Player:
    def __init__(self, current_monster, alive_mons):
        if not isinstance(alive_mons, list) or not all(
            isinstance(mon, str) for mon in alive_mons
        ):
            raise ValueError("Alive monsters must be a list of strings.")
        self.current_monster = current_monster
        self.alive_mons = alive_mons


class Field:
    def __init__(self, player1, player2, weather):
        if weather not in {"sun", "h-sun", "rain", "h-rain", "hail", "sandstorm", "", None}:
            raise ValueError("Invalid weather condition.")
        self.player1 = player1
        self.player2 = player2
        self.weather = weather


def get_sprite_bytes(mon):
    try:
        normalized_name = mon.name.lower().replace("_", "-").replace(" ", "-")
        sprite_path = f"cogs/pokemonduel/nsprites/{normalized_name}.png"
        with open(sprite_path, "rb") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Sprite not found at {sprite_path}, attempting prefix fallback.")
        prefix = normalized_name.split("-")[0]
        sprite_path = f"cogs/pokemonduel/nsprites/{prefix}.png"
        try:
            with open(sprite_path, "rb") as f:
                return f.read()
        except FileNotFoundError:
            print(f"Sprite not found at {sprite_path}, using default fallback.")
            fallback_path = "cogs/pokemonduel/nsprites/a.png"
            with open(fallback_path, "rb") as fallback:
                return fallback.read()


def draw_monster(battlefield, monster, position, spec, size):
    try:
        sprite_bytes = get_sprite_bytes(monster)
        sprite_img = Image.open(io.BytesIO(sprite_bytes))
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


def draw_hp_bar(draw, monster, position, size):
    try:
        hp_bar_height = 24
        bar_padding = 3
        font_size = 16

        percentage = monster.current_hp / monster.max_hp
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
        hp_text = f"{monster.current_hp}/{monster.max_hp}"
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
        x_pos, y_pos = (
            (width - SPRITE_WIDTH, 0)
            if direction == "r"
            else (0, height - SPRITE_HEIGHT)
        )

        for name in indices:
            sprite_path = f"cogs/pokemonduel/nsprites/{name}.png"
            try:
                sprite_img = Image.open(sprite_path)
            except FileNotFoundError:
                prefix = name.split("-")[0]
                sprite_path = f"cogs/pokemonduel/nsprites/{prefix}.png"
                try:
                    sprite_img = Image.open(sprite_path)
                except FileNotFoundError:
                    sprite_img = Image.open("cogs/pokemonduel/nsprites/a.png")
            sprite_img = sprite_img.resize((80, 60), Image.Resampling.NEAREST)

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
        "h-wind": "cogs/pokemonduel/misc/weather-strongwind.png"
    }
    try:
        if weather in weather_map:
            return Image.open(weather_map[weather]).convert("RGBA")
    except FileNotFoundError:
        print(f"Weather image {weather_map[weather]} not found.")
    return None


def generate_field_image(battle):
    try:
        def format_pokemon_name(name):
            return name.lower().replace("_", "-").replace(" ", "-")
        mon1 = battle.trainer1.current_pokemon
        mon2 = battle.trainer2.current_pokemon
        p1am = [mon._name for mon in battle.trainer1.party if mon.hp > 0]
        p2am = [mon._name for mon in battle.trainer2.party if mon.hp > 0]

        player1 = Player(
            Monster(
                name=format_pokemon_name(mon1._name),
                max_hp=int(mon1.starting_hp),
                current_hp=int(mon1.hp),
            ),
            [format_pokemon_name(mon) for mon in p1am],
        )

        player2 = Player(
            Monster(
                name=format_pokemon_name(mon2._name),
                max_hp=mon2.starting_hp,
                current_hp=mon2.hp,
            ),
            [format_pokemon_name(mon) for mon in p2am],
        )

        field = Field(player1, player2, battle.weather._weather_type)

        battlefield = Image.open(f"cogs/pokemonduel/misc/{battle.bg}.png").convert("RGBA")
        if field.weather != "":
            wimg = get_weather_image(field.weather)
            battlefield = wimg
        draw_obj = ImageDraw.Draw(battlefield)

        draw_monster(battlefield, field.player1.current_monster, (90, 250), "b", 250)
        draw_monster(battlefield, field.player2.current_monster, (420, 100), "f", 240)

        draw_hp_bar(draw_obj, field.player1.current_monster, (110, 220), 200)
        draw_hp_bar(draw_obj, field.player2.current_monster, (440, 80), 190)

        draw_teams(battlefield, field.player1.alive_mons, "l")
        draw_teams(battlefield, field.player2.alive_mons, "r")

        img_buffer = io.BytesIO()
        battlefield.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        return img_buffer
    except Exception:
        pass
