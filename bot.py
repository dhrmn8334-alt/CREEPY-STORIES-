import os, json, random, hashlib
import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
import edge_tts

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_NAME = os.getenv("CHANNEL_NAME", "creepy-stories")
INTERVAL_MINUTES = int(os.getenv("INTERVAL_MINUTES", "60"))

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN missing. Add it in Railway Variables / Replit Secrets.")

with open("stories.json", "r", encoding="utf-8") as f:
    STORIES = json.load(f)

SETTINGS_FILE = "guild_settings.json"
try:
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        SETTINGS = json.load(f)
except Exception:
    SETTINGS = {}

AUDIO_DIR = "audio_cache"
os.makedirs(AUDIO_DIR, exist_ok=True)

# Microsoft Edge TTS voices. Punjabi and Hindi voices are used for Punjabi/Hinglish.
TTS_VOICES = {
    "ENGLISH": "en-US-GuyNeural",
    "HINGLISH": "hi-IN-MadhurNeural",
    "PUNJABI": "pa-IN-OjasNeural",
}


def save_settings():
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(SETTINGS, f, ensure_ascii=False, indent=2)


def get_language(guild_id):
    return SETTINGS.get(str(guild_id), "ENGLISH")


def pick_story(language):
    return random.choice(STORIES[language])


def story_message(story):
    return f"👻 **{story['title']}**\n\n{story['text']}"


def audio_path(language, story):
    key = f"{language}|{story['title']}|{story['text']}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]
    return os.path.join(AUDIO_DIR, f"{language.lower()}_{digest}.mp3")


async def make_audio(language, story):
    path = audio_path(language, story)
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return path

    voice = TTS_VOICES.get(language, TTS_VOICES["ENGLISH"])
    # Slightly slower delivery for a creepy-story feel.
    communicate = edge_tts.Communicate(
        story["text"],
        voice=voice,
        rate="-8%",
        volume="+0%",
        pitch="-2Hz",
    )
    await communicate.save(path)
    return path


class StoryAudioView(discord.ui.View):
    def __init__(self, language, story):
        super().__init__(timeout=600)
        self.language = language
        self.story = story

    @discord.ui.button(label="Listen Audio", emoji="🔊", style=discord.ButtonStyle.primary)
    async def listen_audio(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            path = await make_audio(self.language, self.story)
            await interaction.followup.send(
                content=f"🔊 **{self.story['title']}** — {self.language.title()} audio",
                file=discord.File(path, filename="creepy_story.mp3"),
                ephemeral=True,
            )
        except Exception as e:
            print("TTS error:", repr(e))
            await interaction.followup.send(
                "❌ Audio generate nahi ho saki. Thodi der baad dubara try karo.",
                ephemeral=True,
            )


intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


async def post_story(channel, language):
    story = pick_story(language)
    message = story_message(story)

    # Split safely for Discord's 2000-character limit. Put the audio button on the last part.
    chunks = [message[i:i + 1900] for i in range(0, len(message), 1900)]
    for index, chunk in enumerate(chunks):
        if index == len(chunks) - 1:
            await channel.send(chunk, view=StoryAudioView(language, story))
        else:
            await channel.send(chunk)


@tasks.loop(minutes=INTERVAL_MINUTES)
async def automatic_stories():
    for guild in bot.guilds:
        channel = discord.utils.get(guild.text_channels, name=CHANNEL_NAME)
        if channel:
            try:
                await post_story(channel, get_language(guild.id))
            except Exception as e:
                print("Post error:", repr(e))


@automatic_stories.before_loop
async def before_loop():
    await bot.wait_until_ready()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} | Servers: {len(bot.guilds)}")
    try:
        await bot.tree.sync()
    except Exception as e:
        print("Command sync error:", repr(e))
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
    await interaction.followup.send("👻 Story posted with 🔊 Listen Audio button!")


@bot.tree.command(name="creepy_settings", description="Show current language and interval")
async def creepy_settings(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"👻 Language: **{get_language(interaction.guild_id)}**\n"
        f"📢 Channel: **#{CHANNEL_NAME}**\n"
        f"⏰ Interval: **{INTERVAL_MINUTES} minutes**\n"
        f"📚 Stories: **105 per language (315 total)**\n"
        f"🔊 Audio: **Enabled**"
    )


bot.run(TOKEN)
