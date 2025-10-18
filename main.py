import discord
from discord import app_commands, Interaction, Embed, ButtonStyle
from discord.ext import commands
from discord.ui import View, Button
from dotenv import load_dotenv
import os
import asyncio
import logging
from flask import Flask
from threading import Thread
from datetime import datetime

# ===========================
# 🔹 LOAD ENVIRONMENT
# ===========================
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ===========================
# 🔹 CONSTANTS
# ===========================
GUILD_ID = 1392741080033792191  # your main server
WELCOME_CHANNEL_ID = 1392755494879494245
VERIFY_CHANNEL_ID = 1392755437513871432
VERIFIED_ROLE_ID = 1392751633586327615

# ===========================
# 🔹 LOGGING
# ===========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord")

# ===========================
# 🔹 FLASK KEEP-ALIVE
# ===========================
app = Flask("")

@app.route("/")
def home():
    return "Bot is running!", 200

def run_web():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# ===========================
# 🔹 DISCORD BOT SETUP
# ===========================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ===========================
# 🔹 VERIFY BUTTON
# ===========================
class VerifyButton(Button):
    def __init__(self):
        super().__init__(label="✅ Verify", style=ButtonStyle.green, custom_id="verify_button")

    async def callback(self, interaction: Interaction):
        role = interaction.guild.get_role(VERIFIED_ROLE_ID)
        if not role:
            return await interaction.response.send_message("⚠️ Verified role not found.", ephemeral=True)

        if role in interaction.user.roles:
            await interaction.response.send_message("✅ You’re already verified!", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("🎉 You’ve been verified!", ephemeral=True)

class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(VerifyButton())

# ===========================
# 🔹 EVENTS
# ===========================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print("✅ Slash commands synced.")
    keep_alive()

    # Auto-post verify embed if not found
    channel = bot.get_channel(VERIFY_CHANNEL_ID)
    if channel:
        async for msg in channel.history(limit=20):
            if msg.author == bot.user and msg.components:
                break
        else:
            embed = Embed(
                title="🔒 Verification Required",
                description="Click the **Verify** button below to gain access to the server!",
                color=discord.Color.green(),
            )
            await channel.send(embed=embed, view=VerifyView())
            print("✅ Verification embed posted.")

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        embed = Embed(
            title="🎉 Welcome!",
            description=f"Welcome to **{member.guild.name}**, {member.mention}!",
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text="Enjoy your stay!")
        await channel.send(embed=embed)
        print(f"👋 Sent welcome for {member.name}")

# ===========================
# 🔹 SLASH COMMANDS
# ===========================
@tree.command(name="assign", description="Assign a role to a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(role="Role to assign", user="User to assign to")
async def assign(interaction: Interaction, role: discord.Role, user: discord.Member):
    await user.add_roles(role)
    await interaction.response.send_message(f"✅ Gave {role.mention} to {user.mention}")

@tree.command(name="purge", description="Delete a number of messages")
@app_commands.describe(amount="Number of messages to delete")
async def purge(interaction: Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)  # keeps the interaction alive
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 Deleted {len(deleted)} messages.", ephemeral=True)


@tree.command(name="poll", description="Create a poll", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(question="Question to ask")
async def poll(interaction: Interaction, question: str):
    embed = Embed(title="📊 Poll", description=question, color=discord.Color.blue())
    message = await interaction.channel.send(embed=embed)
    await message.add_reaction("✅")
    await message.add_reaction("❌")
    await interaction.response.send_message("✅ Poll created!", ephemeral=True)

@tree.command(name="post_verify", description="Manually post verification embed", guild=discord.Object(id=GUILD_ID))
async def post_verify(interaction: Interaction):
    embed = Embed(
        title="🔒 Verification Required",
        description="Click the **Verify** button below to gain access to the server!",
        color=discord.Color.green(),
    )
    await interaction.channel.send(embed=embed, view=VerifyView())
    await interaction.response.send_message("✅ Verification embed posted.", ephemeral=True)

# ===========================
# 🔹 RUN BOT
# ===========================
bot.run(TOKEN)
