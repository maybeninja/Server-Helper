from utils import *
from config import *
from Cogs.permission import perm_check, admin_check

import discord
from discord.ext import commands, tasks
from discord import app_commands
import json, os, math, random

GUILD_ID = ServerID

ROLEMENU_PATH = "Database/RoleMenu"
USERDATA_PATH = "Database/RoleMenu/UserData"
STATE_PATH = "Database/state.json"

ITEMS_PER_PAGE = 10


class RoleDataView(discord.ui.View):
    def __init__(self, roles_list, menu_name):
        super().__init__(timeout=120)
        self.roles_list = roles_list
        self.menu_name = menu_name
        self.page = 0
        self.max_page = max(0, math.ceil(len(roles_list) / ITEMS_PER_PAGE) - 1)

    def get_embed(self):
        start = self.page * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        chunk = self.roles_list[start:end]

        embed = discord.Embed(
            title=f"Fake Roles — {self.menu_name} (Page {self.page+1}/{self.max_page+1})",
            color=EmbedColor
        )

        for rid, label in chunk:
            embed.add_field(name=rid, value=label, inline=False)

        return embed

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def prev(self, interaction: discord.Interaction, button):
        if self.page > 0:
            self.page -= 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button):
        if self.page < self.max_page:
            self.page += 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)


class RoleSelect(discord.ui.Select):

    def __init__(self, cog, menu_name, menu_data):
        self.cog = cog
        self.menu_name = menu_name
        self.menu_data = menu_data

        options = [
            discord.SelectOption(
                label=o["label"],
                value=o["label"],
                description=o.get("description", "No description.")
            )
            for o in menu_data["options"]
        ]

        super().__init__(
            placeholder=menu_data["placeholder"],
            min_values=0,
            max_values=menu_data["max_values"],
            options=options
        )

    async def callback(self, interaction: discord.Interaction):

        member = interaction.user
        guild = interaction.guild
        menu_type = self.menu_data["type"]

        added, removed = [], []

        if menu_type == "role":

            for label in self.values:
                role = discord.utils.get(guild.roles, name=label)

                if role is None:
                    role = await guild.create_role(name=label)

                if role in member.roles:
                    await member.remove_roles(role)
                    removed.append(label)
                else:
                    await member.add_roles(role)
                    added.append(label)

        else:

            file = f"{USERDATA_PATH}/{self.menu_name.replace('.json','')}_user.json"

            if not os.path.exists(file):
                data = {"roles": {}}
            else:
                with open(file) as f:
                    data = json.load(f)

            for label in self.values:

                role_id = None

                for rid, r in data["roles"].items():
                    if r["label"] == label:
                        role_id = rid
                        break

                if role_id is None:
                    role_id = str(random.randint(10**17, 10**18 - 1))
                    data["roles"][role_id] = {"label": label, "users": []}

                users = data["roles"][role_id]["users"]

                if member.id in users:
                    users.remove(member.id)
                    removed.append(label)
                else:
                    users.append(member.id)
                    added.append(label)

            with open(file, "w") as f:
                json.dump(data, f, indent=2)

        msg = ""
        if added:
            msg += f"✅ Added: {', '.join(added)}\n"
        if removed:
            msg += f"❌ Removed: {', '.join(removed)}"

        await interaction.response.send_message(msg or "No changes.", ephemeral=True)


class MenuView(discord.ui.View):

    def __init__(self, cog, menu_name, menus):
        super().__init__(timeout=None)

        for m in menus:
            self.add_item(RoleSelect(cog, menu_name, m))


