from utils import *
from config import *
from .permission import perm_check
from Cogs.logger import log
PUNISH_PATH = "Database/punish.json"



def parse_duration(duration_str):
    duration_str = duration_str.lower().strip()
    time_units = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400
    }
    if duration_str[-1] in time_units:
        try:
            amount = int(duration_str[:-1])
            return amount * time_units[duration_str[-1]]
        except ValueError:
            return None

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


class Moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @app_commands.command(name="warn", description="Warn a user")
    async def warn(self, interaction: Interaction, user: discord.Member, reason: str):

        if not perm_check(interaction, permission_name="warn"):
            await interaction.response.send_message(
                "You Don't Have Permission.",
                ephemeral=True
            )
            return
        await interaction.response.defer(ephemeral=True)

        logger = self.bot.get_cog("Logger")
        actor = f"{interaction.user} ({interaction.user.id})"

        data = load_punish()

        user_id = str(user.id)
        now = int(time.time())


        if user_id not in data["Warns"]:
            data["Warns"][user_id] = {
                "TotalWarns": 0,
                "LastWarned": None,
                "WarnData": {}
            }


        user_warns = data["Warns"][user_id]


        # =========================
        # REMOVE EXPIRED WARNS
        # =========================

        expired = []

        for warn_id, warn_data in user_warns["WarnData"].items():
            if now - warn_data["timestamp"] > 604800:
                expired.append(warn_id)

        for w in expired:
            del user_warns["WarnData"][w]

        user_warns["TotalWarns"] = len(user_warns["WarnData"])


        warn_number = str(user_warns["TotalWarns"] + 1)

        user_warns["WarnData"][warn_number] = {
            "reason": reason,
            "timestamp": now
        }

        user_warns["TotalWarns"] += 1
        user_warns["LastWarned"] = now


        # =========================
        # CASE SYSTEM
        # =========================

        data["CaseCounter"] += 1
        case_id = str(data["CaseCounter"])

        data["Cases"][case_id] = {
            "user": user.id,
            "moderator": interaction.user.id,
            "action": "warn",
            "reason": reason,
            "duration": None,
            "timestamp": now
        }

        save_punish(data)


        # =========================
        # DM USER
        # =========================

        try:
            embed = discord.Embed(
                title="You Have Been Warned",
                color=EmbedColor
            )

            embed.add_field(name="Server", value=interaction.guild.name)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Total Warns", value=user_warns["TotalWarns"])
            await user.send(embed=embed)

        except:
            pass


        # =========================
        # LOGGING
        # =========================

        log.action(
            "User Warned",
            f"{user} ({user.id}) Warned By {actor} | Reason: {reason}"
        )

        if logger:
            await logger.send_webhook(
                "MODERATION",
                "User Warned",
                f"{user} ({user.id}) Warned By {actor}\nReason: {reason}\nCase: #{case_id}"
            )


        # =========================
        # RESPONSE
        # =========================

        embed = discord.Embed(
            title="User Warned",
            description=f"{user.mention} Has Been Warned.",
            color=EmbedColor
        )

        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Total Warns", value=user_warns["TotalWarns"])
        embed.set_footer(text=f"Case #{case_id}")

        await interaction.followup.send(
    embed=embed,
    ephemeral=True
)

    @app_commands.command(name="clearwarn", description="Clear a warn or all warns from a user")
    async def clearwarn(
        self,
        interaction: Interaction,
        user: discord.Member,
        warn_number: Optional[int] = None
    ):

        if not perm_check(interaction, permission_name="manage_warn"):
            await interaction.response.send_message(
                "You Don't Have Permission.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        logger = self.bot.get_cog("Logger")
        actor = f"{interaction.user} ({interaction.user.id})"

        data = load_punish()
        user_id = str(user.id)

        if user_id not in data["Warns"] or not data["Warns"][user_id]["WarnData"]:
            await interaction.followup.send(
                "This User Has No Warns.",
                ephemeral=True
            )
            return

        user_warns = data["Warns"][user_id]


        # =========================
        # REMOVE SINGLE WARN
        # =========================

        if warn_number:

            warn_key = str(warn_number)

            if warn_key not in user_warns["WarnData"]:
                await interaction.followup.send(
                    "Invalid Warn Number.",
                    ephemeral=True
                )
                return

            warn_reason = user_warns["WarnData"][warn_key]["reason"]

            del user_warns["WarnData"][warn_key]

            user_warns["TotalWarns"] = len(user_warns["WarnData"])

            msg = f"Warn #{warn_number} Removed From {user.mention}."

            # DM USER
            try:
                embed = discord.Embed(
                    title="A Warn Was Removed",
                    color=EmbedColor
                )
                embed.add_field(name="Server", value=interaction.guild.name)
                embed.add_field(name="Removed Warn", value=f"Warn #{warn_number}")
                embed.add_field(name="Original Reason", value=warn_reason, inline=False)

                await user.send(embed=embed)
            except:
                pass

            log.action(
                "Warn Removed",
                f"{user} ({user.id}) Warn #{warn_number} Removed By {actor}"
            )

            if logger:
                await logger.send_webhook(
                    "MODERATION",
                    "Warn Removed",
                    f"{user} ({user.id}) Warn #{warn_number} Removed By {actor}"
                )


        # =========================
        # REMOVE ALL WARNS
        # =========================

        else:

            total = user_warns["TotalWarns"]

            user_warns["WarnData"] = {}
            user_warns["TotalWarns"] = 0
            user_warns["LastWarned"] = None

            msg = f"All Warns Cleared From {user.mention}. ({total} Removed)"

            # DM USER
            try:
                embed = discord.Embed(
                    title="Your Warns Were Cleared",
                    color=EmbedColor
                )

                embed.add_field(name="Server", value=interaction.guild.name)
                embed.add_field(name="Warns Removed", value=str(total))

                await user.send(embed=embed)
            except:
                pass

            log.action(
                "All Warns Cleared",
                f"{user} ({user.id}) All Warns Cleared By {actor}"
            )

            if logger:
                await logger.send_webhook(
                    "MODERATION",
                    "All Warns Cleared",
                    f"{user} ({user.id}) All Warns Cleared By {actor}"
                )


        # =========================
        # CASE SYSTEM
        # =========================

        data["CaseCounter"] += 1
        case_id = str(data["CaseCounter"])

        data["Cases"][case_id] = {
            "user": user.id,
            "moderator": interaction.user.id,
            "action": "clearwarn",
            "reason": "Warn Removed",
            "duration": None,
            "timestamp": int(time.time())
        }

        save_punish(data)


        embed = discord.Embed(
            title="Warn Cleared",
            description=msg,
            color=EmbedColor
        )


        await interaction.followup.send(
            embed=embed,
            ephemeral=True
        )
    @app_commands.command(name="timeout", description="Timeout a User")
    @app_commands.describe(
        user="The User To Timeout",
        reason="The Reason For The Timeout",
        duration="The Duration Of The Timeout (e.g. 10m, 1h, 1d)"
    )
    async def timeout(
        self,
        interaction: Interaction,
        user: discord.Member,
        reason: str,
        duration: Optional[str]
    ):

        if not perm_check(interaction, permission_name="timeout"):
            await interaction.response.send_message(
                "You Don't Have Permission.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        logger = self.bot.get_cog("Logger")
        actor = f"{interaction.user} ({interaction.user.id})"

        data = load_punish()

        # =========================
        # DURATION
        # =========================

        default_seconds = 30 * 60

        if duration is None:
            duration_seconds = default_seconds
            duration_display = "30m"
        else:
            parsed = parse_duration(duration)

            if parsed is None:
                duration_seconds = default_seconds
                duration_display = "30m"
            else:
                duration_seconds = parsed
                duration_display = duration

        # =========================
        # CHECK IF ALREADY TIMED OUT
        # =========================

        user_timeout = user.timed_out_until

        if user_timeout and user_timeout > discord.utils.utcnow():
            await interaction.followup.send(
                "User Is Already Timed Out.",
                ephemeral=True
            )
            return

        # =========================
        # APPLY TIMEOUT
        # =========================

        until = discord.utils.utcnow() + timedelta(seconds=duration_seconds)

        await user.timeout(
            until,
            reason=f"{reason} | By {interaction.user}"
        )

        # =========================
        # CASE SYSTEM
        # =========================

        data["CaseCounter"] += 1
        case_id = str(data["CaseCounter"])

        data["Cases"][case_id] = {
            "user": user.id,
            "moderator": interaction.user.id,
            "action": "timeout",
            "reason": reason,
            "duration": duration_display,
            "timestamp": int(time.time())
        }

        save_punish(data)

        # =========================
        # DM USER
        # =========================

        try:
            embed = discord.Embed(
                title="You Have Been Timed Out",
                color=EmbedColor
            )

            embed.add_field(name="Server", value=interaction.guild.name)
            embed.add_field(name="Duration", value=duration_display)
            embed.add_field(name="Reason", value=reason, inline=False)

            await user.send(embed=embed)

        except:
            pass

        # =========================
        # LOGGING
        # =========================

        log.action(
            "User Timed Out",
            f"{user} ({user.id}) Timed Out By {actor} | Duration: {duration_display} | Reason: {reason}"
        )

        if logger:
            await logger.send_webhook(
                "MODERATION",
                "User Timed Out",
                f"{user} ({user.id}) Timed Out By {actor}\nDuration: {duration_display}\nReason: {reason}\nCase: #{case_id}"
            )

        # =========================
        # RESPONSE
        # =========================

        embed = discord.Embed(
            title="User Timed Out",
            description=f"{user.mention} Has Been Timed Out.",
            color=EmbedColor
        )

        embed.add_field(name="Duration", value=duration_display)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"Case #{case_id}")

        await interaction.followup.send(
            embed=embed,
            ephemeral=True
        )
    
    @app_commands.command(name="untimeout", description="Remove Timeout From A User")
    @app_commands.describe(
        user="The User To Remove Timeout From",
        reason="Reason For Removing Timeout"
    )
    async def untimeout(
        self,
        interaction: Interaction,
        user: discord.Member,
        reason: Optional[str] = None
    ):

        if not perm_check(interaction, permission_name="timeout"):
            await interaction.response.send_message(
                "You Don't Have Permission.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        logger = self.bot.get_cog("Logger")
        actor = f"{interaction.user} ({interaction.user.id})"

        data = load_punish()

        if reason is None:
            reason = "No Reason Provided"

        # =========================
        # CHECK IF USER IS TIMED OUT
        # =========================

        user_timeout = user.timed_out_until

        if not user_timeout or user_timeout <= discord.utils.utcnow():
            await interaction.followup.send(
                "User Is Not Timed Out.",
                ephemeral=True
            )
            return

        # =========================
        # REMOVE TIMEOUT
        # =========================

        await user.timeout(
            None,
            reason=f"{reason} | By {interaction.user}"
        )

        # =========================
        # CASE SYSTEM
        # =========================

        data["CaseCounter"] += 1
        case_id = str(data["CaseCounter"])

        data["Cases"][case_id] = {
            "user": user.id,
            "moderator": interaction.user.id,
            "action": "untimeout",
            "reason": reason,
            "duration": None,
            "timestamp": int(time.time())
        }

        save_punish(data)

        # =========================
        # DM USER
        # =========================

        try:
            embed = discord.Embed(
                title="Your Timeout Was Removed",
                color=EmbedColor
            )

            embed.add_field(name="Server", value=interaction.guild.name)
            embed.add_field(name="Reason", value=reason, inline=False)

            await user.send(embed=embed)

        except:
            pass

        # =========================
        # LOGGING
        # =========================

        log.action(
            "User Timeout Removed",
            f"{user} ({user.id}) Timeout Removed By {actor} | Reason: {reason}"
        )

        if logger:
            await logger.send_webhook(
                "MODERATION",
                "User Timeout Removed",
                f"{user} ({user.id}) Timeout Removed By {actor}\nReason: {reason}\nCase: #{case_id}"
            )

        # =========================
        # RESPONSE
        # =========================

        embed = discord.Embed(
            title="Timeout Removed",
            description=f"{user.mention} Is No Longer Timed Out.",
            color=EmbedColor
        )

        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"Case #{case_id}")

        await interaction.followup.send(
            embed=embed,
            ephemeral=True
        )
    
    @app_commands.command(name="kick", description="Kick A User")
    @app_commands.describe(
        user="The User To Kick",
        reason="Reason For The Kick"
    )
    async def kick(
        self,
        interaction: Interaction,
        user: discord.Member,
        reason: Optional[str] = None
    ):

        if not perm_check(interaction, permission_name="kick"):
            await interaction.response.send_message(
                "You Don't Have Permission.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        logger = self.bot.get_cog("Logger")
        antinuke = self.bot.get_cog("AntiNuke")

        actor = f"{interaction.user} ({interaction.user.id})"

        if reason is None:
            reason = "No Reason Provided"

        # =========================
        # KICK USER
        # =========================

        try:
            await user.kick(reason=f"{reason} | By {interaction.user}")
        except discord.Forbidden:
            await interaction.followup.send(
                "I Cannot Kick This User.",
                ephemeral=True
            )
            return

        # =========================
        # CASE SYSTEM
        # =========================

        data = load_punish()

        data["CaseCounter"] += 1
        case_id = str(data["CaseCounter"])

        data["Cases"][case_id] = {
            "user": user.id,
            "moderator": interaction.user.id,
            "action": "kick",
            "reason": reason,
            "duration": None,
            "timestamp": int(time.time())
        }

        save_punish(data)
        if antinuke:
            await antinuke.record_action(interaction, "kick")

        # =========================
        # DM USER
        # =========================

        try:
            embed = discord.Embed(
                title="You Have Been Kicked",
                color=EmbedColor
            )

            embed.add_field(name="Server", value=interaction.guild.name)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text=f"Case #{case_id}")

            await user.send(embed=embed)
        except:
            pass

        # =========================
        # ANTINUKE RECORD
        # =========================

        # =========================
        # LOGGING
        # =========================

        log.action(
            "User Kicked",
            f"{user} ({user.id}) Kicked By {actor} | Reason: {reason}"
        )

        if logger:
            await logger.send_webhook(
                "MODERATION",
                "User Kicked",
                f"{user} ({user.id}) Kicked By {actor}\nReason: {reason}\nCase: #{case_id}"
            )

        # =========================
        # RESPONSE
        # =========================

        embed = discord.Embed(
            title="User Kicked",
            description=f"{user.mention} Has Been Kicked.",
            color=EmbedColor
        )

        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"Case #{case_id}")

        await interaction.followup.send(
            embed=embed,
            ephemeral=True
        )
    @app_commands.command(name="ban", description="Ban A User")
    @app_commands.describe(
        user="The User To Ban",
        reason="Reason For The Ban"
    )
    async def ban(
        self,
        interaction: Interaction,
        user: discord.Member,
        reason: Optional[str] = None
    ):

        if not perm_check(interaction, permission_name="ban"):
            await interaction.response.send_message(
                "You Don't Have Permission.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        logger = self.bot.get_cog("Logger")
        antinuke = self.bot.get_cog("AntiNuke")

        actor = f"{interaction.user} ({interaction.user.id})"

        if reason is None:
            reason = "No Reason Provided"

        # =========================
        # DM USER BEFORE BAN
        # =========================

        try:
            embed = discord.Embed(
                title="You Have Been Banned",
                color=EmbedColor
            )

            embed.add_field(name="Server", value=interaction.guild.name)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=str(interaction.user))

            await user.send(embed=embed)

        except:
            pass

        # =========================
        # BAN USER
        # =========================

        try:
            await user.ban(reason=f"{reason} | By {interaction.user}")

        except discord.Forbidden:
            await interaction.followup.send(
                "I Cannot Ban This User.",
                ephemeral=True
            )
            return

        # =========================
        # CASE SYSTEM
        # =========================

        data = load_punish()

        data["CaseCounter"] += 1
        case_id = str(data["CaseCounter"])

        data["Cases"][case_id] = {
            "user": user.id,
            "moderator": interaction.user.id,
            "action": "ban",
            "reason": reason,
            "duration": None,
            "timestamp": int(time.time())
        }

        save_punish(data)

        # =========================
        # ANTINUKE RECORD
        # =========================

        if antinuke:
            await antinuke.record_action(interaction, "ban")

        # =========================
        # LOGGING
        # =========================

        log.action(
            "User Banned",
            f"{user} ({user.id}) Banned By {actor} | Reason: {reason}"
        )

        if logger:
            await logger.send_webhook(
                "MODERATION",
                "User Banned",
                f"{user} ({user.id}) Banned By {actor}\nReason: {reason}\nCase: #{case_id}"
            )

        # =========================
        # RESPONSE
        # =========================

        embed = discord.Embed(
            title="User Banned",
            description=f"{user.mention} Has Been Banned.",
            color=EmbedColor
        )

        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"Case #{case_id}")

        await interaction.followup.send(
            embed=embed,
            ephemeral=True
        )

    @app_commands.command(name="unban", description="Unban A User")
    @app_commands.describe(
        user_id="The ID Of The User To Unban",
        reason="Reason For The Unban"
    )
    async def unban(
        self,
        interaction: Interaction,
        user_id: str,
        reason: Optional[str] = None
    ):

        if not perm_check(interaction, permission_name="ban"):
            await interaction.response.send_message(
                "You Don't Have Permission.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        logger = self.bot.get_cog("Logger")
        actor = f"{interaction.user} ({interaction.user.id})"

        if reason is None:
            reason = "No Reason Provided"

        # =========================
        # UNBAN USER
        # =========================
        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user, reason=f"{reason} | By {interaction.user}")
        except discord.NotFound:
            await interaction.followup.send(
                "User Not Found In Ban List.",
                ephemeral=True
            )
            return
        except Exception:
            await interaction.followup.send(
                "Failed To Unban User.",
                ephemeral=True
            )
            return

        # =========================
        # CASE SYSTEM
        # =========================
        data = load_punish()

        data["CaseCounter"] += 1
        case_id = str(data["CaseCounter"])

        data["Cases"][case_id] = {
            "user": user.id,
            "moderator": interaction.user.id,
            "action": "unban",
            "reason": reason,
            "duration": None,
            "timestamp": int(time.time())
        }

        save_punish(data)

        # =========================
        # RESPONSE (send early so interaction finishes)
        # =========================
        embed = discord.Embed(
            title="User Unbanned",
            description=f"{user} Has Been Unbanned.",
            color=EmbedColor
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"Case #{case_id}")

        await interaction.followup.send(embed=embed, ephemeral=True)

        # =========================
        # LOGGING
        # =========================
        log.action(
            "User Unbanned",
            f"{user} ({user.id}) Unbanned By {actor} | Reason: {reason}"
        )

        if logger:
            await logger.send_webhook(
                "MODERATION",
                "User Unbanned",
                f"{user} ({user.id}) Unbanned By {actor}\nReason: {reason}\nCase: #{case_id}"
            )


    
    @app_commands.command(name="purge", description="Bulk Delete Messages")
    @app_commands.describe(
        amount="The Number Of Messages To Delete (Max 500)"
    )
    async def purge(
        self,
        interaction: Interaction,
        amount: int
    ):
        if not perm_check(interaction, permission_name="manage_messages"):
            await interaction.response.send_message(
                "You Don't Have Permission.",
                ephemeral=True
            )
            return

        if amount <= 0 or amount > 500:
            await interaction.response.send_message(
                "Please Enter A Valid Amount (1-500).",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        deleted = await interaction.channel.purge(limit=amount)

        await interaction.followup.send(
            f"Successfully Deleted {len(deleted)} Messages.",
            ephemeral=True
        )
    
   

    @app_commands.command(name="nickname", description="Change A User's Nickname")
    @app_commands.describe(
        user="User Whose Nickname Will Be Changed",
        nickname="New Nickname"
    )
    async def nickname(
        self,
        interaction: Interaction,
        user: discord.Member,
        nickname: Optional[str] = None
    ):

        if not perm_check(interaction, permission_name="nickname"):
            await interaction.response.send_message(
                "You Don't Have Permission.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        logger = self.bot.get_cog("Logger")
        actor = f"{interaction.user} ({interaction.user.id})"

        old_nick = user.nick if user.nick else user.name

        try:
            await user.edit(nick=nickname, reason=f"By {interaction.user}")
        except discord.Forbidden:
            await interaction.followup.send(
                "I Cannot Change This User's Nickname.",
                ephemeral=True
            )
            return

        new_nick = nickname if nickname else user.name

        log.action(
            "Nickname Changed",
            f"{user} ({user.id}) Nickname Changed By {actor} | {old_nick} -> {new_nick}"
        )

        if logger:
            await logger.send_webhook(
                "MODERATION",
                "Nickname Changed",
                f"{user} ({user.id}) Nickname Changed By {actor}\nOld: {old_nick}\nNew: {new_nick}"
            )

        embed = discord.Embed(
            title="Nickname Updated",
            color=EmbedColor
        )

        embed.add_field(name="User", value=user.mention)
        embed.add_field(name="Old Nickname", value=old_nick)
        embed.add_field(name="New Nickname", value=new_nick)

        await interaction.followup.send(embed=embed, ephemeral=True)


    @app_commands.command(name="case", description="View A Case Or User Cases")
    @app_commands.describe(
        case_number="Case Number",
        user="User To View Cases"
    )
    async def case(
        self,
        interaction: Interaction,
        case_number: Optional[int] = None,
        user: Optional[discord.Member] = None
    ):

        if not perm_check(interaction, permission_name="mod_admin"):
            await interaction.response.send_message(
                "You Don't Have Permission.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        data = load_punish()

        # =========================
        # VIEW SINGLE CASE
        # =========================

        if case_number:

            case_id = str(case_number)

            if case_id not in data["Cases"]:
                await interaction.followup.send(
                    "Case Not Found.",
                    ephemeral=True
                )
                return

            case = data["Cases"][case_id]

            embed = discord.Embed(
                title=f"Case #{case_id}",
                color=EmbedColor
            )

            embed.add_field(name="User ID", value=case["user"])
            embed.add_field(name="Moderator ID", value=case["moderator"])
            embed.add_field(name="Action", value=case["action"])
            embed.add_field(name="Reason", value=case["reason"], inline=False)

            if case["duration"]:
                embed.add_field(name="Duration", value=case["duration"])

            embed.add_field(name="Timestamp", value=f"<t:{case['timestamp']}:F>")

            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # =========================
        # VIEW USER CASES
        # =========================

        if user:

            cases = [
                (cid, c) for cid, c in data["Cases"].items()
                if c["user"] == user.id
            ]

            if not cases:
                await interaction.followup.send(
                    "No Cases Found For This User.",
                    ephemeral=True
                )
                return

            embed = discord.Embed(
                title=f"Cases For {user}",
                color=EmbedColor
            )

            description = ""

            for cid, case in cases[-10:]:
                description += f"**#{cid}** • {case['action']} • <t:{case['timestamp']}:R>\n"

            embed.description = description

            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        await interaction.followup.send(
            "Provide Either A Case Number Or A User.",
            ephemeral=True
        )

# CHANNEL MODERATION COMMANDS (e.g. lock, unlock, slowmode) Can Be Added Here


    @app_commands.command(name="lock", description="Lock A Channel")
    @app_commands.describe(
        channel="Channel To Lock",
        reason="Reason For Locking"
    )
    async def lock(
        self,
        interaction: Interaction,
        channel: Optional[discord.TextChannel] = None,
        reason: Optional[str] = None
    ):

        if not perm_check(interaction, permission_name="channel_manage"):
            await interaction.response.send_message(
                "You Don't Have Permission.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        logger = self.bot.get_cog("Logger")

        actor = f"{interaction.user} ({interaction.user.id})"

        if channel is None:
            channel = interaction.channel

        if reason is None:
            reason = "No Reason Provided"

        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False

        try:
            await channel.set_permissions(
                interaction.guild.default_role,
                overwrite=overwrite,
                reason=f"{reason} | By {interaction.user}"
            )

        except discord.Forbidden:
            await interaction.followup.send(
                "I Cannot Lock This Channel.",
                ephemeral=True
            )
            return

        log.action(
            "Channel Locked",
            f"{channel.name} ({channel.id}) Locked By {actor} | Reason: {reason}"
        )

        if logger:
            await logger.send_webhook(
                "CHANNEL",
                "Channel Locked",
                f"{channel.name} ({channel.id}) Locked By {actor}\nReason: {reason}"
            )

        embed = discord.Embed(
            title="Channel Locked",
            description=f"{channel.mention} Has Been Locked.",
            color=EmbedColor
        )

        embed.add_field(name="Reason", value=reason)

        await interaction.followup.send(embed=embed, ephemeral=True)




    @app_commands.command(name="unlock", description="Unlock A Channel")
    @app_commands.describe(
        channel="Channel To Unlock",
        reason="Reason For Unlocking"
    )
    async def unlock(
        self,
        interaction: Interaction,
        channel: Optional[discord.TextChannel] = None,
        reason: Optional[str] = None
    ):

        if not perm_check(interaction, permission_name="channel_manage"):
            await interaction.response.send_message(
                "You Don't Have Permission.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        logger = self.bot.get_cog("Logger")

        actor = f"{interaction.user} ({interaction.user.id})"

        if channel is None:
            channel = interaction.channel

        if reason is None:
            reason = "No Reason Provided"

        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = True

        try:
            await channel.set_permissions(
                interaction.guild.default_role,
                overwrite=overwrite,
                reason=f"{reason} | By {interaction.user}"
            )

        except discord.Forbidden:
            await interaction.followup.send(
                "I Cannot Unlock This Channel.",
                ephemeral=True
            )
            return

        log.action(
            "Channel Unlocked",
            f"{channel.name} ({channel.id}) Unlocked By {actor} | Reason: {reason}"
        )

        if logger:
            await logger.send_webhook(
                "CHANNEL",
                "Channel Unlocked",
                f"{channel.name} ({channel.id}) Unlocked By {actor}\nReason: {reason}"
            )

        embed = discord.Embed(
            title="Channel Unlocked",
            description=f"{channel.mention} Has Been Unlocked.",
            color=EmbedColor
        )

        embed.add_field(name="Reason", value=reason)

        await interaction.followup.send(embed=embed, ephemeral=True)

    

    @app_commands.command(name="createchannel", description="Create A Channel")
    @app_commands.describe(
        name="Channel Name",
        type="Channel Type",
        category="Category To Create Channel In",
        topic="Channel Topic",
        slowmode="Slowmode In Seconds",
        nsfw="Whether Channel Is NSFW",
        bitrate="Voice Bitrate",
        user_limit="Voice User Limit"
    )
    @app_commands.choices(
        type=[
            app_commands.Choice(name="Text", value="text"),
            app_commands.Choice(name="Voice", value="voice"),
            app_commands.Choice(name="Stage", value="stage"),
            app_commands.Choice(name="Forum", value="forum"),
            app_commands.Choice(name="Category", value="category"),
        ]
    )
    async def createchannel(
        self,
        interaction: Interaction,
        name: str,
        type: app_commands.Choice[str],
        category: Optional[discord.CategoryChannel] = None,
        topic: Optional[str] = None,
        slowmode: Optional[int] = None,
        nsfw: Optional[bool] = False,
        bitrate: Optional[int] = None,
        user_limit: Optional[int] = None
    ):

        if not perm_check(interaction, permission_name="channel_manage"):
            await interaction.response.send_message(
                "You Don't Have Permission.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        logger = self.bot.get_cog("Logger")
        antinuke = self.bot.get_cog("AntiNuke")

        actor = f"{interaction.user} ({interaction.user.id})"

        guild = interaction.guild

        try:

            if type.value == "text":
                channel = await guild.create_text_channel(
                    name=name,
                    category=category,
                    topic=topic,
                    slowmode_delay=slowmode,
                    nsfw=nsfw
                )

            elif type.value == "voice":
                channel = await guild.create_voice_channel(
                    name=name,
                    category=category,
                    bitrate=bitrate,
                    user_limit=user_limit
                )

            elif type.value == "stage":
                channel = await guild.create_stage_channel(
                    name=name,
                    category=category
                )

            elif type.value == "forum":
                channel = await guild.create_forum(
                    name=name,
                    category=category
                )

            elif type.value == "category":
                channel = await guild.create_category(name=name)

        except discord.Forbidden:
            await interaction.followup.send(
                "I Cannot Create This Channel.",
                ephemeral=True
            )
            return

        # ANTINUKE
        if antinuke:
            await antinuke.record_action(interaction, "channel_create")

        # LOGGING
        log.action(
            "Channel Created",
            f"{channel.name} ({channel.id}) Created By {actor}"
        )

        if logger:
            await logger.send_webhook(
                "CHANNEL",
                "Channel Created",
                f"{channel.name} ({channel.id}) Created By {actor}"
            )

        embed = discord.Embed(
            title="Channel Created",
            description=f"{channel.mention} Has Been Created.",
            color=EmbedColor
        )

        embed.add_field(name="Type", value=type.value)
        embed.add_field(name="Category", value=category.name if category else "None")

        await interaction.followup.send(embed=embed, ephemeral=True)



    @app_commands.command(name="deletechannel", description="Delete A Channel")
    @app_commands.describe(
        channel="Channel To Delete (Defaults To Current Channel)",
        reason="Reason For Deleting The Channel"
    )
    async def deletechannel(
        self,
        interaction: Interaction,
        channel: Optional[discord.abc.GuildChannel] = None,
        reason: Optional[str] = None
    ):

        if not perm_check(interaction, permission_name="channel_manage"):
            await interaction.response.send_message(
                "You Don't Have Permission.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        logger = self.bot.get_cog("Logger")
        antinuke = self.bot.get_cog("AntiNuke")

        actor = f"{interaction.user} ({interaction.user.id})"

        if channel is None:
            channel = interaction.channel

        if reason is None:
            reason = "No Reason Provided"

        channel_name = channel.name
        channel_id = channel.id

        try:
            await channel.delete(reason=f"{reason} | By {interaction.user}")

        except discord.Forbidden:
            await interaction.followup.send(
                "I Cannot Delete This Channel.",
                ephemeral=True
            )
            return

        # ANTINUKE RECORD
        if antinuke:
            await antinuke.record_action(interaction, "channel_delete")

        # LOGGING
        log.action(
            "Channel Deleted",
            f"{channel_name} ({channel_id}) Deleted By {actor} | Reason: {reason}"
        )

        if logger:
            await logger.send_webhook(
                "CHANNEL",
                "Channel Deleted",
                f"{channel_name} ({channel_id}) Deleted By {actor}\nReason: {reason}"
            )

        embed = discord.Embed(
            title="Channel Deleted",
            description=f"`{channel_name}` Has Been Deleted.",
            color=EmbedColor
        )

        embed.add_field(name="Reason", value=reason, inline=False)

        await interaction.followup.send(embed=embed, ephemeral=True)




# VC MODERATION COMMANDS (e.g. mute, unmute, move) Can Be Added Here
    @app_commands.command(name="vcmute", description="Mute A User In Voice Channels")
    @app_commands.describe(
        user="The User To Mute",
        reason="Reason For The VC Mute"
    )
    async def vcmute(
        self,
        interaction: Interaction,
        user: discord.Member,
        reason: Optional[str] = None
    ):

        if not perm_check(interaction, permission_name="vc_mod"):
            await interaction.response.send_message(
                "You Don't Have Permission.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        logger = self.bot.get_cog("Logger")

        actor = f"{interaction.user} ({interaction.user.id})"

        if reason is None:
            reason = "No Reason Provided"

        try:
            await user.edit(mute=True, reason=f"{reason} | By {interaction.user}")
        except discord.Forbidden:
            await interaction.followup.send(
                "I Cannot VC Mute This User.",
                ephemeral=True
            )
            return
        
        log.action(
            "User VC Muted",
            f"{user} ({user.id}) VC Muted By {actor} | Reason: {reason}"
        )

        if logger:
            await logger.send_webhook(
                "MODERATION",
                "User VC Muted",
                f"{user} ({user.id}) VC Muted By {actor}\nReason: {reason}"
            )
        embed = discord.Embed(
            title="User VC Muted",
            description=f"{user.mention} Has Been Muted In Voice Channels.",
            color=EmbedColor)
        

        embed.add_field(name="Reason", value=reason, inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)

    
    @app_commands.command(name="vcunmute", description="Unmute A User In Voice Channels")
    @app_commands.describe(
        user="The User To Unmute",
        reason="Reason For The VC Unmute"
    )
    async def vcunmute(
        self,
        interaction: Interaction,
        user: discord.Member,
        reason: Optional[str] = None
    ):

        if not perm_check(interaction, permission_name="vc_mod"):
            await interaction.response.send_message(
                "You Don't Have Permission.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        logger = self.bot.get_cog("Logger")

        actor = f"{interaction.user} ({interaction.user.id})"

        if reason is None:
            reason = "No Reason Provided"

        try:
            await user.edit(mute=False, reason=f"{reason} | By {interaction.user}")
        except discord.Forbidden:
            await interaction.followup.send(
                "I Cannot VC Unmute This User.",
                ephemeral=True
            )
            return
        
        log.action(
            "User VC Unmuted",
            f"{user} ({user.id}) VC Unmuted By {actor} | Reason: {reason}"
        )

        if logger:
            await logger.send_webhook(
                "MODERATION",
                "User VC Unmuted",
                f"{user} ({user.id}) VC Unmuted By {actor}\nReason: {reason}"
            )
        
        embed = discord.Embed(
            title="User VC Unmuted",
            description=f"{user.mention} Has Been Unmuted In Voice Channels.",
            color=EmbedColor)
        

        embed.add_field(name="Reason", value=reason, inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)


    @app_commands.command(name="vcmove", description="Move A User To Another Voice Channel")
    @app_commands.describe(user="The User To Move", channel="The Channel To Move The User To", reason="Reason For Moving The User")
    async def vcmove(
        self,
        interaction: Interaction,
        user: discord.Member,
        channel: discord.VoiceChannel,
        reason: Optional[str] = None
    ):

        if not perm_check(interaction, permission_name="vc_mod"):
            await interaction.response.send_message(
                "You Don't Have Permission.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        logger = self.bot.get_cog("Logger")

        actor = f"{interaction.user} ({interaction.user.id})"

        if reason is None:
            reason = "No Reason Provided"

        try:
            await user.move_to(channel, reason=f"{reason} | By {interaction.user}")
        except discord.Forbidden:
            await interaction.followup.send(
                "I Cannot Move This User.",
                ephemeral=True
            )
            return
        
        log.action(
            "User Moved",
            f"{user} ({user.id}) Moved To {channel.name} By {actor} | Reason: {reason}"
        )

        if logger:
            await logger.send_webhook(
                "MODERATION",
                "User Moved",
                f"{user} ({user.id}) Moved To {channel.name} By {actor}\nReason: {reason}"
            )
        
        embed = discord.Embed(
            title="User Moved",
            description=f"{user.mention} Has Been Moved To {channel.mention}.",
            color=EmbedColor)
        

        embed.add_field(name="Reason", value=reason, inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="servermute", description="Mute A User In The Server")
    @app_commands.describe(
        user="The User To Mute",
        reason="Reason For The Server Mute"
    )
    async def servermute(
        self,
        interaction: Interaction,
        user: discord.Member,
        reason: Optional[str] = None
    ):

        if not perm_check(interaction, permission_name="vc_mod"):
            await interaction.response.send_message(
                "You Don't Have Permission.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        logger = self.bot.get_cog("Logger")

        actor = f"{interaction.user} ({interaction.user.id})"

        if reason is None:
            reason = "No Reason Provided"

        try:
            await user.edit(communication_disabled_until=datetime.now() + timedelta(days=365), reason=f"{reason} | By {interaction.user}")
        except discord.Forbidden:
            await interaction.followup.send(
                "I Cannot Server Mute This User.",
                ephemeral=True
            )
            return
        
        log.action(
            "User Server Muted",
            f"{user} ({user.id}) Server Muted By {actor} | Reason: {reason}"
        )

        if logger:
            await logger.send_webhook(
                "MODERATION",
                "User Server Muted",
                f"{user} ({user.id}) Server Muted By {actor}\nReason: {reason}"
            )
        
        embed = discord.Embed(
            title="User Server Muted",
            description=f"{user.mention} Has Been Muted In The Server.",
            color=EmbedColor)
        

        embed.add_field(name="Reason", value=reason, inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="serverdeafen", description="Server Defean A User In The Server")
    @app_commands.describe(
        user="The User To Deafen",
        reason="Reason For The Server Deafen"
    )
    async def serverdeafen(
        self,
        interaction: Interaction,
        user: discord.Member,
        reason: Optional[str] = None
    ):

        if not perm_check(interaction, permission_name="vc_mod"):
            await interaction.response.send_message(
                "You Don't Have Permission.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        logger = self.bot.get_cog("Logger")

        actor = f"{interaction.user} ({interaction.user.id})"

        if reason is None:
            reason = "No Reason Provided"

        try:
            await user.edit(deafen=True, reason=f"{reason} | By {interaction.user}")
        except discord.Forbidden:
            await interaction.followup.send(
                "I Cannot Server Deafen This User.",
                ephemeral=True
            )
            return
        
        log.action(
            "User Server Deafened",
            f"{user} ({user.id}) Server Deafened By {actor} | Reason: {reason}"
        )

        if logger:
            await logger.send_webhook(
                "MODERATION",
                "User Server Deafened",
                f"{user} ({user.id}) Server Deafened By {actor}\nReason: {reason}"
            )
        
        embed = discord.Embed(
            title="User Server Deafened",
            description=f"{user.mention} Has Been Deafened In The Server.",
            color=EmbedColor)
        

        embed.add_field(name="Reason", value=reason, inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)


    @app_commands.command(name="createwebhook", description="Create A Webhook In A Channel")
    @app_commands.describe(
        channel="Channel To Create Webhook In",
        name="Name Of The Webhook"
    )
    async def createwebhook(
        self,
        interaction: Interaction,
        channel: discord.TextChannel,
        name: str
    ):

        if not perm_check(interaction, permission_name="webhook"):
            await interaction.response.send_message(
                "You Don't Have Permission.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        logger = self.bot.get_cog("Logger")
        antinuke = self.bot.get_cog("AntiNuke")

        actor = f"{interaction.user} ({interaction.user.id})"

        try:
            webhook = await channel.create_webhook(
                name=name,
                reason=f"By {interaction.user}"
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "I Cannot Create Webhook In This Channel.",
                ephemeral=True
            )
            return

        # ANTINUKE
        if antinuke:
            await antinuke.record_action(interaction, "webhook")

        # LOGGING
        log.action(
            "Webhook Created",
            f"{webhook.name} ({webhook.id}) Created In {channel.name} By {actor}"
        )

        if logger:
            await logger.send_webhook(
                "WEBHOOK",
                "Webhook Created",
                f"{webhook.name} ({webhook.id}) Created In {channel.name} By {actor}"
            )

        embed = discord.Embed(
            title="Webhook Created",
            color=EmbedColor
        )

        embed.add_field(
            name="Channel",
            value=channel.mention,
            inline=False
        )

        embed.add_field(
            name="Webhook ID",
            value=f"```{webhook.id}```",
            inline=False
        )

        embed.add_field(
            name="Webhook URL",
            value=f"```{webhook.url}```",
            inline=False
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="deletewebhook", description="Delete A Webhook")
    @app_commands.describe(
        webhook_id="ID Of The Webhook To Delete"
    )
    async def deletewebhook(
        self,
        interaction: Interaction,
        webhook_id: str
    ):

        if not perm_check(interaction, permission_name="webhook"):
            await interaction.response.send_message(
                "You Don't Have Permission.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        logger = self.bot.get_cog("Logger")
        antinuke = self.bot.get_cog("AntiNuke")

        actor = f"{interaction.user} ({interaction.user.id})"

        try:
            webhook = await self.bot.fetch_webhook(int(webhook_id))

            if webhook.guild_id != interaction.guild.id:
                await interaction.followup.send(
                    "This Webhook Is Not From This Server.",
                    ephemeral=True
                )
                return

            await webhook.delete(reason=f"By {interaction.user}")

        except discord.NotFound:
            await interaction.followup.send(
                "Webhook Not Found.",
                ephemeral=True
            )
            return

        except discord.Forbidden:
            await interaction.followup.send(
                "I Cannot Delete This Webhook.",
                ephemeral=True
            )
            return

        # ANTINUKE
        if antinuke:
            await antinuke.record_action(interaction, "webhook")

        # LOGGING
        log.action(
            "Webhook Deleted",
            f"{webhook.name} ({webhook.id}) Deleted By {actor}"
        )

        if logger:
            await logger.send_webhook(
                "WEBHOOK",
                "Webhook Deleted",
                f"{webhook.name} ({webhook.id}) Deleted By {actor}"
            )

        embed = discord.Embed(
            title="Webhook Deleted",
            color=EmbedColor
        )

        embed.add_field(
            name="Webhook",
            value=f"`{webhook.name}`",
            inline=False
        )

        embed.add_field(
            name="Webhook ID",
            value=f"```{webhook.id}```",
            inline=False
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="webhooks", description="List All Webhooks In The Server")
    async def webhooks(self, interaction: Interaction):

        if not perm_check(interaction, permission_name="webhook"):
            await interaction.response.send_message(
                "You Don't Have Permission.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        webhooks = await interaction.guild.webhooks()

        if not webhooks:
            await interaction.followup.send(
                "No Webhooks Found In This Server.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Server Webhooks",
            color=EmbedColor
        )

        description = ""

        for webhook in webhooks:

            description += (
                f"**{webhook.name}**\n"
                f"ID: `{webhook.id}`\n"
                f"Channel: {webhook.channel.mention}\n\n"
            )

        embed.description = description

        await interaction.followup.send(embed=embed, ephemeral=True)
async def setup(bot):
    await bot.add_cog(Moderation(bot))