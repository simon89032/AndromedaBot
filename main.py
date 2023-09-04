import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime
import requests
from keep_alive import keep_alive
import os
import pytz

desired_timezone = pytz.timezone('Europe/Sofia')

intents = discord.Intents.default()
intents.members = True
intents.messages = True

bot = commands.Bot(command_prefix='$', intents=intents)

voice_channel_id = 1147642751337377963
voice_channel_id_date = 1147635201145589941
log_channel_id = 1048179434517176340

original_permissions = {}

hours = 0
minutes = 0
seconds = 0

async def log_to_discord(channel_id, message):
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send(message)

keep_alive()

@tasks.loop(hours=24)
async def update_date():
    current_date = datetime.now(desired_timezone).strftime('%A, %b %d')

    voice_channel_date = bot.get_channel(voice_channel_id_date)

    if voice_channel_date and isinstance(voice_channel_date, discord.VoiceChannel):
        new_name_date = f"{current_date}"
        try:
            await voice_channel_date.edit(name=new_name_date)
            await log_to_discord(log_channel_id, f'Voice channel name updated to "{new_name_date}"')
        except discord.HTTPException as e:
            if "rate limited" in str(e).lower():
                await log_to_discord(log_channel_id, 'Rate limit exceeded while updating date channel name. Waiting...')
            else:
                await log_to_discord(log_channel_id, f'An error occurred while updating date channel name: {e}')

@tasks.loop(minutes=5) 
async def update_time():
    current_time = datetime.now(desired_timezone).strftime("%H:%M")

    voice_channel_time = bot.get_channel(voice_channel_id)

    if voice_channel_time and isinstance(voice_channel_time, discord.VoiceChannel):
        new_name_time = f"Server Time: {current_time}"
        try:
            await voice_channel_time.edit(name=new_name_time)
            await log_to_discord(log_channel_id, f'Voice channel name updated to "{new_name_time}"')
        except discord.HTTPException as e:
            if "rate limited" in str(e).lower():
                await log_to_discord(log_channel_id, 'Rate limit exceeded while updating time channel name. Waiting...')
            else:
                await log_to_discord(log_channel_id, f'An error occurred while updating time channel name: {e}')

@update_date.before_loop
async def before_update_date():
    await bot.wait_until_ready()

@update_time.before_loop
async def before_update_time():
    await bot.wait_until_ready()

@bot.event
async def on_ready():
    await log_to_discord(log_channel_id, f'Logged in as {bot.user.name} ({bot.user.id})')
    update_date.start()
    update_time.start()
    await send_alive_message()

lockdowned_role_names = ["Guild Members", "Members", "Shadow Family", "Talker", "Helpers"]

async def on_error(event, *args, **kwargs):
    print(f"An error occurred in event {event}: {args[0]}")
  
async def send_alive_message():
    await bot.wait_until_ready()
    guild = bot.get_guild(1038062520512040993)
    channel = guild.get_channel(log_channel_id)

    while True:
        response = requests.get("https://python-test-bot.simeonmladenov.repl.co?")

        if response.status_code == 200:
            await channel.send("Bot is alive bitch!")
        else:
            await channel.send("Bot may not be running.")

        await asyncio.sleep(300)

@bot.command()
async def lockdown(ctx):
    if ctx.author.guild_permissions.administrator:
        for role in ctx.guild.roles:
            if role.name != "@everyone":
                original_permissions[role.id] = role.permissions

                perms = role.permissions
                perms.read_message_history = False
                perms.send_messages = False
                perms.manage_channels = False

                if role.name in lockdowned_role_names:
                    await role.edit(permissions=perms)

                log_message = f"{ctx.author.name} used lockdown command."
        await ctx.send(log_message)
    else:
        log_message = "Only the server owner can use this command to lock down the server."
        await ctx.send(log_message)

@bot.command()
async def unlockdown(ctx):
    if ctx.author.guild_permissions.administrator:
        for role in ctx.guild.roles:
            if role.name != "@everyone":
                original_permissions[role.id] = role.permissions

                perms = role.permissions
                perms.read_message_history = True
                perms.send_messages = True
                perms.manage_channels = True

                if role.name in lockdowned_role_names:
                    await role.edit(permissions=perms)

                log_message = "Server is unlocked. Permissions are reverted back."
        await ctx.send(log_message)
    else:
        log_message = "Only the server owner can use this command to unlockdown the server."
        await ctx.send(log_message)


@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel != after.channel:
        log_message = None

        if after.channel:
            log_message = f"{member.name} joined {after.channel.name}"
        if before.channel:
            log_message = f"{member.name} left {before.channel.name}"

        if log_message:
            log_message = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {log_message}"
            await log_to_discord(log_channel_id, log_message)  

@bot.event
async def on_message_delete(message):
    if message.attachments:
        for attachment in message.attachments:
            log_message = f"Deleted Image from {message.author}: {attachment.url}"
            await log_to_discord(log_channel_id, log_message) 

    if message.content:
        log_message = f"Deleted Message from {message.author}: {message.content}"
        await log_to_discord(log_channel_id, log_message) 

api_secret = os.environ['api']

async def main():
    await bot.start(api_secret)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
