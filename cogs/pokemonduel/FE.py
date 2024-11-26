from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont
import io
import traceback
from .temp import bundled_data_path

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .battle import Battle
    from .trainer import Trainer

def get_sprite_image(path, name: str) -> Image.Image:
    try:
        normalized_name = name.lower().replace("_", "-").replace(" ", "-")
        sprite_path = path / "nsprites" / f"{normalized_name}.png"
        sprite_img = Image.open(sprite_path)
        return sprite_img
    except FileNotFoundError:
        prefix = normalized_name.split("-")[0]
        sprite_path = path / "nsprites" / f"{prefix}.png"
        try:
            sprite_img = Image.open(sprite_path)
            return sprite_img
        except FileNotFoundError:
            print(f"Sprite not found at {sprite_path}, using default")
            fallback_path = path / "nsprites" / "a.png"
            return Image.open(fallback_path)

def get_misc_image(path, name: str) -> Image.Image:
    try:
        image_path = path / "misc" / f"{name}.png"
        sprite_img = Image.open(image_path).convert("RGBA")
        return sprite_img
    except FileNotFoundError:
        print(f"Image not found at {image_path}, using default")
        fallback_path = path / "nsprites" / "a.png"
        return Image.open(fallback_path).convert("RGBA")

def draw_screens(image: Image.Image, position: tuple, size: tuple, color: tuple):
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))  
    draw = ImageDraw.Draw(overlay)
    top_left = position
    bottom_right = (position[0] + size[0], position[1] + size[1])
    draw.rectangle([top_left, bottom_right], fill=color)
    image.alpha_composite(overlay)

#for team preview
def draw_teams(path, base_image, indices, direction):
    try:
        sprite_width = 80
        sprite_height = 60
        width, height = base_image.size
        x_pos, y_pos = ((width - sprite_width, 0) if direction == "r" else (0, height - sprite_height))
        for name in indices:
            sprite_img = get_sprite_image(path, name).resize((80, 60), Image.Resampling.NEAREST)
            base_image.paste(sprite_img, (x_pos, y_pos), sprite_img)
            if direction == "r":
                y_pos += sprite_height
            else:
                y_pos -= sprite_height
    except Exception as e:
        print(f"Failed to draw teams: {e}")

#for backgrounds with slightly differnet size
def get_scaled_positions(image_size: tuple):
    left_proportion_x = 0.12  
    left_proportion_y = 0.5  

    right_proportion_x = 0.6  
    right_proportion_y = 0.2  

    new_width, new_height = image_size
    scaled_left_x = left_proportion_x * new_width
    scaled_left_y = left_proportion_y * new_height

    scaled_right_x = right_proportion_x * new_width
    scaled_right_y = right_proportion_y * new_height

    return (int(scaled_left_x), int(scaled_left_y)), (int(scaled_right_x), int(scaled_right_y))

def generate_field_image(battle: Battle):
    try:
        path = bundled_data_path(battle.ctx.cog)
        font = ImageFont.truetype(path / "misc" / "poppinsb.ttf", 16)

        extratext = ""
        field = get_misc_image(path, battle.bg)
        draw = ImageDraw.Draw(field)

        if battle.terrain.item:
            timg = get_misc_image(path, battle.terrain.item)
            field = timg
            draw = ImageDraw.Draw(field)
            extratext += f"- {battle.terrain.item} terrain\n"
        if battle.weather._weather_type != "":
            wimg = get_misc_image(path, battle.weather._weather_type.split("-")[-1])
            field = wimg
            draw = ImageDraw.Draw(field)
            extratext += f"- {battle.weather._weather_type} weather\n"

        if battle.trick_room.active():
            extratext += f"- trick room\n"
        if battle.magic_room.active():
            extratext += f"- magic room\n"
        if battle.wonder_room.active():
            extratext += f"- wonder room\n"
        if battle.gravity.active():
            extratext += f"- gravity\n"

        if extratext != "":
            draw.text((10, 5), extratext, font=font, fill=(0, 0, 0))

        p1, p2 = get_scaled_positions(field.size)
        Side(path=path, field=field, trainer=battle.trainer1, position=p1, size=250, spec="l", behind_the_sprite=True).draw()
        Side(path=path, field=field, trainer=battle.trainer2, position=p2, size=200, spec="r", behind_the_sprite=False).draw()

        img_buffer = io.BytesIO()
        field.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        return img_buffer
    except Exception as e:
        print("error in FE")
        print(traceback.format_exc())


