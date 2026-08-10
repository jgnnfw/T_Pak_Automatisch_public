from time import sleep
import requests
from fitparse import FitFile
from User_Information_parser import get_token, get_user_id
from fit_parser import get_time, get_intensity_ranges, get_activity_parameters, get_location, get_session_field
from typing import Any
from garmin_to_t_pak import MAIN_DURATION_SUBACTIVITY, t_pak_id_mapper
from datetime import date

TPAK_URL = "https://www.t-pak.ch/api/activities"
TOKEN = get_token()
USER_ID = get_user_id()


def upload_to_t_pak(
        fit_bytes, given_activity_type : str,
        activity : dict[str, Any],
        details : dict[str, Any],
        debug : bool = False
) -> tuple[int, dict] | tuple[str, dict] | tuple[int | None, str]:
    """
    Post an activity to t-pak.
    :param fit_bytes: unzipped non-converted fitfile in bytes format
    :param given_activity_type: activity type given by author/mapping
    :param activity: dictionary with activity parameters
    :param details: dictionary with activity details
    :param debug: if True, no activity is posted to the t-pak api and headers and payload are returned for inspection.
    :return: status code or error text and payload (if debug is False)
    """
    fitfile = FitFile(fit_bytes)

    start_time = get_session_field(fitfile, "start_time")  # datetime object
    if start_time is None:
        raise ValueError("No date can be assigned since start_time is missing!")
    date = start_time.strftime("%Y-%m-%d")

    activity_type_id = t_pak_id_mapper(given_activity_type)
    sub_activity_type_id = MAIN_DURATION_SUBACTIVITY.get(activity_type_id, activity_type_id)
    if activity_type_id is None:
        raise TypeError("Activity type does not exist!")

    intensity_ranges = get_intensity_ranges(fitfile, activity)

    parameters = [{"activityParameterId" : k,
                   "value" : v}
                  for k, v in get_activity_parameters(fitfile).items()
                  if k is not None and v is not None]

    time_min = get_time(fitfile) / 60

    payload = {
        "activityDetails": [],
        "activityTypeId": activity_type_id,
        "completed": True,
        "date": date,
        "intensityRanges": intensity_ranges,
        "isTemplate": False,
        "parameters": parameters,
        "planned": False,
        "subActivities": [
            {"subActivityTypeId": sub_activity_type_id, "duration": time_min}
        ],
        "userId": USER_ID,
    }

    location = get_location(details)
    if location is not None:
        payload["location"] = location

    headers = {
        "X-Auth-Token": get_token(),
        "Content-Type": "application/json"
    }

    if debug:
        return "debug", payload

    ### Posting the activity
    try:
        r = requests.post(TPAK_URL, headers=headers, json=payload, timeout=10)
        r.raise_for_status()
    except requests.exceptions.Timeout:
        return None, "Request timed out"
    except requests.exceptions.ConnectionError:
        return None, "Connection error"
    except requests.exceptions.HTTPError:
        return r.status_code, r.text
    except requests.exceptions.RequestException as e:
        return None, str(e)

    return r.status_code, r.json()

def get_last_entry_date():
    headers = {
        "X-Auth-Token": get_token(),
        "Content-Type": "application/json",
    }

    try:
        response = requests.get("https://www.t-pak.ch/api/activities/last-diary-entry", headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print("Please make sure your t-pak token is up to date!")
        sleep(3)
        return None

    date_str = response.text.strip('"')          # "YYYY-MM-DD"
    return date.fromisoformat(date_str)
