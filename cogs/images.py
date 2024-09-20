import io
import discord
from PIL import Image, ImageDraw, ImageFont
from discord.ext import commands
from discord import app_commands
from typing import Optional
import aiohttp
from io import BytesIO
import textwrap



class Images(commands.Cog):
    """Image related commands."""
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def get_avatar_bytes(self, user: discord.User) -> bytes:
        async with aiohttp.ClientSession() as session:
            avatar_url = user.avatar.url
            async with session.get(avatar_url) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    raise Exception("Failed to fetch user avatar.")
                

    @app_commands.command(name='caption', description='Add a caption to an image')
    @app_commands.describe(caption_text='The caption text', attachment='The image attachment', link='The image link')
    async def add_caption(self, interaction: discord.Interaction, caption_text: str, attachment: Optional[discord.Attachment] = None, link: Optional[str] = None):
        await interaction.response.defer()

        if attachment and link:
            await interaction.response.send_message("Please provide either an attachment or a link, not both.")
            return

        if attachment:
            img_bytes = await attachment.read()
            original_extension = attachment.filename.split('.')[-1].lower()
            if original_extension not in ['jpg', 'jpeg', 'png', 'webp']:
                await interaction.response.send_message("The attachment must be an image file.")
                return
        elif link:
            async with aiohttp.ClientSession() as session:
                async with session.get(link) as resp:
                    img_bytes = await resp.read()
                    original_extension = link.split('.')[-1].lower().split('?')[0]
                    if original_extension not in ['jpg', 'jpeg', 'png', 'webp']:
                        await interaction.response.send_message("The link must point to an image file.")
                        return
        else:
            await interaction.response.send_message("Please attach an image or provide a link :>")
            return
    

        max_width = 800

 
        img = Image.open(io.BytesIO(img_bytes))


        if img.width > max_width:
            ratio = max_width / float(img.width)
            height_size = int(float(img.height) * float(ratio))
            img = img.resize((max_width, height_size), Image.ANTIALIAS)

        fpth = r"cogs/assests/caption.otf"
        font_size = 50
        font = ImageFont.truetype(fpth, font_size)
        max_width = img.width - 20
        max_chars_per_line = 25
        lines = [caption_text[i:i + max_chars_per_line] for i in range(0, len(caption_text), max_chars_per_line)]

        total_text_height = 0
        for line in lines:
            while font.getsize(line)[0] > max_width:
                font_size -= 1
                font = ImageFont.truetype(fpth, font_size)

            _, text_height = font.getsize(line)
            total_text_height += text_height

        # Set the height of the caption image dynamically based on the total text height with padding
        caption_padding = 20  
        caption_height = total_text_height + 2 * caption_padding
        new_height = img.height + caption_height

        caption_img = Image.new('RGB', (img.width, caption_height), 'white')
        caption_draw = ImageDraw.Draw(caption_img)

        font_size = 50
        font = ImageFont.truetype(fpth, font_size)

        current_height = caption_padding
        for line in lines:
            while font.getsize(line)[0] > max_width:
                font_size -= 1
                font = ImageFont.truetype(fpth, font_size)

            text_width, text_height = font.getsize(line)
            text_position = ((caption_img.width - text_width) // 2, current_height)
            caption_draw.text(text_position, line, fill='black', font=font)
            current_height += text_height

        new_img = Image.new('RGBA', (img.width, new_height), (255, 255, 255, 0))

        new_img.paste(caption_img, (0, 0))


        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            # The image has an alpha channel, can use it as mask
            new_img.paste(img, (0, caption_height), mask=img.split()[3])
        else:
            
            new_img.paste(img, (0, caption_height))

        output_image = io.BytesIO()
        new_img.save(output_image, format='png')
        output_image.seek(0)
        await interaction.followup.send(file=discord.File(output_image, f'meme.{original_extension}'))



    @commands.command(name="quote", description="Generate a quote image", help="Generate a quote.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def quote(self, ctx: commands.Context):
        await ctx.defer()
        
        if ctx.message.reference is not None:
            sm = await ctx.send("please wait...")
            replied_message: discord.Message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            quote = replied_message.content
            name = replied_message.author.name
            avatar_bytes = await self.get_avatar_bytes(replied_message.author)

            quote_image = await self.generate_quote_image(quote, name, avatar_bytes)
        
            image_bytes = BytesIO()
            quote_image.save(image_bytes, format="PNG")
            image_bytes.seek(0)

            await sm.edit(attachments=[discord.File(image_bytes, filename="quote.png")])
        else:
            await ctx.send('Use this command while replying to the message you want to make the quote image for')



    async def generate_quote_image(self, quote: str, name: str, avatar_bytes: bytes) -> Image.Image:
        width, height = 1000, 512
        _image = Image.new("RGB", (width, height), color="black")

        small_image = Image.open(BytesIO(avatar_bytes)).resize((512, 512))
        _image.paste(small_image, (0, 0))

        overlay_image_path = r"cogs/assests/qwww3.png"
        overlay_image = Image.open(overlay_image_path)
        _image.paste(overlay_image, (0, 0), mask=overlay_image)

        draw = ImageDraw.Draw(_image)

        font_size = 42
        font_path = r"cogs/assests/poppins.ttf"

      
        x_quote_center = 3 * width / 4  # Center of the right half
        y_quote = height / 2  # Vertical center of the image

        wrapped_quote = textwrap.fill(quote, width=20)
        wrapped_quote_lines = wrapped_quote.split('\n')  # Split the wrapped text into lines

        # Add the quote text
        font = ImageFont.truetype(font_path, font_size)
        total_text_height = sum(draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1] for line in wrapped_quote_lines)
        y_start = y_quote - total_text_height / 2
        for line in wrapped_quote_lines:
            text_bbox = draw.textbbox((0, 0), line, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            x_quote = x_quote_center - text_width / 2
            draw.text((x_quote, y_start), line, fill="white", font=font)
            y_start += text_height

         # Calculate position for the name
        name_font = ImageFont.truetype(font_path, font_size - 16)  
        name_text_bbox = draw.textbbox((0, 0), name, font=name_font)
        name_text_width = name_text_bbox[2] - name_text_bbox[0]
        x_name = x_quote_center - name_text_width / 2
        y_name = y_start + 20  # Space between quote and name

        draw.text((x_name, y_name), f"- {name}", fill="white", font=name_font)

        return _image

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Images(bot))