class Side:
    def __init__(self, path, field: Image.Image, trainer: Trainer, position: tuple, size: int, spec: str, behind_the_sprite: bool):
        self.path = path
        self.field = field
        self.trainer = trainer
        self.position = position
        self.size = size
        self.spec = spec
        self.behind_the_sprite = behind_the_sprite
        self.mon = trainer.current_pokemon

    def reflect_and_lightscreen(self):
        screen_position = (self.position[0] + (50 if self.spec == "l" else -50), self.position[1] + (0 if self.spec == "l" else 40))
        size = ((230, 140) if self.spec == "l" else (210, 120))
        if self.trainer.reflect.active():
            draw_screens(self.field, position=(screen_position[0], screen_position[1]), size=size, color=(255, 215, 0, 128))
        if self.trainer.light_screen.active():
            draw_screens(self.field, position=(screen_position[0]+20, screen_position[1]+20), size=size, color=(231, 84, 128, 128))

    def hazards(self):
        y_displace = [10, 20, 15]
        if self.trainer.sticky_web:
            webimg = get_misc_image(self.path, "web")
            self.field.paste(webimg, (self.position[0] + 50, self.position[1] + 110), webimg)
        if self.trainer.stealth_rock:
            rockimg = get_misc_image(self.path, "rock1")
            for i in range(3):
                self.field.paste(rockimg, (self.position[0] + 40 + (40*i), self.position[1] + 140 + (y_displace[i])), rockimg)
        if self.trainer.toxic_spikes > 0:
            toxic_img = get_misc_image(self.path, "poisoncaltrop")
            for i in range(self.trainer.toxic_spikes):
                self.field.paste(toxic_img, (self.position[0] + 60 + (20*i), self.position[1] + 140 + (y_displace[i])), toxic_img)
        if self.trainer.spikes > 0:
            spikes_img = get_misc_image(self.path, "caltrop")
            for i in range(min(self.trainer.spikes, 3)):
                self.field.paste(spikes_img, (self.position[0] + 70 + (20*i), self.position[1] + 160 + (y_displace[i])), spikes_img)

    def sprite(self):
        try:
            if self.trainer.current_pokemon.substitute == 0:
                sprite_img = get_sprite_image(self.path, self.trainer.current_pokemon._name) 
            else:
                sprite_img = get_misc_image(self.path, "substitute")
            width, height = sprite_img.size
            aspect_ratio = width / height
            new_width = self.size
            new_height = int(new_width / aspect_ratio)
            if self.spec == "l":
                sprite_img = sprite_img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            sprite_img = sprite_img.resize(
                (new_width, new_height), Image.Resampling.NEAREST
            )
            self.field.paste(sprite_img, self.position, sprite_img)
        except Exception as e:
            print(f"Failed to draw monster: {e}")

    def hp_bar(self):
        try:
            draw = ImageDraw.Draw(self.field)
            bar_height = 24
            bar_padding = 3

            percentage = self.mon.hp / self.mon.starting_hp
            bar_length = int(percentage * self.size)

            base_y = self.position[1] - 30
            hp_bar_base = [self.position[0], base_y, self.position[0] + self.size, base_y + bar_height]
            draw.rectangle(hp_bar_base, fill=(255, 255, 255))

            hp_bar = [
                self.position[0] + bar_padding,
                base_y + bar_padding,
                self.position[0] + bar_length - bar_padding,
                base_y + bar_height - bar_padding,
            ]
            hp_color = (
                (230, 28, 28)
                if percentage < 0.3
                else (232, 199, 14) if percentage < 0.6 else (0, 255, 0)
            )
            draw.rectangle(hp_bar, fill=hp_color)
            hp_text = f"{self.mon.hp}/{self.mon.starting_hp}"

            font = ImageFont.truetype(self.path / "misc" / "poppinsb.ttf", 16)
            text_bbox = draw.textbbox((0, 0), hp_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

            text_position = (
                self.position[0] + (self.size - text_width) // 2,  # center horizontally
                base_y + (bar_height - text_height) // 2,  # center vertically
            )

            draw.text(text_position, hp_text, font=font, fill=(0, 0, 0))
        except Exception as e:
            print(f"Failed to draw HP bar: {e}")

    def teams(self):
        try:
            indices = [mon._name for mon in self.trainer.party if mon.hp > 0]
            sprite_width = 80
            sprite_height = 60
            field_width, field_height = self.field.size
            x_pos, y_pos = ((field_width - sprite_width, 0) if self.spec == "r" else (0, field_height - sprite_height))
            for name in indices:
                sprite_img = get_sprite_image(self.path, name).resize((80, 60), Image.Resampling.NEAREST)
                self.field.paste(sprite_img, (x_pos, y_pos), sprite_img)

                if self.spec == "r":
                    y_pos += sprite_height
                else:
                    y_pos -= sprite_height
        except Exception as e:
            print(f"Failed to draw teams: {e}")

    def draw(self):
        actions = []
        if self.behind_the_sprite:
            actions = [self.hazards, self.reflect_and_lightscreen, self.sprite, self.hp_bar, self.teams]
        else:
            actions = [self.sprite, self.hazards, self.reflect_and_lightscreen, self.hp_bar, self.teams]

        for action in actions:
            action()
