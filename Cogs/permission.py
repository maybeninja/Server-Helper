from utils import *
from config import *
from .logger import log

# ==========================================
# PERMISSION CHECK DECORATOR
# ==========================================
def perm_check(interaction: Interaction, permission_name: str):

    # Allow admins automatically
    if admin_check(interaction):
        return True

    cog = interaction.client.get_cog("Permission")

    if not cog:
        return False

    perms = cog.permissions

    if permission_name not in perms:
        return False

    data = perms[permission_name]

    # User permission
    if interaction.user.id in data["UserIDs"]:
        return True

    # Role permission
    user_roles = [role.id for role in interaction.user.roles]

    if any(role_id in data["RoleIDs"] for role_id in user_roles):
        return True

    return False

# ==========================================
# PERMISSION COG
# ==========================================

class Permission(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        with open("Database/permission.json", "r") as f:
            self.permissions = json.load(f)


    # ==========================================
    # AUTOCOMPLETE
    # ==========================================

    async def permission_autocomplete(
        self,
        interaction: Interaction,
        current: str
    ):

        return [
            app_commands.Choice(name=perm, value=perm)
            for perm in self.permissions.keys()
            if current.lower() in perm.lower()
        ]


    # ==========================================
    # PERMISSION COMMAND
    # ==========================================

    @app_commands.check(admin_check)
    @app_commands.command(
        name="permission",
        description="Add Or Remove Permission Access"
    )

    @app_commands.describe(
        permission="Permission Name",
        action="Add Or Remove",
        user="User To Add Or Remove",
        role="Role To Add Or Remove"
    )

    @app_commands.choices(
        action=[
            app_commands.Choice(name="Add", value="add"),
            app_commands.Choice(name="Remove", value="remove")
        ]
    )

    @app_commands.autocomplete(permission=permission_autocomplete)

    async def permission(
        self,
        interaction: Interaction,
        permission: str,
        action: app_commands.Choice[str],
        user: Optional[discord.User] = None,
        role: Optional[discord.Role] = None
    ):

        logger = self.bot.get_cog("Logger")
        actor = f"{interaction.user} ({interaction.user.id})"


        if permission not in self.permissions:

            await interaction.response.send_message(
                "Invalid Permission.",
                ephemeral=True
            )
            return


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


        data = self.permissions[permission]


        # ==========================================
        # ADD
        # ==========================================

        if action.value == "add":

            if user:

                if user.id in data["UserIDs"]:

                    await interaction.response.send_message(
                        "This User Already Has This Permission.",
                        ephemeral=True
                    )
                    return

                data["UserIDs"].append(user.id)

                log.action(
                    "Permission Added",
                    f"{permission} -> {user} By {actor}"
                )

                if logger:
                    await logger.send_webhook(
                        "ACTION",
                        "Permission Added",
                        f"{permission} -> {user} ({user.id}) By {actor}"
                    )

                await interaction.response.send_message(
                    f"{user.mention} Added To `{permission}` Permission.",ephemeral=True
                )

            else:

                if role.id in data["RoleIDs"]:

                    await interaction.response.send_message(
                        "This Role Already Has This Permission.",
                        ephemeral=True
                    )
                    return

                data["RoleIDs"].append(role.id)

                log.action(
                    "Permission Role Added",
                    f"{permission} -> {role} By {actor}"
                )

                if logger:
                    await logger.send_webhook(
                        "ACTION",
                        "Permission Role Added",
                        f"{permission} -> {role} ({role.id}) By {actor}"
                    )

                await interaction.response.send_message(
                    f"{role.mention} Added To `{permission}` Permission.", ephemeral=True
                )


        # ==========================================
        # REMOVE
        # ==========================================

        else:

            if user:

                if user.id not in data["UserIDs"]:

                    await interaction.response.send_message(
                        "This User Does Not Have This Permission.",
                        ephemeral=True
                    )
                    return

                data["UserIDs"].remove(user.id)

                log.warn(
                    "Permission Removed",
                    f"{permission} -> {user} By {actor}"
                )

                if logger:
                    await logger.send_webhook(
                        "WARN",
                        "Permission Removed",
                        f"{permission} -> {user} ({user.id}) By {actor}"
                    )

                await interaction.response.send_message(
                    f"{user.mention} Removed From `{permission}` Permission." , ephemeral=True
                )

            else:

                if role.id not in data["RoleIDs"]:

                    await interaction.response.send_message(
                        "This Role Does Not Have This Permission.",
                        ephemeral=True
                    )
                    return

                data["RoleIDs"].remove(role.id)

                log.warn(
                    "Permission Role Removed",
                    f"{permission} -> {role} By {actor}"
                )

                if logger:
                    await logger.send_webhook(
                        "WARN",
                        "Permission Role Removed",
                        f"{permission} -> {role} ({role.id}) By {actor}"
                    )

                await interaction.response.send_message(
                    f"{role.mention} Removed From `{permission}` Permission." , ephemeral=True
                )


        # ==========================================
        # SAVE DATABASE
        # ==========================================

        with open("Database/permission.json", "w") as f:
            json.dump(self.permissions, f, indent=4)


    # ==========================================
    # PERMISSION LIST
    # ==========================================
    @app_commands.check(admin_check)
    @app_commands.command(
        name="permission_list",
        description="List All Bot Permissions"
    )

    async def permission_list(self, interaction: Interaction):

        perms = "\n".join(
            f"• `{perm}`" for perm in self.permissions.keys()
        )

        embed = discord.Embed(
            title="Bot Permissions",
            description=perms,
            color=EmbedColor
        )

        await interaction.response.send_message(embed=embed, ephemeral=True) 


# ==========================================
# SETUP
# ==========================================

async def setup(bot):
    await bot.add_cog(Permission(bot))