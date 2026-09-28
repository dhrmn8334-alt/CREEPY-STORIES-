import os, json, random
import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_NAME = os.getenv("CHANNEL_NAME", "creepy-stories")
INTERVAL_MINUTES = int(os.getenv("INTERVAL_MINUTES", "60"))

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN missing. Add it in Replit Secrets.")

with open("stories.json", "r", encoding="utf-8") as f:
    STORIES = json.load(f)

SETTINGS_FILE = "guild_settings.json"
try:
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        SETTINGS = json.load(f)
except:
    SETTINGS = {}

def save_settings():
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(SETTINGS, f, ensure_ascii=False, indent=2)

def get_language(guild_id):
    return SETTINGS.get(str(guild_id), "ENGLISH")

def pick_story(language):
    return random.choice(STORIES[language])

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

async def post_story(channel, language):
    s = pick_story(language)
    message = f"👻 **{s['title']}**\n\n{s['text']}"
    # Split safely for Discord's 2000-character limit.
    for i in range(0, len(message), 1900):
        await channel.send(message[i:i+1900])

@tasks.loop(minutes=INTERVAL_MINUTES)
async def automatic_stories():
    for guild in bot.guilds:
        channel = discord.utils.get(guild.text_channels, name=CHANNEL_NAME)
        if channel:
            try:
                await post_story(channel, get_language(guild.id))
            except Exception as e:
                print("Post error:", e)

@automatic_stories.before_loop
async def before_loop():
    await bot.wait_until_ready()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} | Servers: {len(bot.guilds)}")
    try:
        await bot.tree.sync()
    except Exception as e:
        print("Command sync error:", e)
    if not automatic_stories.is_running():
        automatic_stories.start()

@bot.tree.command(name="language", description="Choose story language")
@app_commands.choices(language=[
    app_commands.Choice(name="🇬🇧 English", value="ENGLISH"),
    app_commands.Choice(name="🇮🇳 Hinglish", value="HINGLISH"),
    app_commands.Choice(name="🅿️ Punjabi", value="PUNJABI"),
])
async def language(interaction: discord.Interaction, language: app_commands.Choice[str]):
    SETTINGS[str(interaction.guild_id)] = language.value
    save_settings()
    await interaction.response.send_message(
        f"✅ Language set to **{language.name}**. Automatic creepy stories will use this language."
    )

@bot.tree.command(name="creepy", description="Post a random creepy story now")
async def creepy(interaction: discord.Interaction):
    await interaction.response.defer()
    await post_story(interaction.channel, get_language(interaction.guild_id))
    await interaction.followup.send("👻 Story posted!")

@bot.tree.command(name="creepy_settings", description="Show current language and interval")
async def creepy_settings(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"👻 Language: **{get_language(interaction.guild_id)}**\n"
        f"📢 Channel: **#{CHANNEL_NAME}**\n"
        f"⏰ Interval: **{INTERVAL_MINUTES} minutes**\n"
        f"📚 Stories: **105 per language (315 total)**"
    )

bot.run(TOKEN)
