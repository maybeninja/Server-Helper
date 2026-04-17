
from utils import *
from config import *
from Cogs.permission import admin_check
from Cogs.logger import log

STAFF_PATH = "Database/staff.json"


def load_staff():
    if not os.path.exists(STAFF_PATH):
        os.makedirs("Database", exist_ok=True)

        with open(STAFF_PATH, "w") as f:
            json.dump({}, f, indent=4)

    with open(STAFF_PATH, "r") as f:
        return json.load(f)


def save_staff(data):
    with open(STAFF_PATH, "w") as f:
        json.dump(data, f, indent=4)


class Staffing(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


# ==========================================
# STAFFROLE ADD / REMOVE
# ==========================================

    @app_commands.command(name="staffrole", description="Register Or Remove Staff Roles")
    @app_commands.describe(
        action="Add Or Remove",
        role="Staff Role"
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Add", value="add"),
            app_commands.Choice(name="Remove", value="remove")
        ]
    )
    async def staffrole(self, interaction: Interaction, action: app_commands.Choice[str], role: discord.Role):

        if not admin_check(interaction):
            await interaction.response.send_message(
                "Admin Only Command.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        logger = self.bot.get_cog("Logger")
        actor = f"{interaction.user} ({interaction.user.id})"

        data = load_staff()
        role_id = str(role.id)

        if action.value == "add":

            if role_id in data:
                await interaction.followup.send("Role Already Registered.", ephemeral=True)
                return

            data[role_id] = {
                "name": role.name,
                "staffIDs": []
            }

            save_staff(data)

            log.action(
                "Staff Role Added",
                f"{role.name} ({role.id}) Added By {actor}"
            )

            if logger:
                await logger.send_webhook(
                    "STAFF",
                    "Staff Role Added",
                    f"{role.name} ({role.id}) Added By {actor}"
                )

            await interaction.followup.send(
                f"{role.mention} Added As Staff Role.",
                ephemeral=True
            )

        else:

            if role_id not in data:
                await interaction.followup.send("Role Not Registered.", ephemeral=True)
                return

            del data[role_id]
            save_staff(data)

            log.action(
                "Staff Role Removed",
                f"{role.name} ({role.id}) Removed By {actor}"
            )

            if logger:
                await logger.send_webhook(
                    "STAFF",
                    "Staff Role Removed",
                    f"{role.name} ({role.id}) Removed By {actor}"
                )

            await interaction.followup.send(
                f"{role.mention} Removed From Staff Roles.",
                ephemeral=True
            )


# ==========================================
# STAFF ADD / REMOVE
# ==========================================

    @app_commands.command(name="staff", description="Add Or Remove Staff")
    @app_commands.describe(
        action="Add Or Remove",
        role="Staff Role",
        user="User"
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Add", value="add"),
            app_commands.Choice(name="Remove", value="remove")
        ]
    )
    async def staff(self, interaction: Interaction, action: app_commands.Choice[str], role: discord.Role, user: discord.Member):

        if not admin_check(interaction):
            await interaction.response.send_message(
                "Admin Only Command.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        logger = self.bot.get_cog("Logger")
        actor = f"{interaction.user} ({interaction.user.id})"

        data = load_staff()
        role_id = str(role.id)

        if role_id not in data:
            await interaction.followup.send(
                "This Role Is Not Registered As Staff Role.",
                ephemeral=True
            )
            return

        default_role = interaction.guild.get_role(DefaultStaffRole)
        announce = interaction.guild.get_channel(StaffAnnouncementChannel)

        if action.value == "add":

            if user.id in data[role_id]["staffIDs"]:
                await interaction.followup.send("User Already Staff.", ephemeral=True)
                return

            data[role_id]["staffIDs"].append(user.id)

            await user.add_roles(role)
            await user.add_roles(default_role)

            save_staff(data)

            if announce:
                await announce.send(
                    f"🎉 {user.mention} Has Joined The Staff Team As {role.mention}"
                )

            log.action(
                "Staff Added",
                f"{user} ({user.id}) Added As {role.name} By {actor}"
            )

            if logger:
                await logger.send_webhook(
                    "STAFF",
                    "Staff Added",
                    f"{user} ({user.id}) Added As {role.name} By {actor}"
                )

            await interaction.followup.send(
                f"{user.mention} Added As {role.name}.",
                ephemeral=True
            )

        else:

            if user.id not in data[role_id]["staffIDs"]:
                await interaction.followup.send("User Is Not Staff.", ephemeral=True)
                return

            data[role_id]["staffIDs"].remove(user.id)

            await user.remove_roles(role)
            await user.remove_roles(default_role)

            save_staff(data)

            if announce:
                await announce.send(
                    f"{user.mention} Has Been Removed From The Staff Team."
                )

            log.action(
                "Staff Removed",
                f"{user} ({user.id}) Removed From Staff By {actor}"
            )

            if logger:
                await logger.send_webhook(
                    "STAFF",
                    "Staff Removed",
                    f"{user} ({user.id}) Removed From Staff By {actor}"
                )

            await interaction.followup.send(
                f"{user.mention} Removed From Staff.",
                ephemeral=True
            )


# ==========================================
# STAFF LIST
# ==========================================

    @app_commands.command(name="stafflist", description="View Staff Members Of A Role")
    async def stafflist(self, interaction: Interaction, role: discord.Role):

        if not admin_check(interaction):
            await interaction.response.send_message(
                "Admin Only Command.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        data = load_staff()
        role_id = str(role.id)

        if role_id not in data:
            await interaction.followup.send("Role Not Registered.", ephemeral=True)
            return

        staff_ids = data[role_id]["staffIDs"]

        if not staff_ids:
            await interaction.followup.send("No Staff In This Role.", ephemeral=True)
            return

        members = "\n".join([f"<@{uid}>" for uid in staff_ids])

        embed = discord.Embed(
            title=f"{role.name} Staff",
            description=members,
            color=EmbedColor
        )

        await interaction.followup.send(embed=embed, ephemeral=True)


# ==========================================
# STAFF POSITION CHANGE
# ==========================================

    @app_commands.command(name="staffposition", description="Change Staff Position")
    async def staffposition(self, interaction: Interaction, role: discord.Role, user: discord.Member):

        if not admin_check(interaction):
            await interaction.response.send_message(
                "Admin Only Command.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        logger = self.bot.get_cog("Logger")
        actor = f"{interaction.user} ({interaction.user.id})"

        data = load_staff()

        current_role_id = None

        for rid in data:
            if user.id in data[rid]["staffIDs"]:
                current_role_id = rid

        if not current_role_id:
            await interaction.followup.send("User Is Not Staff.", ephemeral=True)
            return

        new_role_id = str(role.id)

        if new_role_id not in data:
            await interaction.followup.send("Role Not Registered As Staff Role.", ephemeral=True)
            return

        old_role = interaction.guild.get_role(int(current_role_id))

        data[current_role_id]["staffIDs"].remove(user.id)
        data[new_role_id]["staffIDs"].append(user.id)

        await user.remove_roles(old_role)
        await user.add_roles(role)

        save_staff(data)

        announce = interaction.guild.get_channel(StaffAnnouncementChannel)

        if announce:
            await announce.send(
                f"⭐ {user.mention} Has Been Promoted To {role.mention}"
            )

        log.action(
            "Staff Position Changed",
            f"{user} ({user.id}) Promoted To {role.name} By {actor}"
        )

        if logger:
            await logger.send_webhook(
                "STAFF",
                "Staff Position Changed",
                f"{user} ({user.id}) Promoted To {role.name} By {actor}"
            )

        await interaction.followup.send(
            f"{user.mention} Position Updated To {role.name}.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Staffing(bot))

