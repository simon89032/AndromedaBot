import discord
from discord.ext import commands, tasks
import asyncio
import time
import logging
from datetime import datetime, timezone, timedelta

import pytz
desired_timezone = pytz.timezone('Europe/Sofia')

intents = discord.Intents.default()
intents.members = True
intents.messages = True

bot = commands.Bot(command_prefix='$', intents=intents)

voice_channel_id = 1147642751337377963
voice_channel_id_date = 1147635201145589941

original_permissions = {}
target_text_channel_id = 1048179434517176340
log_channel_id = 1048179434517176340

hours = 0
minutes = 0
seconds = 0

info_logger = logging.getLogger('info_logger')
info_logger.setLevel(logging.INFO)

warning_logger = logging.getLogger('warning_logger')
warning_logger.setLevel(logging.WARNING)

info_handler = logging.FileHandler('info.log')
warning_handler = logging.FileHandler('warning.log')

formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')

info_handler.setFormatter(formatter)
warning_handler.setFormatter(formatter)

info_logger.addHandler(info_handler)
warning_logger.addHandler(warning_handler)

@tasks.loop(hours=24)
async def update_date():
    current_date = datetime.now(desired_timezone).strftime('%A, %b %d')

    voice_channel_date = bot.get_channel(voice_channel_id_date)

    if voice_channel_date and isinstance(voice_channel_date, discord.VoiceChannel):
        new_name_date = f"{current_date}"
        try:
            await voice_channel_date.edit(name=new_name_date)
            info_logger.info(f'Voice channel name updated to "{new_name_date}"')
        except discord.HTTPException as e:
            if "rate limited" in str(e).lower():
                warning_logger.warning('Rate limit exceeded while updating date channel name. Waiting...')
            else:
                warning_logger.error(f'An error occurred while updating date channel name: {e}')

@tasks.loop(minutes=5) 
async def update_time():
    current_time = datetime.now(desired_timezone).strftime("%H:%M")

    voice_channel_time = bot.get_channel(voice_channel_id)

    if voice_channel_time and isinstance(voice_channel_time, discord.VoiceChannel):
        new_name_time = f"Server Time: {current_time}"
        try:
            await voice_channel_time.edit(name=new_name_time)
            info_logger.info(f'Voice channel name updated to "{new_name_time}"')
        except discord.HTTPException as e:
            if "rate limited" in str(e).lower():
                warning_logger.warning('Rate limit exceeded while updating time channel name. Waiting...')
            else:
                warning_logger.error(f'An error occurred while updating time channel name: {e}')

@update_date.before_loop
async def before_update_date():
    await bot.wait_until_ready()

@update_time.before_loop
async def before_update_time():
    await bot.wait_until_ready()

@bot.event
async def on_ready():
    info_logger.info(f'Logged in as {bot.user.name} ({bot.user.id})')
    update_date.start()
    update_time.start()

lockdowned_role_names = ["Guild Members", "Приятели", "Shadow Family", "Talker", "Helpers"]

@bot.command()
async def lockdown(ctx):
    log_message = None

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

        log_message = "Server is now locked down. Permissions have been modified."
    else:
        log_message = "Only an admin can use this command to lock down the server."

    log_message = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {log_message}"

    with open('chat.log', 'a') as log_file:
        log_file.write(log_message + '\n')

    await ctx.send(log_message)

@bot.command()
async def unlockdown(ctx):
    log_message = None

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
    else:
        log_message = "Only an admin can use this command to lock down the server."

    log_message = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {log_message}"

    with open('chat.log', 'a') as log_file:
        log_file.write(log_message + '\n')

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
            with open('chat.log', 'a') as log_file:
                log_file.write(log_message + '\n')

@bot.event
async def on_message_delete(message):
    if message.attachments:
        for attachment in message.attachments:
            log_message = f"Deleted Image from {message.author}: {attachment.url}"
            with open('chat.log', 'a') as log_file:
                log_file.write(log_message + '\n')

    if message.content:
        log_message = f"Deleted Message from {message.author}: {message.content}"
        with open('chat.log', 'a') as log_file:
            log_file.write(log_message + '\n')

async def main():
    await bot.start("")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
