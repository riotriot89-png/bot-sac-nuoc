import os

import discord
from discord import app_commands


class Bot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        print(f"Bot online: {self.user}", flush=True)


bot = Bot()


@bot.tree.command(description="Kiểm tra bot có đang hoạt động không")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")


bot.run(os.environ["DISCORD_TOKEN"])
