from utils import *
from config import *

import time
import traceback
import asyncio
import os

START_TIME = time.time()

# Jishaku config
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_HIDE"] = "True"

bot = commands.AutoShardedBot(
    command_prefix="!",
    intents=discord.Intents.all(),
    help_command=None
)

ignore = ["__pycache__", "utils.py", "config.py"]


async def load_cogs():

    loaded = 0
    failed = 0

    print("\n========== LOADING COGS ==========\n")

    for file in os.listdir("./Cogs"):

        if file.endswith(".py") and file not in ignore:

            name = f"Cogs.{file[:-3]}"

            try:
                await bot.load_extension(name)
                print(f"[✓] {file}")
                loaded += 1

            except Exception:
                print(f"[✗] {file}")
                traceback.print_exc()
                failed += 1

    print("\n----------------------------------")
    print(f"Loaded : {loaded}")
    print(f"Failed : {failed}")
    print("----------------------------------\n")


async def rotate_status():

    await bot.wait_until_ready()

    while not bot.is_closed():

        try:
            guild = bot.get_guild(ServerID)
            server_name = guild.name if guild else "Server"

            for activity in Activites:

                await bot.change_presence(
                    activity=discord.Activity(
                        type=discord.ActivityType.watching,
                        name=f"{activity} • {server_name}"
                    )
                )

                await asyncio.sleep(ActivityInterval)

        except Exception:
            traceback.print_exc()


@bot.event
async def setup_hook():
    await load_cogs()

    try:
        await bot.load_extension("jishaku")
        print("[✓] Jishaku Loaded")
    except Exception:
        print("[✗] Jishaku Failed")
        traceback.print_exc()


@bot.event
async def on_ready():

    startup_time = round(time.time() - START_TIME, 2)

    print("\n========== BOT STARTED ==========\n")

    print(f"User        : {bot.user}")
    print(f"ID          : {bot.user.id}")

    print("\n----------------------------------")

    print(f"Shard Count : {bot.shard_count or 1}")

    try:
        shard_ids = [shard_id for shard_id in bot.shards]
    except:
        shard_ids = []

    print(f"Shard IDs   : {shard_ids}")

    print("----------------------------------")

    guild = discord.Object(id=ServerID)

    bot.tree.copy_global_to(guild=guild)

    synced = await bot.tree.sync(guild=guild)

    commands_list = list(bot.tree.walk_commands())
    total_commands = len(commands_list)

    print(f"Synced Cmds : {len(synced)}")
    print(f"Total Cmds  : {total_commands}")
    print(f"Guild ID    : {ServerID}")

    print("----------------------------------")
    print(f"Startup Time: {startup_time}s")
    print("----------------------------------\n")

    if not hasattr(bot, "status_task"):
        bot.status_task = bot.loop.create_task(rotate_status())


@bot.event
async def on_shard_ready(shard_id):
    print(f"[Shard Ready] {shard_id}")


@bot.event
async def on_command_error(ctx, error):
    print("\n[Prefix Error]")
    traceback.print_exception(type(error), error, error.__traceback__)
    print("----------------------------------\n")


@bot.tree.error
async def on_app_command_error(interaction, error):

    print("\n[Slash Error]")
    traceback.print_exception(type(error), error, error.__traceback__)
    print("----------------------------------\n")

    try:
        if interaction.response.is_done():
            await interaction.followup.send("An error occurred.", ephemeral=True)
        else:
            await interaction.response.send_message("An error occurred.", ephemeral=True)
    except:
        pass


@bot.check
async def global_owner_only(ctx):
    return str(ctx.author.id) in botowner


bot.run(token=Token, reconnect=True)