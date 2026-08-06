import configparser
import os
import sys

def get_config():
    base_dir = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else __file__)
    config = configparser.ConfigParser(interpolation=None)
    config.read(os.path.join(base_dir, "User_Sensible_Information.ini"))
    return config

def get_email():
    return get_config()["garmin"]["email"]

def get_password():
    return get_config()["garmin"]["password"]

def get_token():
    return get_config()["t_pak"]["token"]

def get_user_id():
    return int(get_config()["t_pak"]["user_id"])

def get_default_trainingsgefaess():
    return get_config()["settings"]["default_trainingsgefaess"]

DEFAULT_TRAININGSGEFAESS = get_default_trainingsgefaess()