class SelfRole(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        os.makedirs(ROLEMENU_PATH, exist_ok=True)
        os.makedirs(USERDATA_PATH, exist_ok=True)

        if not os.path.exists(STATE_PATH):
            with open(STATE_PATH, "w") as f:
                json.dump({"SelfRole": {}}, f, indent=2)

        # ✅ Load persistent views properly
        for file in os.listdir(ROLEMENU_PATH):
            if file.endswith(".json"):
                try:
                    with open(f"{ROLEMENU_PATH}/{file}") as f:
                        data = json.load(f)
                    self.bot.add_view(MenuView(self, file, data["menus"]))
                except:
                    pass

        self.refresh_loop.start()

    def load_state(self):
        with open(STATE_PATH) as f:
            return json.load(f)

    def save_state(self, data):
        with open(STATE_PATH, "w") as f:
            json.dump(data, f, indent=2)

    # ✅ FIXED duplicate cleaner
    async def delete_duplicates(self, channel):

        state = self.load_state()
        valid_ids = set()

        for menu, data in state["SelfRole"].items():
            if data["channel_id"] == channel.id:
                valid_ids.add(data["message_id"])

        try:
            async for msg in channel.history(limit=50):

                if msg.author != self.bot.user:
                    continue

                if msg.id not in valid_ids:
                    try:
                        await msg.delete()
                    except:
                        pass
        except:
            pass

    async def deploy_menu(self, file):

        path = f"{ROLEMENU_PATH}/{file}"

        with open(path) as f:
            data = json.load(f)

        guild = self.bot.get_guild(data["guild_id"])
        if guild is None:
            return

        channel = guild.get_channel(data["channel_id"])
        if channel is None:
            return

        embed = discord.Embed(
            title=data["title"],
            description=data["description"],
            color=EmbedColor
        )

        view = MenuView(self, file, data["menus"])

        state = self.load_state()
        entry = state["SelfRole"].get(file)

        msg = None

        if entry:
            try:
                msg = await channel.fetch_message(entry["message_id"])
            except:
                msg = None

        if msg:
            try:
                await msg.edit(embed=embed, view=view)
                await self.delete_duplicates(channel)
                return
            except:
                msg = None

        new_msg = await channel.send(embed=embed, view=view)

        state["SelfRole"][file] = {
            "guild_id": data["guild_id"],
            "channel_id": data["channel_id"],
            "message_id": new_msg.id
        }

        self.save_state(state)

        await self.delete_duplicates(channel)

    async def refresh_all(self):
        for file in os.listdir(ROLEMENU_PATH):
            if file.endswith(".json"):
                await self.deploy_menu(file)

    @tasks.loop(minutes=3)
    async def refresh_loop(self):
        await self.refresh_all()

    @refresh_loop.before_loop
    async def before_refresh_loop(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="addmenu")
    @commands.check(admin_check)
    async def addmenu(self, interaction: discord.Interaction, file: discord.Attachment):

        data = json.loads(await file.read())

        path = f"{ROLEMENU_PATH}/{file.filename}"

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        await self.deploy_menu(file.filename)

        await interaction.response.send_message("✅ Menu added.", ephemeral=True)

    @app_commands.command(name="removemenu")
    @commands.check(admin_check)
    async def removemenu(self, interaction: discord.Interaction, menu_name: str):

        state = self.load_state()
        entry = state["SelfRole"].pop(menu_name, None)

        if entry:
            try:
                guild = self.bot.get_guild(entry["guild_id"])
                channel = guild.get_channel(entry["channel_id"])
                msg = await channel.fetch_message(entry["message_id"])
                await msg.delete()
            except:
                pass

        self.save_state(state)

        try:
            os.remove(f"{ROLEMENU_PATH}/{menu_name}")
        except:
            pass

        await interaction.response.send_message("🗑 Menu removed.", ephemeral=True)

    @app_commands.command(name="role_data")
    async def role_data(self, interaction: discord.Interaction, menu_name: str):

        if not perm_check(interaction, permission_name="selfrole"):
            return

        file = f"{USERDATA_PATH}/{menu_name.replace('.json','')}_user.json"

        if not os.path.exists(file):
            return await interaction.response.send_message(
                "No database roles.",
                ephemeral=True
            )

        with open(file) as f:
            data = json.load(f)

        roles = data.get("roles", {})
        if not roles:
            return await interaction.response.send_message(
                "No roles found in database.",
                ephemeral=True
            )

        roles_list = [(rid, r.get("label", "No Label")) for rid, r in roles.items()]

        view = RoleDataView(roles_list, menu_name)
        embed = view.get_embed()

        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(SelfRole(bot))