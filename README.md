# 👻 Free Creepy Stories Bot — 315 Stories + Audio

No OpenAI API required.

- 105 English stories
- 105 Hinglish stories
- 105 Punjabi stories
- `/language` selects the language
- `/creepy` posts a random story immediately
- Every story has a **🔊 Listen Audio** button
- Audio is generated on demand and sent as an MP3
- Audio is cached locally so repeated listens are faster
- `/creepy_settings` shows settings
- Automatic posting every 60 minutes
- Only Discord bot token is required

## Setup
1. Create a Discord bot in Discord Developer Portal.
2. Invite it with `bot` + `applications.commands`.
3. Give View Channel and Send Messages permissions.
4. Put the bot token in Railway Variables (or Replit Secrets) as `DISCORD_TOKEN`.
5. Run `python bot.py`.

## Audio note
Audio generation needs an internet connection because the bot uses Microsoft Edge's online TTS service through the `edge-tts` Python package. No OpenAI API key is needed.

Do not share your Discord bot token.
