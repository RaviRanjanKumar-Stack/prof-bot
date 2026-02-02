from flask import Flask
import threading
import discord
from discord.ext import commands, tasks

# ======================
# CONFIG
# ======================
# -----------------------
# FLASK KEEP-ALIVE SERVER
# -----------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_web():
    app.run(host="0.0.0.0", port=10000)

def keep_alive():
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()
import os
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN not set in environment variables")
LOG_CHANNEL_NAME = "name-logs"
CHECK_INTERVAL_MINUTES = 2

# ======================
# INTENTS
# ======================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Store last known global display names
last_display_names = {}

# ======================
# EVENTS
# ======================
@bot.event
async def on_ready():
    print(f"Bot online: {bot.user}")

    # Force member cache to load
    for guild in bot.guilds:
        await guild.chunk()

    if not display_name_checker.is_running():
        display_name_checker.start()

# ======================
# HELPERS
# ======================
def get_global_name(member):
    return member.global_name or member.name

async def get_log_channel(guild):
    return discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)

# ======================
# SERVER NICKNAME TRACKING (INSTANT)
# ======================
@bot.event
async def on_member_update(before, after):
    # Only fires for server nickname changes
    if before.nick != after.nick:
        channel = await get_log_channel(after.guild)
        if not channel:
            return

        before_name = before.nick or before.name
        after_name = after.nick or after.name

        await channel.send(
            f"✏️ **Server Nickname Changed**\n"
            f"User: {after.mention}\n"
            f"Before: `{before_name}`\n"
            f"After: `{after_name}`"
        )

# ======================
# GLOBAL DISPLAY NAME TRACKING (POLLING LOOP)
# ======================
@tasks.loop(minutes=CHECK_INTERVAL_MINUTES)
async def display_name_checker():
    for guild in bot.guilds:
        channel = await get_log_channel(guild)
        if not channel:
            continue

        for member in guild.members:
            current = get_global_name(member)
            old = last_display_names.get(member.id)

            if old is None:
                last_display_names[member.id] = current
                continue

            if old != current:
                await channel.send(
                    f"🔄 **Global Display Name Changed**\n"
                    f"User: {member.mention}\n"
                    f"Before: `{old}`\n"
                    f"After: `{current}`"
                )
                last_display_names[member.id] = current

# Make sure loop starts only after bot is ready
@display_name_checker.before_loop
async def before_display_name_checker():
    await bot.wait_until_ready()
    print("Member cache ready. Starting global name checker...")

# ======================
# RUN
# ======================
keep_alive()
bot.run(TOKEN)
