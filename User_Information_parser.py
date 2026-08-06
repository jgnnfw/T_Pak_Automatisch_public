import configparser
import sys
from pathlib import Path

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
