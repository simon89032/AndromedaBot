import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime
import requests
import pytz
import logging

desired_timezone = pytz.timezone('Europe/Sofia')

intents = discord.Intents.all()
intents.members = True
intents.messages = True
intents.presences = False

bot = commands.Bot(command_prefix='$', intents=intents)

voice_channel_id_time = 1147642751337377963
voice_channel_id_date = 1147635201145589941
log_channel_id = 1148562977272905761

original_permissions = {}
lockdowned_role_names = ["Guild Members", "Members", "Shadow Family", "Talker", "Helpers", "LoL", "DsO", "GTA", "Paladins", "Valorant"]

### main log ###
bot_logger = logging.getLogger('bot')
bot_logger.setLevel(logging.INFO)

# Create a handler for the logger with the specified encoding
log_handler = logging.FileHandler('bot.log', encoding='utf-8')  # Use 'utf-8' encoding
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
bot_logger.addHandler(log_handler)


### rate limit ###
rate_limit_logger = logging.getLogger('rate_limit')
rate_limit_logger.setLevel(logging.WARNING)

rate_limit_file_handler = logging.FileHandler('log_rate_limit.txt')
rate_limit_file_handler.setLevel(logging.WARNING)

rate_limit_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
rate_limit_file_handler.setFormatter(rate_limit_formatter)

rate_limit_logger.addHandler(rate_limit_file_handler)

async def log_to_discord(channel_id, message):
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send(message)

@bot.command()
async def test(ctx):
    bot_logger.warning("test")
    
@bot.event
async def on_ready():
    await log_to_discord(log_channel_id, f'Logged in as {bot.user.name} ({bot.user.id})')
    update_date.start()
    update_time.start()
    await send_alive_message()

                
async def send_alive_message():
    await bot.wait_until_ready()
    guild = bot.get_guild(1038062520512040993)
    channel = guild.get_channel(log_channel_id)

    while True:
        response = requests.get("https://andromeda.simeonmladenov.repl.co/")

        if response.status_code == 200:
            await channel.send("Bot is alive bitch!")
        else:
            await channel.send("Bot may not be running.")

        await asyncio.sleep(600)

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
    current_datetime = datetime.now(desired_timezone)

    days_mapping = {"Monday": "Понеделник", "Tuesday": "Вторник", "Wednesday": "Сряда", "Thursday": "Четвъртък",
                    "Friday": "Петък", "Saturday": "Събота", "Sunday": "Неделя"}

    months_mapping = {"January": "Януари", "February": "Февруари", "March": "Март", "April": "Април", "May": "Май",
                      "June": "Юни", "July": "Юли", "August": "Август", "September": "Сеп", "October": "Окт",
                      "November": "Ноем", "December": "Дек"}

    voice_channel_date = bot.get_channel(voice_channel_id_date)

    if voice_channel_date and isinstance(voice_channel_date, discord.VoiceChannel):
        english_day = current_datetime.strftime('%A')
        english_month = current_datetime.strftime('%B')
        year = current_datetime.year

        bulgarian_day = days_mapping.get(english_day, english_day)
        bulgarian_month = months_mapping.get(english_month, english_month)

        if bulgarian_month in ["Септември", "Октомври", "Ноември", "Декември"]:
            bulgarian_month = bulgarian_month[:4]

        new_name_date = f"{bulgarian_day}, {bulgarian_month} {year}г"

        try:
            await voice_channel_date.edit(name=new_name_date)
            bot_logger.info(f'Voice channel name updated to "{new_name_date}"')
        except discord.HTTPException as e:
            log_message = 'Rate limit exceeded while updating date channel name. Waiting...' if "rate limited" in str(e).lower() else f'Error updating date channel name: {e}'
            rate_limit_logger.warning(log_message)


@tasks.loop(minutes=5)
async def update_time():
    try:
        current_time = datetime.now(desired_timezone).strftime("%H:%M")

        voice_channel_time = bot.get_channel(voice_channel_id_time)

        if voice_channel_time and isinstance(voice_channel_time, discord.VoiceChannel):
            new_name_time = f"Server Time: {current_time}"
            await voice_channel_time.edit(name=new_name_time)
            log_message = f'Voice channel name updated to "{new_name_time}"'
            bot_logger.info(log_message)

    except discord.HTTPException as e:
        if e.status == 429:
            log_message_rate = f'Rate limit exceeded. Exception: {e}'
            rate_limit_logger.warning(log_message_rate)
        else:
            log_message_error = f'An error occurred while updating time channel name: {e}'            
            bot_logger.error(log_message_error)

@update_date.before_loop
async def before_update_date():
    await bot.wait_until_ready()

@update_time.before_loop
async def before_update_time():
    await bot.wait_until_ready()

async def main():
    await bot.start("MTE0NjY3NDA2MDIyNzUzMDc2Mg.GCO_Vk.9BB5fQ6gKquZsVKNHLv7nwKYNpIbdrgfC00dUQ") # Simple Bot

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())