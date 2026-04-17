from utils import *
from config import *






# ===============================
# 🔥 CONSOLE LOGGER
# ===============================

class ConsoleLogger:

    def __init__(self):
        init(autoreset=True)

        self.c = {
            "blk": Fore.LIGHTBLACK_EX,
            "red": Fore.LIGHTRED_EX,
            "ylw": Fore.LIGHTYELLOW_EX,
            "blu": Fore.LIGHTBLUE_EX,
            "grn": Fore.LIGHTGREEN_EX,
            "cyn": Fore.LIGHTCYAN_EX,
            "mag": Fore.LIGHTMAGENTA_EX,
            "wht": Fore.WHITE
        }

    def t(self):
        return datetime.now().strftime("%H:%M:%S")

    def _print(self, level, color, msg, obj=""):
        print(f"{self.c['blk']}{self.t()} » {color}{level} ➜ {self.c['wht']}{msg} [{obj}]")

    def info(self, m, o=""):
        self._print("INFO", self.c["blu"], m, o)

    def warn(self, m, o=""):
        self._print("WARN", self.c["ylw"], m, o)

    def err(self, m, o=""):
        self._print("ERROR", self.c["red"], m, o)

    def ok(self, m, o=""):
        self._print("SUCCESS", self.c["grn"], m, o)

    def action(self, m, o=""):
        self._print("ACTION", self.c["cyn"], m, o)

    def system(self, m, o=""):
        self._print("SYSTEM", self.c["mag"], m, o)

    def security(self, m, o=""):
        self._print("SECURITY", self.c["red"], m, o)

    def debug(self, m, o=""):
        self._print("DEBUG", self.c["blk"], m, o)


log = ConsoleLogger()


# ===============================
# 🎨 DISCORD EMBED COLORS
# ===============================

color_map = {
    "INFO": discord.Color.blue(),
    "WARN": discord.Color.orange(),
    "ERROR": discord.Color.red(),
    "SUCCESS": discord.Color.green(),
    "ACTION": discord.Color.blurple(),
    "SYSTEM": discord.Color.purple(),
    "SECURITY": discord.Color.red(),
    "DEBUG": discord.Color.light_grey()
}


# ===============================
# 📡 DISCORD WEBHOOK LOGGER
# ===============================

class Logger(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.webhook_url = NoticeWebhook
        self.session = aiohttp.ClientSession()

    async def send_webhook(self, level: str, message: str, obj: str = ""):

        color = color_map.get(level, discord.Color.default())

        embed = discord.Embed(
            title=level,
            description=f"{message} [{obj}]",
            color=color,
            timestamp=datetime.now()
        )

        webhook = discord.Webhook.from_url(
            self.webhook_url,
            session=self.session
        )

        await webhook.send(
            embed=embed
        )


# ===============================
# ⚙️ COG SETUP
# ===============================

async def setup(bot):
    await bot.add_cog(Logger(bot))
