from utils import *
from config import *
from Cogs.permission import admin_check
from Cogs.logger import log

import yaml
import sys
import os
import platform
import aiohttp
import asyncio
import subprocess
import threading
import zipfile
from datetime import datetime

SETTINGS_PATH = "settings.yaml"
START_TIME = datetime.utcnow()


# ===============================
# SETTINGS LOAD / SAVE
# ===============================

def load_settings():
    with open(SETTINGS_PATH) as f:
        return yaml.safe_load(f)


def save_settings(data):
    with open(SETTINGS_PATH, "w") as f:
        yaml.dump(data, f, sort_keys=False)


# ===============================
# RESTART SYSTEM
# ===============================

def restart_bot():

    python = sys.executable
    args = [python] + sys.argv

    try:
        subprocess.Popen(args)
    except:
        pass

    def relaunch():
        try:
            subprocess.Popen(args)
        except:
            pass

    try:
        threading.Thread(target=relaunch).start()
    except:
        pass

    try:
        os.execv(python, args)
    except:
        pass

    try:
        os.execl(python, python, *sys.argv)
    except:
        pass

    try:
        os._exit(0)
    except:
        pass


class Setup(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.weekly_backup.start()


# ===============================
# AUTOCOMPLETE
# ===============================

    async def setting_keys(self, interaction: discord.Interaction, current: str):

        data = load_settings()

        return [
            app_commands.Choice(name=k, value=k)
            for k in data.keys()
            if current.lower() in k.lower()
        ][:25]


# ===============================
# SETSETTING
# ===============================

    @app_commands.command(name="setsetting")
    @app_commands.autocomplete(key=setting_keys)
    async def setsetting(self, interaction: Interaction, key: str, value: str):

        if not admin_check(interaction):
            return await interaction.response.send_message(
                "Admin Only Command.",
                ephemeral=True
            )

        settings = load_settings()

        if key not in settings:
            return await interaction.response.send_message(
                "Invalid Setting Key.",
                ephemeral=True
            )

        old_value = settings[key]
        settings[key] = value
        save_settings(settings)

        logger = self.bot.get_cog("Logger")
        actor = f"{interaction.user} ({interaction.user.id})"

        log.action("Setting Changed", f"{key}: {old_value} -> {value} By {actor}")

        if logger:
            await logger.send_webhook(
                "SYSTEM",
                "Setting Changed",
                f"{key}\nOld: {old_value}\nNew: {value}\nBy: {actor}"
            )

        async with aiohttp.ClientSession() as session:
            await session.post(
                NoticeWebhook,
                json={
                    "content": f"⚙️ **Setting Changed**\n{key}: {old_value} → {value}\nBy {actor}"
                }
            )

        await interaction.response.send_message(
            f"Setting `{key}` Updated.\nRestarting...",
            ephemeral=True
        )

        await asyncio.sleep(1)
        restart_bot()


# ===============================
# BOTINFO
# ===============================

    @app_commands.command(name="botinfo")
    async def botinfo(self, interaction: Interaction):

        start_ts = int(START_TIME.timestamp())

        embed = discord.Embed(title="Bot Information", color=EmbedColor)

        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        embed.add_field(name="Developer", value=Developer, inline=True)
        embed.add_field(name="Version", value=Version, inline=True)

        embed.add_field(name="Support Server", value=SupportServer, inline=False)

        embed.add_field(name="Python", value=platform.python_version(), inline=True)
        embed.add_field(name="discord.py", value=discord.__version__, inline=True)

        embed.add_field(name="Uptime", value=f"<t:{start_ts}:R>", inline=False)

        embed.set_footer(text=f"Bot ID: {self.bot.user.id}")

        await interaction.response.send_message(embed=embed)


# ===============================
# WEEKLY DATABASE BACKUP
# ===============================

    @tasks.loop(hours=168)  # 7 days
    async def weekly_backup(self):

        await self.bot.wait_until_ready()

        try:
            folder = "Database"
            timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
            zip_name = f"backup_{timestamp}.zip"

            with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zipf:

                for root, dirs, files in os.walk(folder):
                    for file in files:
                        path = os.path.join(root, file)
                        arcname = os.path.relpath(path, folder)
                        zipf.write(path, arcname)

            async with aiohttp.ClientSession() as session:

                with open(zip_name, "rb") as f:

                    data = aiohttp.FormData()
                    data.add_field("file", f, filename=zip_name)

                    data.add_field(
                        "payload_json",
                        json.dumps({
                            "content": f"📦 **Weekly Database Backup**\n<t:{int(datetime.utcnow().timestamp())}:F>"
                        })
                    )

                    await session.post(NoticeWebhook, data=data)

            os.remove(zip_name)

            log.action("Backup Sent", f"{zip_name}")

        except Exception as e:
            log.action("Backup Failed", str(e))


    @weekly_backup.before_loop
    async def before_backup(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Setup(bot))