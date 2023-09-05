import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime
from keep_alive import keep_alive
import requests
import os
import pytz
import logging

desired_timezone = pytz.timezone('Europe/Sofia')
voice_channel_id_time = 1147642751337377963
voice_channel_id_date = 1147635201145589941

intents = discord.Intents.all()
intents.members = True
intents.messages = True
intents.presences = False

bot = commands.Bot(command_prefix='$', intents=intents)

log_channel_id = 1048179434517176340

original_permissions = {}
lockdowned_role_names = ["Guild Members", "Members", "Shadow Family", "Talker", "Helpers", "LoL", "DsO", "GTA", "Paladins", "Valorant"]

keep_alive()

logging.basicConfig(filename='rate_limit.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

async def log_to_discord(channel_id, message):
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send(message)

@bot.event
async def on_ready():
    await log_to_discord(log_channel_id, f'Logged in as {bot.user.name} ({bot.user.id})')
    update_date.start()
    update_time.start()

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
                perms.use_soundboard = False
                if role.name in lockdowned_role_names:
                    await role.edit(permissions=perms)

        await log_to_discord(log_channel_id, f"{ctx.author.name} used lockdown command.")
    else:
        await log_to_discord(log_channel_id, "Only the server owner can use this command to lock down the server.")


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
                perms.use_soundboard = True

                if role.name in lockdowned_role_names:
                    await role.edit(permissions=perms)

        await log_to_discord(log_channel_id,"Server is unlocked. Permissions are reverted back.")
    else:
        await log_to_discord(log_channel_id, "Only the server owner can use this command to unlockdown the server.")

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

def log_rate_limit(message):
    with open('rate_limit_log.txt', 'a') as log_file:
        log_file.write(f'{datetime.now()} - {message}\n')

@tasks.loop(minutes=5)
async def update_time():
    try:
        current_time = datetime.now(desired_timezone).strftime("%H:%M")

        voice_channel_time = bot.get_channel(voice_channel_id_time)

        if voice_channel_time and isinstance(voice_channel_time, discord.VoiceChannel):
            new_name_time = f"Server Time: {current_time}"
            await voice_channel_time.edit(name=new_name_time)
            log_message = f'Voice channel name updated to "{new_name_time}"'
            await log_to_discord(log_channel_id, log_message)
            logging.info(log_message)

    except discord.HTTPException as e:
        if e.status == 429:
            log_message = f'Rate limit exceeded. Exception: {e}'
            logging.warning(log_message)
        else:
            log_message = f'An error occurred while updating time channel name: {e}'
            await log_to_discord(log_channel_id, log_message)
            logging.error(log_message)

@update_date.before_loop
async def before_update_date():
    await bot.wait_until_ready()

@update_time.before_loop
async def before_update_time():
    await bot.wait_until_ready()

api_secret = os.environ['api']

async def main():
    await bot.start(api_secret)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
