import discord , yaml , os , discord_webhook , datetime , time , random , string , aiohttp , asyncio , json , requests 
from discord.ext import commands , tasks 
from discord import Embed , File , Webhook , app_commands , Interaction 
from discord.ui import Button , View , Select , Modal , TextInput , DynamicItem , RoleSelect , UserSelect , ChannelSelect
from discord.utils import get , find
from discord.ext.commands import has_permissions , MissingPermissions , CheckFailure , CommandNotFound , BadArgument , MissingRequiredArgument , CommandOnCooldown , TooManyArguments , UserInputError
from discord.errors import Forbidden , NotFound , HTTPException , DiscordException
from typing_extensions import Self , Literal , List , Optional , Union 
from yaml import safe_load , dump
from datetime import datetime , timedelta



from colorama import Fore, init

import math
import hashlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def change_settings(key , value):
    with open("settings.yaml" , "r") as f:
        data = yaml.safe_load(f)
    data[key] = value
    with open("settings.yaml" , "w") as f:
        yaml.dump(data , f)


from Cogs.logger import *
from Cogs.admin import admin_check

from colorama import Fore, init