import discord 

waitlist = []  

class Call:
    def __init__(self, user1: discord.User, channel1: discord.TextChannel, user2: discord.User, channel2: discord.TextChannel):
        self.user1 = user1
        self.channel1 = channel1
        self.user2 = user2
        self.channel2 = channel2
        self.active = True

    async def transmit_message(self, message: discord.Message, sender: discord.User):
        if sender == self.user1:
            await self.channel2.send(f"< {message}")
        else:
            await self.channel1.send(f"< {message}")

    async def end_call(self):
        self.active = False
        await self.channel1.send("The call has ended.")
        await self.channel2.send("The call has ended.")
