import discord
from discord.ext import commands
from discord import app_commands
import json
import inspect
import qrcode
from io import BytesIO
import random
from typing import Optional
from main import QillBot
import datetime
import asyncio
import traceback
from .utils.timeutils import Timeconverter as Tc

class Call:
    def __init__(self, user1, channel1, user2, channel2):
        self.user1 = user1
        self.channel1 = channel1
        self.user2 = user2
        self.channel2 = channel2
        self.active = True

    async def transmit_message(self, message, sender):
        if sender == self.user1:
            await self.channel2.send(f"< {message}")
        else:
            await self.channel1.send(f"< {message}")

    async def end_call(self):
        self.active = False
        await self.channel1.send("The call has ended.")
        await self.channel2.send("The call has ended.")

waitlist = []  

class Misc(commands.Cog):
    """Uncategorized commands."""    
    
    def __init__(self, bot: QillBot):
        self.bot: QillBot = bot
        self.collection = self.bot.db['pokemon']

    @commands.hybrid_command(
        description='Send a message to a specified channel',
        help='Send a message to the specified channel with the provided text.'
    )
    @app_commands.describe(channel='The channel to send the message to', text='The text to send in the message')
    @commands.has_permissions(manage_messages=True)

    async def echo(self, ctx: commands.Context, channel: discord.TextChannel, *, text: str) -> None:
        try:
            
            text = discord.utils.escape_mentions(text)
            await channel.send(text)
            await ctx.send(f"Message `{text}` successfully delivered to {channel} channel!", ephemeral=True)

        except commands.CheckFailure:
            await ctx.send(f"You don't have the required permissions to use this command.")



    @commands.command(
        help='Fetch the raw embed by replying to a message with this command that contains and embed',
        description='Fetch the raw embed by replying to a message with this command that contains and embed'
    )
    async def fe(self, ctx: commands.Context) -> None:
        if not ctx.message.reference or not ctx.message.reference.message_id:
            await ctx.send("Please reply to a message from the bot to fetch its raw embed.")
            return

        try:
            original_message_id = ctx.message.reference.message_id
            original_message = await ctx.channel.fetch_message(original_message_id)
            raw_embed = None
            if original_message.embeds:
                raw_embed = original_message.embeds[0].to_dict()

            if raw_embed:
                embed_json = json.dumps(raw_embed, indent=2)
                if len(embed_json) <= 2000:
                    await ctx.send(f"```json\n{embed_json}\n```")
                else:
                    # If JSON is too long, send as a file 
                    file_content = BytesIO(embed_json.encode())
                    await ctx.send(file=discord.File(file_content, filename="raw_embed.json"))

            else:
                await ctx.send("The replied message does not contain any embed.")

        except Exception as e:
            print("Error:", e)
            await ctx.send(f"An error occurred while processing the command.\n ```py {e}```")

    @commands.hybrid_command(
        description='Generate a QR code!',
        help='Generate a QR code with the provided text or link and send it as an image.'
    )
    @app_commands.describe(content='The text or link to generate a QR code from.')
    async def qrcode(self, ctx: commands.Context, *, content: str) -> None:
        await ctx.defer()
        if not content:
            await ctx.send("Please provide some text or a link to generate a QR code.")
            return

        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(content)
            try:
                qr.make(fit=True)
            except qrcode.exceptions.DataOverflowError:
                await ctx.send("The data provided is too large to fit in a single QR code. Please provide less data.")
                return

            qr_image = qr.make_image(fill_color="black", back_color="white")

            buffer = BytesIO()
            qr_image.save(buffer, format="PNG", quality=95)
            buffer.seek(0)

            await ctx.send(file=discord.File(buffer, filename="qrcode.png"))

        except Exception as e:
            await ctx.send(f"An error occurred while generating the QR code: {str(e)}")


    @commands.hybrid_command(description="Randomly selects one of the given options.",help='Randomly selects one of the given options.\n Separate the items with commas `,`')
    @app_commands.describe(options="The options to choose from.")
    async def choose(self, ctx, *, options):
        options_list = options.split(",")
        options_list = [option.strip() for option in options_list]  # Remove leading/trailing spaces

        if len(options_list) < 2:
            await ctx.send("Please provide at least two options. ￣へ￣")
        else:
            choice = random.choice(options_list)
            await ctx.send(f"I'll choose {choice}.")


    @commands.hybrid_command(name="rep", description="+1 rep", help="+1 rep")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    @app_commands.describe(user="To whom you want to +1 rep.")
    @app_commands.guild_only()
    async def rep(self, ctx: commands.Context, user: discord.User):
        try:
            async with self.bot.conn.cursor() as cursor:
                query_select = """
                    SELECT rep FROM reputation WHERE server_id = ? AND user_id = ?;
                """
                query_update = """
                    UPDATE reputation SET rep = rep + 1 WHERE server_id = ? AND user_id = ?;
                """
                query_insert = """
                    INSERT INTO reputation (server_id, user_id, rep) VALUES (?, ?, ?);
                """
                query_dec = """
                    UPDATE reputation SET rep = rep - 1 WHERE server_id = ? AND user_id = ?;
                """

                server_id = ctx.guild.id
                await cursor.execute(query_select, (server_id, user.id))
                existing_rep = await cursor.fetchone()

                if existing_rep is not None:
                    if ctx.author == user:
                        await cursor.execute(query_dec, (server_id, user.id))
                        await ctx.send("-1     ¯\_(ツ)_/¯")
                        await self.bot.conn.commit()   
                        return
                    else:
                        await cursor.execute(query_update, (server_id, user.id))
                else:
                    await cursor.execute(query_insert, (server_id, user.id, 1))
                await ctx.send(f"{user.name} has gained +1 rep from {ctx.author.name}!")
            await self.bot.conn.commit()  
        except Exception as e:
            print(e)

    @commands.hybrid_command(name="reputation", aliases=["rept"], description="View the reputation of a user in this server", help="View the reputation of a user in this server")
    @app_commands.describe(user="The user whose reputation you want to view.")
    @app_commands.guild_only()
    async def reputation(self, ctx: commands.Context, user: Optional[discord.User]):
        try:
            async with self.bot.conn.cursor() as cursor:  
                query = """
                    SELECT rep FROM reputation WHERE server_id = ? AND user_id = ?;
                """
                server_id = ctx.guild.id
                user_id = user.id if user else ctx.author.id
                
                await cursor.execute(query, (server_id, user_id))
                rep = await cursor.fetchone()
        
                if rep is None:
                    await ctx.send("This user has no reputation. (NOT REALLY)")
                else:
                    await ctx.send(f"{rep['rep']} rep(s)")
        except Exception as e:
            print(e)
        print("e")


    @commands.hybrid_command(name='noticeme', help='...')
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def notice_me_senpai(self, ctx: commands.Context):

        gifs = [
            'https://i.alexflipnote.dev/500ce4.gif', 
            'https://tenor.com/view/senpai-notice-bite-sip-clingy-gif-5740206' 
        ]
   
        gif = random.choices(gifs, weights=[99, 1])[0]
        await ctx.send(gif)



    @commands.hybrid_command(name="sleep", description="Timeout self(command invoker) for the given time.", help="Timeout self(command invoker) for the given time")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @app_commands.describe(duration='Time duration for self timeout, example: 30m | 12hr | 12hr20m50s')
    async def sleep(self, ctx: commands.Context, duration: str):
        try:
            await ctx.defer()
            time_d: int = Tc.parse_time(duration)
            if time_d == 0:
                await ctx.send('invalid time input \n example: 30m | 12hr | 12hr20m50s')
            elif time_d < 86401:
                time_delta = datetime.timedelta(seconds=time_d)
                time_r = Tc.seconds_to_relative(time_d)
                await ctx.author.timeout(time_delta)
                await ctx.send(f"bye, see you in {time_r} ヾ(•_•`)o")
            else:
                await ctx.send("noooooo i won't let you ( ´･-･)ﾉ(._.`)")
        except discord.Forbidden:
            await ctx.send("Not able to timeout because I'm lower in role hierarchy or the user is administrator")


    @commands.hybrid_command(name='qpinfo', description='...', help='...')
    async def qpinfo(self, ctx: commands.Context):
        info = inspect.cleandoc(
            f"""
            **args:** `--ab` abilities, `--t` types, `--m` moves, `--hp`, `--atk`, `--def`, `--spatk`, `--spdef`, `--speed`
            - you can add `>` or `<` after stat name for greater than or lesser than 
                - example: `--atk< 100` attack lesser than 100, `--speed> 50` speed greater than 50
            - for multiple abilities, types or moves use comma separated values:
                - `,qp --t water,grass` 
                - `,qp --m protect,dark-pulse`
            **example usage:**
            - `,qp --ab levitate --t steel --speed< 100`
            - `,qp --speed> 130`
            - `,qp --t grass,water`
            - `,qp --m moonblast,dark-pulse`
            """
        )
        await ctx.send(info)



    @commands.command(name='qp', description='query pokemons based on type abilities, stats, moves etc (use qpinfo for detailed query formatting)', help='query pokemons based on type abilities, stats, moves etc (use qpinfo for detailed query formatting)')
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def query(self, ctx: commands.Context, *, args: str):
        try:
            pokemon_list = await self.parsepq(args)
            if pokemon_list:
                embed = discord.Embed(description=', '.join(pokemon_list), color=discord.Colour(0xffebf8))
                await ctx.send(embed=embed)
            else:
                await ctx.send("Found nothing.\nFor query format use `,qpinfo`")
        except discord.HTTPException as e:
            if e.code == 50035:
                await ctx.send("Too many results to send as message maybe specify more in your query...\nFor query format use `,qpinfo`")
        except Exception as e:
            await ctx.send("Found nothing.\nFor query format use `,qpinfo`")

    async def parsepq(self, args: str) -> list:
        args = args.split('--')
        filters = {}
        for arg in args[1:]:
            if arg:
                # Splitting and stripping leading/trailing whitespaces
                parts = arg.split(' ')
                key, values = parts[0].strip(), [v.strip() for v in ' '.join(parts[1:]).strip().split(',')] #forgot wwt
                if key == 'ab':
                    filters['abilities'] = {'$all': values}
                elif key == 't':
                    filters['types'] = {'$all': values}
                elif key == 'm':
                    filters['moves'] = {'$all': values}
                else:  # For stats
                    if '>' in key:
                        key = key.replace('>', '')
                        filters[key] = {'$gt': int(values[0])}
                    elif '<' in key:
                        key = key.replace('<', '')
                        filters[key] = {'$lt': int(values[0])}
                    else:
                        filters[key] = int(values[0])
                    
        if filters:
            results = self.collection.find(filters)
            pokemon_list = [f"{result['pokemon']}" async for result in results]
            return pokemon_list
        else: 
            return ['bad query','use `,qpinfo` for query formatting']
        

    @commands.command(name='dial')
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def dial(self, ctx: commands.Context):
        try:
            user_id = ctx.author.id
            channel_id = ctx.channel.id

            if any(user_id == uid for uid, _ in waitlist):
                await ctx.send("WAIT!...")
                return
            
            if waitlist:
                userf = random.choice(waitlist)
                waitlist.remove(userf)

                user2_id, channel2_id = userf
                
                call = Call(ctx.author, ctx.channel, self.bot.get_user(user2_id), self.bot.get_channel(channel2_id))

                await ctx.send(f"Connecting...")
                await asyncio.sleep(1)
                await self.handle_call(call)
            else:
                waitlist.append((user_id, channel_id))
                await ctx.send("There is no one active. You have been added to the waitlist. Waiting for a call...")

                try:
                    await asyncio.wait_for(asyncio.sleep(60), timeout=60) 
                except asyncio.TimeoutError:
                    pass

                if any(user_id == uid for uid, _ in waitlist):
                    waitlist.remove((user_id, channel_id))
                    await ctx.send("You have been removed from the waitlist due to inactivity.")
        except Exception as e:
            print(e)
            traceback.print_exc()


    async def handle_call(self, call: Call):
        await call.channel1.send("Call started!\nType 'end' to terminate the call.")
        await call.channel2.send("Call started!\nType 'end' to terminate the call.")

        try:
            while call.active:
                def check(m):
                    return m.channel in [call.channel1, call.channel2] and m.author in [call.user1, call.user2]

                message = await self.bot.wait_for('message', timeout=60.0, check=check)

                if message.content.lower() == "end":
                    await call.end_call()
                    return

                await call.transmit_message(message.content, message.author)
        except asyncio.TimeoutError:
            await call.end_call()

async def setup(bot: QillBot) -> None:
    await bot.add_cog(Misc(bot))
