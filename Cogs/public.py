
from utils import *
from config import *
from Cogs.permission import perm_check



from typing import Optional

PUNISH_PATH = "Database/punish.json"
USERDATA_PATH = "Database/RoleMenu/UserData"

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
        
        
def save_punish(data):
    with open(PUNISH_PATH, "w") as f:
        json.dump(data, f, indent=4)

def load_punish():
    if not os.path.exists(PUNISH_PATH):
        return {"Warns": {}}

    with open(PUNISH_PATH) as f:
        return json.load(f)




class ReportModal(discord.ui.Modal, title="Report User"):

    user_id = discord.ui.TextInput(
        label="User ID To Report",
        placeholder="Enter User ID...",
        required=True,
        max_length=30
    )

    description = discord.ui.TextInput(
        label="Description",
        placeholder="Explain what happened...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    evidence = discord.ui.TextInput(
        label="Evidence (Image URLs)",
        placeholder="Paste image links (optional)...",
        required=False,
        max_length=1000
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):

        logger = self.bot.get_cog("Logger")
        actor = f"{interaction.user} ({interaction.user.id})"

        reported_id = self.user_id.value
        desc = self.description.value
        evidence = self.evidence.value or "None"

        # =========================
        # CREATE CASE
        # =========================

        data = load_punish()

        data["CaseCounter"] += 1
        case_id = str(data["CaseCounter"])

        data["Cases"][case_id] = {
            "user": int(reported_id),
            "moderator": interaction.user.id,
            "action": "report",
            "reason": desc,
            "duration": None,
            "timestamp": int(time.time())
        }

        save_punish(data)

        # =========================
        # EMBED
        # =========================

        embed = discord.Embed(
            title="🚨 New Report",
            color=EmbedColor
        )

        embed.add_field(
            name="Reporter",
            value=f"{interaction.user} ({interaction.user.id})",
            inline=False
        )

        embed.add_field(
            name="Reported User ID",
            value=reported_id,
            inline=False
        )

        embed.add_field(
            name="Description",
            value=desc,
            inline=False
        )

        embed.add_field(
            name="Evidence",
            value=evidence,
            inline=False
        )

        embed.set_footer(text=f"Case #{case_id}")

        # =========================
        # WEBHOOK
        # =========================

        async with aiohttp.ClientSession() as session:

            await session.post(
                NoticeWebhook,
                json={"embeds": [embed.to_dict()]}
            )

        # =========================
        # LOGGING
        # =========================

        log.action(
            "User Reported",
            f"{reported_id} Reported By {actor} | Case #{case_id}"
        )

        if logger:
            await logger.send_webhook(
                "REPORT",
                "User Report",
                f"User: {reported_id}\nBy: {actor}\nReason: {desc}\nCase: #{case_id}"
            )

        # =========================
        # RESPONSE
        # =========================

        await interaction.response.send_message(
            f"Report Submitted Successfully. Case #{case_id}",
            ephemeral=True
        )



class ProfileView(discord.ui.View):

    def __init__(self, bot, member):
        super().__init__(timeout=120)
        self.bot = bot
        self.member = member
        self.page = 0

    async def build_embed(self):

        member = self.member

        # =========================
        # PAGE 1 - USER INFO
        # =========================
        if self.page == 0:

            user = await self.bot.fetch_user(member.id)

            embed = discord.Embed(
                title=f"{member}",
                color=EmbedColor
            )

            embed.set_thumbnail(url=member.display_avatar.url)

            if user.banner:
                embed.set_image(url=user.banner.url)

            badges = []

            flags = member.public_flags

            if flags.hypesquad_balance:
                badges.append("⚖️ Balance")
            if flags.hypesquad_bravery:
                badges.append("🦁 Bravery")
            if flags.hypesquad_brilliance:
                badges.append("💡 Brilliance")
            if flags.active_developer:
                badges.append("👨‍💻 Active Developer")
            if flags.verified_bot:
                badges.append("🤖 Verified Bot")

            embed.add_field(
                name="User ID",
                value=f"`{member.id}`"
            )

            embed.add_field(
                name="Joined Server",
                value=f"<t:{int(member.joined_at.timestamp())}:F>"
            )

            embed.add_field(
                name="Account Created",
                value=f"<t:{int(member.created_at.timestamp())}:F>"
            )

            embed.add_field(
                name="Badges",
                value=", ".join(badges) if badges else "None",
                inline=False
            )

            embed.set_footer(text="Page 1/3 • Info")

            return embed

        # =========================
        # PAGE 2 - WARNINGS
        # =========================
        elif self.page == 1:

            data = load_punish()

            warns = data["Warns"].get(str(member.id))

            embed = discord.Embed(
                title=f"{member} • Warnings",
                color=EmbedColor
            )

            if not warns or not warns["WarnData"]:
                embed.description = "No warnings."

            else:

                desc = ""

                for wid, w in warns["WarnData"].items():
                    desc += f"**#{wid}** — {w['reason']}\n"

                embed.description = desc

            embed.set_footer(text="Page 2/3 • Warnings")

            return embed

        # =========================
        # PAGE 3 - ROLES
        # =========================
        else:

            embed = discord.Embed(
                title=f"{member} • Roles",
                color=EmbedColor
            )

            # DATABASE ROLES
            db_roles = []

            if os.path.exists(USERDATA_PATH):

                for file in os.listdir(USERDATA_PATH):

                    if not file.endswith("_user.json"):
                        continue

                    with open(f"{USERDATA_PATH}/{file}") as f:
                        data = json.load(f)

                    for r in data["roles"].values():

                        if member.id in r["users"]:
                            db_roles.append(r["label"])

            embed.add_field(
                name="Database Roles",
                value=", ".join(db_roles) if db_roles else "None",
                inline=False
            )

            # NORMAL SERVER ROLES
            roles = [r.mention for r in member.roles if r.name != "@everyone"]

            embed.add_field(
                name="Server Roles",
                value=", ".join(roles) if roles else "None",
                inline=False
            )

            embed.set_footer(text="Page 3/3 • Roles")

            return embed

    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):

        self.page = (self.page - 1) % 3

        embed = await self.build_embed()

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):

        self.page = (self.page + 1) % 3

        embed = await self.build_embed()

        await interaction.response.edit_message(embed=embed, view=self)


