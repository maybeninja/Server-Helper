from utils import *
from config import *
from Cogs.logger import log
from Cogs.permission import admin_check


STATE_FILE = "Database/state.json"
COLOUR_FILE = "Database/colourroles.json"
IMAGE_FILE = "Database/colour_roles.png"


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def get_colour_hash():
    if not os.path.exists(COLOUR_FILE):
        return None
    with open(COLOUR_FILE, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def get_text_color(hex_color):
    hex_color = hex_color.replace("#", "")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    brightness = (r * 299 + g * 587 + b * 114) / 1000
    return "black" if brightness > 150 else "white"


def generate_image(colours):
    items = list(colours.items())
    total = len(items)

    cols = min(8, max(4, math.ceil(math.sqrt(total))))
    rows = math.ceil(total / cols)

    BOX = 130
    PAD = 30
    RADIUS = 28

    width = cols * BOX + (cols + 1) * PAD
    height = rows * BOX + (rows + 1) * PAD

    img = Image.new("RGBA", (width, height), "#1e1f22")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except:
        font = ImageFont.load_default()

    for i, (num, colour) in enumerate(items):

        r_i = i // cols
        c_i = i % cols

        x = PAD + c_i * (BOX + PAD)
        y = PAD + r_i * (BOX + PAD)

        shadow = Image.new("RGBA", (BOX, BOX), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(shadow)

        sdraw.rounded_rectangle([6, 6, BOX, BOX], radius=RADIUS, fill=(0, 0, 0, 90))
        shadow = shadow.filter(ImageFilter.GaussianBlur(6))
        img.alpha_composite(shadow, (x, y))

        square = Image.new("RGBA", (BOX, BOX), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(square)

        sdraw.rounded_rectangle([0, 0, BOX, BOX], radius=RADIUS, fill=colour)
        img.alpha_composite(square, (x, y))

        text = str(num)
        bbox = draw.textbbox((0, 0), text, font=font)

        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        draw.text(
            (x + (BOX - tw) / 2, y + (BOX - th) / 2),
            text,
            fill=get_text_color(colour),
            font=font
        )

    img.convert("RGB").save(IMAGE_FILE)


class ColourModal(Modal):

    def __init__(self):
        super().__init__(title="Choose Colour")

        self.number = TextInput(
            label="Enter Colour Number (0 to remove)",
            placeholder="Example: 5",
            required=True
        )

        self.add_item(self.number)

    async def on_submit(self, interaction: discord.Interaction):

        colours = load_json(COLOUR_FILE, {})

        try:
            num = int(self.number.value)
        except:
            await interaction.response.send_message("Invalid number.", ephemeral=True)
            return

        member = interaction.user

        if num == 0:
            roles_to_remove = [r for r in member.roles if r.name.startswith("Colour - ")]
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove)

            await interaction.response.send_message("Colour removed.", ephemeral=True)
            return

        if str(num) not in colours:
            await interaction.response.send_message("That colour does not exist.", ephemeral=True)
            return

        hex_colour = colours[str(num)]
        role_name = f"Colour - {num}"

        role = discord.utils.get(interaction.guild.roles, name=role_name)

        if role is None:
            role = await interaction.guild.create_role(
                name=role_name,
                colour=discord.Colour(int(hex_colour.replace("#", ""), 16))
            )

        roles_to_remove = [r for r in member.roles if r.name.startswith("Colour - ")]
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove)

        await member.add_roles(role)

        await interaction.response.send_message(f"Colour {num} applied.", ephemeral=True)


class ColourView(View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Set Colour",
        style=discord.ButtonStyle.primary,
        custom_id="colour_role_button"
    )
    async def button(self, interaction: discord.Interaction, button):
        await interaction.response.send_modal(ColourModal())


class Colors(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(ColourView())
        self.refresh_panel.start()

    def get_state(self):
        state = load_json(STATE_FILE, {})
        if "ColourRoles" not in state:
            state["ColourRoles"] = {}
        return state

    def save_state(self, state):
        save_json(STATE_FILE, state)

    async def build_embed(self):

        embed = discord.Embed(
            title="Choose Your Colour",
            description="Click **Set Colour** and enter the number.\nEnter **0** to remove your colour.",
            color=EmbedColor
        )

        file = discord.File(IMAGE_FILE, filename="colours.png")
        embed.set_image(url="attachment://colours.png")

        return embed, file

    async def cleanup_unused_roles(self, guild):

        for role in guild.roles:

            if role.name.startswith("Colour - "):

                if len(role.members) == 0:
                    try:
                        await role.delete(reason="Unused colour role cleanup")
                    except:
                        pass

    async def delete_duplicate_panels(self, channel, valid_message_id):

        try:
            async for msg in channel.history(limit=50):
                if msg.id != valid_message_id and msg.author == self.bot.user:
                    try:
                        await msg.delete()
                    except:
                        pass
        except:
            pass

    @app_commands.command(name="colormenu", description="Create colour role panel")
    @app_commands.check(admin_check)
    async def colormenu(self, interaction: discord.Interaction, channel: discord.TextChannel, json_file: discord.Attachment):

        await interaction.response.defer(thinking=True)

        logger = self.bot.get_cog("Logger")
        actor = f"{interaction.user} ({interaction.user.id})"

        if not json_file.filename.endswith(".json"):
            await interaction.followup.send("Upload a valid JSON file.", ephemeral=True)
            return

        data = await json_file.read()

        try:
            colours = json.loads(data.decode())
        except:
            await interaction.followup.send("Invalid JSON.", ephemeral=True)
            return

        save_json(COLOUR_FILE, colours)
        generate_image(colours)

        state = self.get_state()
        state["ColourRolesHash"] = get_colour_hash()

        guild_id = str(interaction.guild.id)
        old = state["ColourRoles"].get(guild_id)

        embed, file = await self.build_embed()
        view = ColourView()

        if old:
            try:
                old_channel = self.bot.get_channel(old["channel"])
                msg = await old_channel.fetch_message(old["message"])
            except:
                msg = None

            if msg:
                try:
                    if old["channel"] != channel.id:
                        await msg.delete()
                        sent = await channel.send(embed=embed, file=file, view=view)
                    else:
                        await msg.edit(embed=embed, attachments=[file], view=view)
                        sent = msg
                except:
                    sent = await channel.send(embed=embed, file=file, view=view)
            else:
                sent = await channel.send(embed=embed, file=file, view=view)
        else:
            sent = await channel.send(embed=embed, file=file, view=view)

        state["ColourRoles"][guild_id] = {
            "channel": channel.id,
            "message": sent.id
        }

        self.save_state(state)

        await self.delete_duplicate_panels(channel, sent.id)
        await self.cleanup_unused_roles(interaction.guild)

        await interaction.followup.send("Colour Panel Created.", ephemeral=True)

        log.action("Colour Panel Created", f"Channel: {channel} ({channel.id}) By {actor}")

        if logger:
            await logger.send_webhook(
                "ACTION",
                "Colour Panel Created",
                f"Channel: {channel} ({channel.id}) By {actor}"
            )

    @tasks.loop(minutes=4)
    async def refresh_panel(self):

        await self.bot.wait_until_ready()

        state = self.get_state()
        colours = load_json(COLOUR_FILE, {})
        current_hash = get_colour_hash()

        if state.get("ColourRolesHash") != current_hash:
            generate_image(colours)
            state["ColourRolesHash"] = current_hash
            self.save_state(state)

        for guild_id, data in state["ColourRoles"].items():

            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                continue

            await self.cleanup_unused_roles(guild)

            channel = self.bot.get_channel(data["channel"])
            if not channel:
                continue

            try:
                msg = await channel.fetch_message(data["message"])
            except:
                msg = None

            embed, file = await self.build_embed()
            view = ColourView()

            if msg:
                try:
                    await msg.edit(embed=embed, attachments=[file], view=view)
                    await self.delete_duplicate_panels(channel, msg.id)
                except:
                    new_msg = await channel.send(embed=embed, file=file, view=view)
                    data["message"] = new_msg.id
                    self.save_state(state)
                    await self.delete_duplicate_panels(channel, new_msg.id)
            else:
                new_msg = await channel.send(embed=embed, file=file, view=view)
                data["message"] = new_msg.id
                self.save_state(state)
                await self.delete_duplicate_panels(channel, new_msg.id)


async def setup(bot):
    await bot.add_cog(Colors(bot))