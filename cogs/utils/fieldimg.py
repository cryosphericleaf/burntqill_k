from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont
import aiohttp
from typing import Literal, Optional
from .dtypes import  Monster, Weather
from io import BytesIO

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from field import Field

bgpath = r'cogs/assests/xywifi.jpg'
subpath = r'cogs/assests/sub.png'
rainpath = r'cogs/assests/rainbg.png'
sunpath = r'cogs/assests/sun.png'
snowpath = r'cogs/assests/snow.png'
sandpath = r'cogs/assests/sand.png'


class FieldImg:
    def __init__(self, field: Field) -> None:
        self.field = field

    def get_sprite_url(self, natdex_no, spec: Optional[Literal["f","b"]]):
        if spec not in ['f', 'b']:
            raise ValueError("Option must be either 'f' or 'b'")
        base_url = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon'
        if spec == 'b':
            url = f"{base_url}/back/{natdex_no}.png"
        else:
            url = f"{base_url}/{natdex_no}.png"
        return url
    
    async def get_sprite_bytes(self, mon: Monster):
        spec = 'b'
        if mon.owner == self.field.player2:
            spec = 'f'

        url = self.get_sprite_url(mon.natdex, spec)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    img_bytes = await response.read()
                    return img_bytes
                else:
                    with open(subpath, 'rb') as f:
                        img_bytes = f.read()
                    return img_bytes

                
    async def create_field_image(self):
        zpath = bgpath
        if self.field.crrw.weather == Weather.rain:
            zpath = rainpath
        elif self.field.crrw.weather == Weather.sun:
            zpath = sunpath
        elif self.field.crrw.weather == Weather.sand:
            zpath = sandpath
        elif self.field.crrw.weather == Weather.snow:
            zpath = snowpath

        battlefield = Image.open(zpath).convert("RGBA")
        draw = ImageDraw.Draw(battlefield)

        if self.field.player1.crrmon1:
            sprite1 =  await self.get_sprite_bytes(self.field.player1.crrmon1)
            pokemon1 = Pokemon(sprite1, self.field.player1.crrmon1.maxhp, self.field.player1.crrmon1.hp)
            battlefield = pokemon1.draw(draw, (80, 190), battlefield)
        if self.field.player1.crrmon2:
            sprite2 =  await self.get_sprite_bytes(self.field.player1.crrmon2)
            pokemon2 = Pokemon(sprite2, self.field.player1.crrmon2.maxhp, self.field.player1.crrmon2.hp)
            battlefield = pokemon2.draw(draw, (380, 240), battlefield)
        if self.field.player2.crrmon1:
            sprite3 = await self.get_sprite_bytes(self.field.player2.crrmon1)
            pokemon3 = Pokemon(sprite3, self.field.player2.crrmon1.maxhp, self.field.player2.crrmon1.hp)
            battlefield = pokemon3.draw(draw, (260, 40), battlefield)
        if self.field.player2.crrmon2:
            sprite4 = await self.get_sprite_bytes(self.field.player2.crrmon2)
            pokemon4 = Pokemon(sprite4, self.field.player2.crrmon2.maxhp, self.field.player2.crrmon2.hp)
            battlefield = pokemon4.draw(draw, (510, 70), battlefield)

     
            
        img_buffer = BytesIO()
        battlefield.save(img_buffer, format='png')
        img_buffer.seek(0)
        return img_buffer


class Pokemon:
    def __init__(self, sprite: bytes, max_hp: int, curr_hp: int, base_color='white'):
        self.sprite = sprite
        self.max_hp = max_hp
        self.curr_hp = curr_hp
        self.length = 170
        self.width = 18
        self.base_color = base_color
        self.image = self._resized_sprite(sprite)
        
    def _resized_sprite(self, sprite: bytes):
        sprite_image = Image.open(BytesIO(sprite)).convert("RGBA") ### conversion is imp for alpha composite
        resized_sprite = sprite_image.resize((200, 200))
    
        return resized_sprite
    
    def draw(self, draw, position, battlefield):
        x, y = position
        image_width = self.image.size[0]

        # Calculate the center position for HP text and HP bar
        center_x = x + image_width // 2
        bar_position = (center_x - self.length // 2, y - 7 - self.width)
        base_position = (center_x - self.length // 2, y - 7)

        # Draw Pokemon image on the battlefield
        battlefield.alpha_composite(self.image, (x, y))

        percentage = self.curr_hp / self.max_hp
        bar_length = int(self.length * percentage)
        color = 'lime'
        if percentage < 0.3:
            color = (230, 28, 28)
        elif percentage < 0.6:
            color = (232, 199, 14)

        # base of hp bar
        draw.rectangle([base_position, (base_position[0] + self.length, base_position[1] + 3)], fill=self.base_color)
        # HP bar
        draw.rectangle([bar_position, (bar_position[0] + bar_length, bar_position[1] + self.width)], fill=color)

        fpth = r"cogs/assests/poppinsb.ttf"  
        font_size = 18
        font = ImageFont.truetype(fpth, font_size)

        # Text of hp
        hp_text = f'{self.curr_hp}/{self.max_hp}'
        text_bbox = draw.textbbox((0, 0), hp_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        hp_text_position = (center_x - text_width // 2, bar_position[1] + self.width // 2 - text_height // 2)
        draw.text(hp_text_position, hp_text, fill='black', font=font)

        return battlefield