class Public(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @app_commands.command(name="profile", description="View User Profile")
    async def profile(
        self,
        interaction: Interaction,
        user: Optional[discord.Member] = None
    ):

        if user is None:
            user = interaction.user

        view = ProfileView(self.bot, user)

        embed = await view.build_embed()

        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True
        )
    @app_commands.command(name="databaseping", description="Ping Users With A Database Role")
    @app_commands.describe(role_id="Fake Role ID From Database")
    async def databaseping(
        self,
        interaction: Interaction,
        role_id: str
    ):

        if not perm_check(interaction, "selfrole"):
            await interaction.response.send_message(
                "You Don't Have Permission.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        users_to_ping = []

        if not os.path.exists(USERDATA_PATH):
            await interaction.followup.send(
                "Database Roles Folder Not Found.",
                ephemeral=True
            )
            return

        for file in os.listdir(USERDATA_PATH):

            if not file.endswith("_user.json"):
                continue

            with open(f"{USERDATA_PATH}/{file}") as f:
                data = json.load(f)

            if role_id in data["roles"]:
                users_to_ping = data["roles"][role_id]["users"]
                break

        if not users_to_ping:
            await interaction.followup.send(
                "No Users Found With This Database Role.",
                ephemeral=True
            )
            return

        await interaction.followup.send(
            f"Pinging {len(users_to_ping)} Users...",
            ephemeral=True
        )

        for uid in users_to_ping:

            try:
                msg = await interaction.channel.send(f"<@{uid}>")
                await asyncio.sleep(3)
                await msg.delete()
                await asyncio.sleep(1)
            except:
                pass
    @app_commands.command(name="selfmute", description="Mute Yourself For A Duration")
    @app_commands.describe(duration="Duration (e.g. 10m, 1h, 1d)")
    async def selfmute(
        self,
        interaction: Interaction,
        duration: str
    ):

        await interaction.response.defer(ephemeral=True)

        logger = self.bot.get_cog("Logger")

        user = interaction.user
        actor = f"{user} ({user.id})"

        # =========================
        # PARSE DURATION
        # =========================

        seconds = parse_duration(duration)

        if seconds is None:
            await interaction.followup.send(
                "Invalid Duration Format.",
                ephemeral=True
            )
            return

        # =========================
        # CHECK IF ALREADY MUTED
        # =========================

        if user.timed_out_until and user.timed_out_until > discord.utils.utcnow():
            await interaction.followup.send(
                "You Are Already Muted.",
                ephemeral=True
            )
            return

        until = discord.utils.utcnow() + timedelta(seconds=seconds)

        # =========================
        # APPLY TIMEOUT
        # =========================

        try:
            await user.timeout(
                until,
                reason="Self Mute"
            )

        except discord.Forbidden:
            await interaction.followup.send(
                "I Cannot Mute You.",
                ephemeral=True
            )
            return

        # =========================
        # LOGGING
        # =========================

        log.action(
            "Self Mute",
            f"{actor} Muted Themselves For {duration}"
        )

        if logger:
            await logger.send_webhook(
                "PUBLIC",
                "Self Mute",
                f"{actor} Muted Themselves\nDuration: {duration}"
            )

        # =========================
        # RESPONSE
        # =========================

        embed = discord.Embed(
            title="You Are Muted",
            description=f"You Muted Yourself For **{duration}**.",
            color=EmbedColor
        )

        await interaction.followup.send(embed=embed, ephemeral=True)
    
    
    @app_commands.command(name="reportuser", description="Report A User")
    async def reportuser(self, interaction: Interaction):

     modal = ReportModal(self.bot)

     await interaction.response.send_modal(modal)

    @app_commands.command(name="guidebook", description="View The Guidebook")
    async def guidebook(self, interaction: Interaction):
        await interaction.response.send_message(
            "Here Is The Guidebook: <https://gist.github.com/maybeninja/69e85a17aa494e05cb79fac86fcc859d>",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Public(bot))

