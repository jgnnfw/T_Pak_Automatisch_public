from typing import Any
from User_Information_parser import DEFAULT_TRAININGSGEFAESS
from garmin_to_t_pak import HR_ZONE_DESCRIPTIONS, t_pak_id_mapper, ONLY_MOVING_TIME


def get_session_field(fitfile, field_name: str) -> Any:
    """
    Returns value from the "session_field" field of a fitfile.
    :param fitfile: fitfile object
    :param field_name: name of the field
    :return: value of the field
    """
    session = next(fitfile.get_messages("session", as_dict=True))
    return next((f["value"] for f in session["fields"] if f["name"] == field_name), None)


def _bucket_hr_zones(fitfile, running: bool = False):
    """
    THIS FUNCTION IS NOT USED ANYMORE. The Heart Rate Zones are already stored in the activity_dict.
    """
    records = list(fitfile.get_messages("record", as_dict=True))
    if running:
        zone_seconds = {idx: 0.0 for _, _, name, idx in HR_ZONE_BOUNDARIES_RUNNING if name}
    else:
        zone_seconds = {idx: 0.0 for _, _, name, idx in HR_ZONE_BOUNDARIES if name}

    for prev, curr in zip(records, records[1:]):
        hr = next((f["value"] for f in curr["fields"] if f["name"] == "heart_rate"), None)
        t0 = next((f["value"] for f in prev["fields"] if f["name"] == "timestamp"), None)
        t1 = next((f["value"] for f in curr["fields"] if f["name"] == "timestamp"), None)
        if hr is not None and t0 is not None and t1 is not None:
            dt = (t1 - t0).total_seconds()
            for lo, hi, name, idx in HR_ZONE_BOUNDARIES:
                if lo <= hr <= hi and name:
                    zone_seconds[idx] += dt
                    break
    return zone_seconds

def get_hr_zones(activity : dict[str, Any]):
    zone_seconds = {}
    for idx in range(1,6):
        zone_seconds[HR_ZONE_DESCRIPTIONS[idx]] = activity[f"hrTimeInZone_{idx}"]
    return zone_seconds

def get_location(details : dict[str, Any]) -> str | None:
    return details.get("locationName", None)


def get_activity_parameters(fitfile, trainingsgefaess: str = DEFAULT_TRAININGSGEFAESS) -> dict[int | None, Any]:
    parameters = {}

    total_time_min = get_time(fitfile) / 60

    parameters["Trainingsgefäss"] = t_pak_id_mapper(trainingsgefaess, None)

    distance_m = get_session_field(fitfile, "total_distance") or 0
    parameters["Distanz"] = distance_km = distance_m / 1000 or 0

    parameters["Steigung"] = get_session_field(fitfile, "total_ascent") or 0
    parameters["Durchschnitts-Pace"] = total_time_min / distance_km if distance_km else 0
    parameters["Durchschnittsgeschwindigkeit"] = 60 * distance_km / total_time_min if total_time_min else 0
    parameters["Maximalgeschwindigkeit"] = get_session_field(fitfile, "max_speed")  \
                                           or get_session_field(fitfile, "enhanced_max_speed") \
                                           or None
    
    # Trainingsbelastung ist in unknown_193 codiert, mit 10 multipliziert, da fitfile diesen Datentyp nicht unterstützt.
    # Das Gefühl ist in unknown_192 codiert mit einer Zahl 0-100. {0: sehr schwach, 25: schwach, 50: normal, 75: stark, 100: sehr stark}
    rpe = get_session_field(fitfile, "unknown_193")
    parameters["Trainingsbelastung"] = int(rpe/10) if rpe else None

    parameters["Durchschnittspuls"] = get_session_field(fitfile, "avg_heart_rate") or None
    parameters["Maximalpuls"] = get_session_field(fitfile, "max_heart_rate") or None

    result_parameters : dict[int | None, Any] = {t_pak_id_mapper(k) : v for k, v in parameters.items()}
    return result_parameters


def get_time(fitfile) -> float | int:
    """
    Returns elapsed/moving time of ``fitfile`` activity in seconds.
    """
    if get_sport(fitfile) in ONLY_MOVING_TIME:
        return get_session_field(fitfile, "total_moving_time") or get_session_field(fitfile, "total_timer_time") or get_session_field(fitfile, "total_elapsed_time") or 0
    else:
        return get_session_field(fitfile, "total_timer_time") or get_session_field(fitfile, "total_elapsed_time") or 0


def _round_preserving_sum(values: list[float], total: int | None = None) -> list[int]:
    """
    Round a list of floats to ints such that they sum exactly to ``total``
    (or round(sum(values)) if total is None), using the largest-remainder method.
    """
    if total is None:
        total = round(sum(values))

    floors = [int(v) for v in values]  # truncate
    remainder = total - sum(floors)

    # distribute the remaining +1s to the values with the largest fractional part
    fractions = sorted(
        range(len(values)),
        key=lambda i: values[i] - floors[i],
        reverse=True
    )

    result = floors[:]
    for i in fractions[:remainder]:
        result[i] += 1

    return result

def get_intensity_ranges(fitfile, activity : dict[str, Any]) -> list[dict[str, float|int]]:
    total_time_s = get_time(fitfile)

    zone_seconds = get_hr_zones(activity)

    # HR zones, scaled to match total duration
    zone_sum = sum(zone_seconds.values()) or 1
    scale = total_time_s / zone_sum
    zone_minutes = {k: (v * scale) / 60 for k, v in zone_seconds.items()}

    keys = list(zone_minutes.keys())
    values = list(zone_minutes.values())

    rounded = _round_preserving_sum(values)  # total defaults to round(sum(values))
    zone_minutes_rounded = dict(zip(keys, rounded))

    intensity_ranges = [
        {"duration": round(zone_minutes_values, 1), "intensityRangeId": idx}
        for idx, zone_minutes_values in zone_minutes_rounded.items()
    ]

    return intensity_ranges

def extract_coordinates(fitfile) -> list[tuple[float,float]]:

    coords = []

    for record in fitfile.get_messages("record"):
        lat = None
        lon = None

        for field in record:
            if field.name == "position_lat":
                lat : float | None = field.value
            elif field.name == "position_long":
                lon : float | None = field.value

        if lat is not None and lon is not None:
            coords.append((lat * (180 / 2**31), lon * (180 / 2**31)))

    return coords

def get_name(activity_dict: dict[str, Any]) -> str | None:
    return activity_dict.get("activityName", None)

def get_sport(fitfile) -> str | None:
    return get_session_field(fitfile, "sport") or None

def get_distance(fitfile) -> float| int | None:
    return get_session_field(fitfile, "total_distance") or None

def get_total_time(fitfile) -> float | int :
    """
    Do not use this function for uploading, only for the web app handler. Use get_time instead for uploading.
    :param fitfile: fitfile data
    :return: total elapsed time of ``fitfile`` activity in seconds.
    """
    return get_session_field(fitfile, "total_timer_time") or get_session_field(fitfile, "total_elapsed_time") or 0

def get_date(activity_dict : dict[str, Any]) -> str | None:
    date_str = activity_dict.get("startTimeLocal", None)

    if date_str is None:
        return None

    date_str = date_str.split(" ")[0].split("-")
    return f"{date_str[2]}.{date_str[1]}."