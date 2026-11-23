import os
import sqlite3
from contextlib import closing
from pathlib import Path

import discord
from discord import app_commands


# Lưu ngoài thư mục code để giữ các câu trả lời qua mỗi lần VPS cập nhật.
DATABASE = Path.home() / "autoreplies.sqlite3"


class Bot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        with closing(sqlite3.connect(DATABASE)) as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS autoreplies (
                    guild_id INTEGER NOT NULL,
                    keyword TEXT NOT NULL,
                    reply TEXT NOT NULL,
                    PRIMARY KEY (guild_id, keyword)
                )
            """)
            db.commit()

        await self.tree.sync()

    async def on_ready(self):
        print(f"Bot online: {self.user}", flush=True)

    async def on_message(self, message: discord.Message):
        if message.guild is None or message.author.bot:
            return

        keyword = message.content.strip().casefold()
        if not keyword:
            return

        with closing(sqlite3.connect(DATABASE)) as db:
            row = db.execute(
                "SELECT reply FROM autoreplies WHERE guild_id = ? AND keyword = ?",
                (message.guild.id, keyword),
            ).fetchone()

        if row:
            await message.channel.send(
                row[0],
                allowed_mentions=discord.AllowedMentions.none(),
            )


bot = Bot()


@bot.tree.command(description="Kiểm tra bot có đang hoạt động không")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")


@bot.tree.command(description="Đặt câu trả lời tự động cho một từ khóa")
@app_commands.guild_only()
@app_commands.default_permissions(manage_guild=True)
@app_commands.describe(
    tukhoa="Tin nhắn người dùng cần nhập để kích hoạt",
    noidung="Nội dung bot sẽ trả lời",
)
async def autoreply(
    interaction: discord.Interaction,
    tukhoa: app_commands.Range[str, 1, 200],
    noidung: app_commands.Range[str, 1, 2000],
):
    if not interaction.permissions.manage_guild:
        await interaction.response.send_message(
            "Bạn cần quyền Quản lý máy chủ để dùng lệnh này.",
            ephemeral=True,
        )
        return

    keyword = tukhoa.strip().casefold()
    reply = noidung.strip()
    if not keyword or not reply:
        await interaction.response.send_message(
            "Từ khóa và nội dung trả lời phải có chữ.",
            ephemeral=True,
        )
        return

    with closing(sqlite3.connect(DATABASE)) as db:
        db.execute(
            """
            INSERT INTO autoreplies (guild_id, keyword, reply)
            VALUES (?, ?, ?)
            ON CONFLICT (guild_id, keyword)
            DO UPDATE SET reply = excluded.reply
            """,
            (interaction.guild_id, keyword, reply),
        )
        db.commit()

    await interaction.response.send_message(
        "Đã lưu câu trả lời tự động.",
        ephemeral=True,
    )


bot.run(os.environ["DISCORD_TOKEN"])
