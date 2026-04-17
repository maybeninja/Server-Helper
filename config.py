from yaml import safe_load


botowner = open("Database/owners.txt" , "r").read().splitlines()
settings = safe_load(open("settings.yaml" , "r"))

Token = settings["Token"]
Activites = settings["Activities"]
ActivityInterval = settings["ActivityInterval"]
NoticeWebhook = settings["NoticeWebhook"]
ServerID = settings["ServerID"]

def get_embed_color(color_value):
    
    if isinstance(color_value, int):
        return color_value

    if isinstance(color_value, str):
        color_value = color_value.replace("#", "")
        return int(color_value, 16)

    return 0xffffff

EmbedColor = get_embed_color(settings["EmbedColor"])
DefaultStaffRole = settings["DefaultStaffRole"]
StaffAnnouncementChannel = settings["StaffAnnouncementChannel"]


Version =  settings["Version"]
SupportServer = settings["SupportServer"]
Developer = settings["Developer"]
