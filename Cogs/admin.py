from utils import *
from config import *
from Cogs.logger import log





with open("Database/admins.json", "r") as f:
    admins = json.load(f)


# ===============================
# OWNER CHECK
# ===============================

def owner_check(interaction: Interaction):
    if interaction.user.id not in [int(x) for x in botowner]:
        return False
    return True


# ===============================
# ADMIN CHECK
# ===============================

def admin_check(interaction: Interaction):

    with open("Database/admins.json", "r") as f:
        admins = json.load(f)

    if interaction.user.id in [int(x) for x in botowner]:
        return True

    if interaction.user.id in admins["UserIDs"]:
        return True

    user_roles = [role.id for role in interaction.user.roles]

    if any(role_id in admins["RoleIDs"] for role_id in user_roles):
        return True

    return False

# ===============================
# ADMIN COG
# ===============================

class Admin(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @app_commands.check(owner_check)
    @app_commands.command(
        name="admin",
        description="Add Or Remove An Admin To The Bot"
    )
    @app_commands.describe(
        user="User To Add Or Remove As Admin",
        role="Role To Add Or Remove As Admin",
        action="Add Or Remove"
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Add", value="add"),
            app_commands.Choice(name="Remove", value="remove")
        ]
    )
    async def admin(
        self,
        interaction: Interaction,
        user: Optional[discord.User],
        role: Optional[discord.Role],
        action: app_commands.Choice[str]
    ):

        logger = self.bot.get_cog("Logger")
        actor = f"{interaction.user} ({interaction.user.id})"


        if not user and not role:
            await interaction.response.send_message(
                "You Must Provide Either A User Or A Role.",
                ephemeral=True
            )
            return


        if user and role:
            await interaction.response.send_message(
                "You Cannot Provide Both A User And A Role.",
                ephemeral=True
            )
            return


        # ===============================
        # ADD
        # ===============================

        if action.value == "add":

            if user:

                if user.id in admins["UserIDs"]:
                    await interaction.response.send_message(
                        "This User Is Already An Admin.",
                        ephemeral=True
                    )
                    return

                admins["UserIDs"].append(user.id)

                log.action("Admin Added", f"{user} By {actor}")

                if logger:
                    await logger.send_webhook(
                        "ACTION",
                        "Admin Added",
                        f"{user} ({user.id}) By {actor}"
                    )

            else:

                if role.id in admins["RoleIDs"]:
                    await interaction.response.send_message(
                        "This Role Is Already An Admin.",
                        ephemeral=True
                    )
                    return

                admins["RoleIDs"].append(role.id)

                log.action("Admin Role Added", f"{role} By {actor}")

                if logger:
                    await logger.send_webhook(
                        "ACTION",
                        "Admin Role Added",
                        f"{role} ({role.id}) By {actor}"
                    )


        # ===============================
        # REMOVE
        # ===============================

        else:

            if user:

                if user.id not in admins["UserIDs"]:
                    await interaction.response.send_message(
                        "This User Is Not An Admin.",
                        ephemeral=True
                    )
                    return

                admins["UserIDs"].remove(user.id)

                log.warn("Admin Removed", f"{user} By {actor}")

                if logger:
                    await logger.send_webhook(
                        "WARN",
                        "Admin Removed",
                        f"{user} ({user.id}) By {actor}"
                    )

            else:

                if role.id not in admins["RoleIDs"]:
                    await interaction.response.send_message(
                        "This Role Is Not An Admin.",
                        ephemeral=True
                    )
                    return

                admins["RoleIDs"].remove(role.id)

                log.warn("Admin Role Removed", f"{role} By {actor}")

                if logger:
                    await logger.send_webhook(
                        "WARN",
                        "Admin Role Removed",
                        f"{role} ({role.id}) By {actor}"
                    )


        # ===============================
        # SAVE DATABASE
        # ===============================

        with open("Database/admins.json", "w") as f:
            json.dump(admins, f, indent=4)


        target = user.mention if user else role.mention
        action_word = "Added As" if action.value == "add" else "Removed From"


        await interaction.response.send_message(
            f"{target} Has Been {action_word} Bot Admins.",
            ephemeral=True
        )


# ===============================
# SETUP
# ===============================

async def setup(bot):
    await bot.add_cog(Admin(bot))
