from utils import *
from config import *
from Cogs.logger import log
from Cogs.permission import perm_check


PUNISH_PATH = "Database/punish.json"
def load_punish():
    if not os.path.exists(PUNISH_PATH):
        os.makedirs("Database", exist_ok=True)

        data = {
            "Warns": {},
            "Cases": {},
            "CaseCounter": 0
        }

        with open(PUNISH_PATH, "w") as f:
            json.dump(data, f, indent=4)

        return data

    with open(PUNISH_PATH, "r") as f:
        return json.load(f)


def save_punish(data):
    with open(PUNISH_PATH, "w") as f:
        json.dump(data, f, indent=4)



MOD_ACTION_PATH = "Database/mod_action.json"


class AntiNuke(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.limits = {
            "ban": 5,
            "kick": 6,
            "timeout": 20,
            "channel_create": 5,
            "channel_delete": 2,
            "webhook": 2
        }

    # ===============================
    # LOAD / SAVE
    # ===============================

    def load_data(self):

        if not os.path.exists(MOD_ACTION_PATH):
            os.makedirs("Database", exist_ok=True)

            with open(MOD_ACTION_PATH, "w") as f:
                json.dump({}, f, indent=4)

        with open(MOD_ACTION_PATH, "r") as f:
            return json.load(f)

    def save_data(self, data):

        with open(MOD_ACTION_PATH, "w") as f:
            json.dump(data, f, indent=4)

    # ===============================
    # RECORD ACTION
    # ===============================

    async def record_action(self, interaction: Interaction, action: str):

        if perm_check(interaction, "anti_nuke_bypass"):
            return

        data = self.load_data()

        user_id = str(interaction.user.id)
        today = datetime.now().strftime("%Y-%m-%d")

        if user_id not in data:

            data[user_id] = {
                "date": today,
                "ban": 0,
                "kick": 0,
                "timeout": 0,
                "webhook": 0,
                "channel_create": 0,
                "channel_delete": 0,
                "purge": 0,
                "warn": 0
            }

        # reset counters if new day
        if data[user_id]["date"] != today:

            data[user_id] = {
                "date": today,
                "ban": 0,
                "kick": 0,
                "timeout": 0,
                "webhook": 0,
                "channel_create": 0,
                "channel_delete": 0,
                "purge": 0,
                "warn": 0
            }

        if action not in data[user_id]:
            data[user_id][action] = 0

        data[user_id][action] += 1

        self.save_data(data)

        if action in self.limits:
            if data[user_id][action] > self.limits[action]:
                await self.trigger_antinuke(interaction, action)

    # ===============================
    # TRIGGER ANTINUKE
    # ===============================

    async def trigger_antinuke(self, interaction: Interaction, action: str):

        logger = self.bot.get_cog("Logger")
        actor = f"{interaction.user} ({interaction.user.id})"

        limit = self.limits[action]

        try:
            until = discord.utils.utcnow() + timedelta(days=1)

            await interaction.user.timeout(
                until,
                reason="Anti Nuke Triggered"
            )
        except:
            pass

        # =========================
        # CASE SYSTEM
        # =========================

        data = load_punish()

        data["CaseCounter"] += 1
        case_id = str(data["CaseCounter"])

        data["Cases"][case_id] = {
            "user": interaction.user.id,
            "moderator": 0,
            "action": "antinuke",
            "reason": f"Exceeded {action} limit ({limit}/day)",
            "duration": "1d",
            "timestamp": int(time.time())
        }

        save_punish(data)

        # =========================
        # DM ADMINS
        # =========================

        try:

            with open("Database/admins.json", "r") as f:
                admins = json.load(f)

            admin_ids = set(admins["UserIDs"])

            for uid in admin_ids:

                user = self.bot.get_user(uid)

                if user:

                    embed = discord.Embed(
                        title="⚠️ Anti Nuke Triggered",
                        color=EmbedColor
                    )

                    embed.add_field(
                        name="User",
                        value=f"{interaction.user} ({interaction.user.id})",
                        inline=False
                    )

                    embed.add_field(
                        name="Action",
                        value=action,
                        inline=True
                    )

                    embed.add_field(
                        name="Limit",
                        value=f"{limit}/day",
                        inline=True
                    )

                    embed.add_field(
                        name="Punishment",
                        value="Timeout 1 Day",
                        inline=False
                    )

                    embed.set_footer(text=f"Case #{case_id}")

                    try:
                        await user.send(embed=embed)
                    except:
                        pass

        except:
            pass

        # =========================
        # LOGGING
        # =========================

        log.action(
            "Anti Nuke Triggered",
            f"{interaction.user} ({interaction.user.id}) Exceeded {action} Limit ({limit})"
        )

        if logger:

            await logger.send_webhook(
                "SECURITY",
                "Anti Nuke Triggered",
                f"{interaction.user} ({interaction.user.id})\n"
                f"Action: {action}\n"
                f"Limit: {limit}/day\n"
                f"Punishment: Timeout 1 Day\n"
                f"Case: #{case_id}"
            )

    


async def setup(bot):
    await bot.add_cog(AntiNuke(bot))