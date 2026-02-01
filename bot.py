import os
import json
import re
import discord
from discord.ext import commands

# ================= CONFIG =================

# Load token from environment variable (safe for hosting)
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("❌ DISCORD_TOKEN not found in environment variables")
    exit(1)

# Central server channel ID
CENTRAL_CHANNEL_ID = 1467484783771783248 # replace with your central channel

# Load triggers from JSON
try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        SPECIAL_MESSAGES = [msg.lower() for msg in config.get("special_messages", [])]
except Exception as e:
    print("❌ Error loading config.json:", e)
    exit(1)

# ================== BOT SETUP ==================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")


@bot.event
async def on_message(message):
    # ignore DMs only, allow bot messages
    if not message.guild:
        return

    # ================= trigger check =================
    content = message.content.lower().strip()

    # include embed content
    if message.embeds:
        for embed in message.embeds:
            if embed.title:
                content += " " + embed.title.lower()
            if embed.description:
                content += " " + embed.description.lower()
            for field in embed.fields:
                content += " " + field.name.lower() + " " + field.value.lower()
            if embed.footer:
                content += " " + embed.footer.text.lower()
            if embed.author:
                content += " " + embed.author.name.lower()

    # check if any trigger is present
    triggered = False
    matched_triggers = []
    for trigger in SPECIAL_MESSAGES:
        if re.search(re.escape(trigger), content):
            triggered = True
            matched_triggers.append(trigger)

    # debug prints
    if triggered:
        print(f"📩 Trigger detected in {message.guild.name} | Channel: {message.channel}")
        print(f"Message: {message.content}")
        print(f"Matched triggers: {matched_triggers}")

        # get central channel
        central_channel = bot.get_channel(CENTRAL_CHANNEL_ID)
        if not central_channel:
            print("❌ Central channel not found")
            return

        # create one-time invite
        try:
            invite = await message.channel.create_invite(
                max_age=3600,  # 1 hour
                max_uses=1,
                reason="Auto invite from relay bot"
            )
        except discord.Forbidden:
            await central_channel.send(
                f"❌ Missing invite permission in **{message.guild.name}**"
            )
            return

        # message link
        msg_link = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"

        # embed for central server
        embed = discord.Embed(
            title="🚨 New Server Trigger",
            color=discord.Color.orange()
        )
        embed.add_field(name="Server", value=message.guild.name, inline=False)
        embed.add_field(name="Channel", value=message.channel.mention, inline=False)
        embed.add_field(name="Author", value=message.author.mention, inline=False)
        embed.add_field(name="Message Link", value=msg_link, inline=False)
        embed.add_field(name="Invite Link", value=str(invite), inline=False)
        embed.add_field(name="Matched Triggers", value=", ".join(matched_triggers), inline=False)

        await central_channel.send(embed=embed)

    # allow commands to still work
    await bot.process_commands(message)


# ================== RUN BOT ==================
bot.run(TOKEN)
