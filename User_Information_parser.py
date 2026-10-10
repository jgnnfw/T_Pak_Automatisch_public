import configparser
import sys
from pathlib import Path
import requests

def get_config():
    if getattr(sys, "frozen", False):
        base_dir = Path(sys.executable).parent
    else:
        base_dir = Path(__file__).resolve().parent

    config_path = base_dir / "User_Sensible_Information.ini"
    config = configparser.ConfigParser(interpolation=None)

    if not config.read(config_path):
        raise FileNotFoundError(f"Could not find configuration file: {config_path}")

    return config

def get_name():
    return get_config()["name"]["name"]

def get_email():
    return get_config()["garmin"]["email"]

def get_password():
    return get_config()["garmin"]["password"]

def get_login():
    login = requests.post(
        "https://www.t-pak.ch/api/authenticate/login",
        data = {"username": get_config()["t_pak"]["user_name"],
                "password": get_config()["t_pak"]["password"],}
    )

    if not login.ok:
        print("T-Pak Login Failed")
        raise ValueError("T-Pak Login Failed")

    user_id = login.json()["userId"]
    if type(user_id) is tuple:
        user_id = str(user_id[0])
    token = str(login.json()["token"])

    return user_id, token

def get_token():
    user_id, token = get_login()
    return token

def get_user_id():
    user_id, token = get_login()
    return user_id

def get_default_trainingsgefaess():
    return get_config()["settings"]["default_trainingsgefaess"]

DEFAULT_TRAININGSGEFAESS = get_default_trainingsgefaess()
