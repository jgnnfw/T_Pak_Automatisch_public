from flask import Flask, render_template, request,  redirect, url_for
from fitparse import FitFile
import io
from garmin_client import load_cached_activities, mark_uploaded, fetch_and_cache_activities
from fit_parser import get_sport, get_name, get_distance, get_total_time, extract_coordinates, get_date
from garmin_to_t_pak import GARMIN_TO_TPAK_DEFAULT, t_pak_id_mapper, \
     LIST_SUGGESTED_SPORTS, ALL_SPORTS, ALL_TRAININGSGEFAESSE
from T_Pak_uploading import upload_to_t_pak, get_last_entry_date
from typing import Any
import os
import webbrowser
import threading
from pathlib import Path
import sys

def resource_path(relative_path):
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).parent / relative_path

app = Flask(__name__, template_folder=str(resource_path("templates")), static_folder=str(resource_path("static")))

def seconds_to_time(seconds: float | int) -> str:
    """
    Convert seconds to HH:MM:SS or MM:SS string.
    :param seconds: seconds to convert
    :return: (HH:)MM:SS string
    """
    seconds = int(seconds)

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"

    return f"{minutes}:{secs:02d}"

def get_suggested_activities(sport: str | None) -> list[str]:
    """
    Gets the list of suggested activities for the given t-pak sport. (all in T-Pak activity types)
    :param sport: given sport
    :return: list of suggested activities
    """
    if sport is None:
        return ALL_SPORTS

    for sublist in LIST_SUGGESTED_SPORTS:
        if sport in sublist:
            return sublist
    return ALL_SPORTS


def prepare_activity(activity_tup : tuple[int, bytes, dict, dict]) -> dict[str, Any | None]:
    """
    Convert cached activity tuple into data for HTML.
    :param activity_tup: tuple of (activity_id, fit_bytes, activity_dict, details_dict)
    :return: dictionary of activity info for the use of the HTML
    """
    activity_id, fit_bytes, activity_dict, details_dict = activity_tup

    fitfile = FitFile(io.BytesIO(fit_bytes))

    coords = extract_coordinates(fitfile)

    width, height = 80, 60
    svg_points = coordinates_to_svg_points(coords, width=width, height=height)

    sport = get_sport(fitfile)
    t_pak_sport = GARMIN_TO_TPAK_DEFAULT.get(sport, None)
    recommended_activities = get_suggested_activities(t_pak_sport)

    return {
        "id": activity_id,
        "name": get_name(activity_dict),
        "distance": round((get_distance(fitfile) or 0) / 1000, 2),
        "time": seconds_to_time(get_total_time(fitfile)),
        "date": get_date(activity_dict),

        # svg
        "svg_points": svg_points,
        "svg_height": height,
        "svg_width": width,

        # used by upload later
        "fit_bytes": fit_bytes,
        "activity_dict": activity_dict,
        "details_dict": details_dict,

        # selectors
        "sport": sport,
        "default_type": t_pak_sport,
        "recommended_types": recommended_activities,
        "all_types": ALL_SPORTS,
        "default_trainingsgefaess": "Regionalkader",
        "all_trainingsgefaesse" : ALL_TRAININGSGEFAESSE,
    }

def coordinates_to_svg_points(coordinates, width=100, height=100, padding=0):
    """
    Convert [(lat, lon), ...] into an SVG polyline points string, preserving aspect ratio and centering in the dimension with
    remaining space. The y-axis is flipped because SVG y increases downward while latitude increases upward.
    :param coordinates: GPS coordinates
    :param width: width of SVG in pixels
    :param height: height of SVG in pixels
    :param padding: padding around the SVG in pixels
    :return: SVG polyline point string
    """
    if not coordinates:
        return ""

    lats = [c[0] for c in coordinates]
    lons = [c[1] for c in coordinates]

    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    lat_range = max_lat - min_lat or 1e-9
    lon_range = max_lon - min_lon or 1e-9

    usable_w = width - 2 * padding
    usable_h = height - 2 * padding

    # Preserve aspect ratio
    scale = min(usable_w / lon_range, usable_h / lat_range)

    scaled_w = lon_range * scale
    scaled_h = lat_range * scale

    # Center along the dimension with extra space
    offset_x = padding + (usable_w - scaled_w) / 2
    offset_y = padding + (usable_h - scaled_h) / 2

    points = []
    for lat, lon in coordinates:
        x = offset_x + (lon - min_lon) * scale
        y = offset_y + (max_lat - lat) * scale  # flip y-axis
        points.append(f"{x:.1f},{y:.1f}")

    return " ".join(points)

@app.route("/")
def index():

    cached = load_cached_activities(only_pending=True)

    activities = [prepare_activity(activity) for activity in cached]

    return render_template("index.html", activities=activities)

@app.route("/upload", methods=["POST"])
def upload():
    activity_ids = request.form.getlist("activity_ids")

    # re-load cache, keyed by id, so we have fit_bytes/activity_dict/details_dict again
    cached = {
        str(activity_id): (fit_bytes, activity_dict, details_dict)
        for activity_id, fit_bytes, activity_dict, details_dict in load_cached_activities(only_pending=True)
    }

    failures = []

    for activity_id in activity_ids:
        fit_bytes, activity_dict, details_dict = cached[activity_id]
        activity_type = request.form.get(f"activity_type_{activity_id}")

        if activity_type is None:
            failures.append((activity_id, "No activity type specified."))
            continue

        try:
            upload_to_t_pak(fit_bytes, activity_type, activity_dict, details_dict)
            mark_uploaded(int(activity_id), delete_cache=True)
        except Exception as e:
            failures.append((activity_id, str(e)))

    if failures:
        print('\033[91m {}\033[00m'.format('Upload failures: ') + failures.__repr__())

        return redirect(url_for("index"))

    return redirect(url_for("confirm"))

@app.route("/confirm")
def confirm():
    return render_template("confirm.html")


@app.route("/shutdown", methods=["POST"])
def shutdown():
    def stop():
        os._exit(0)

    threading.Timer(0.3, stop).start()  # let the response flush before killing the process
    return "", 204


def open_browser():
    webbrowser.open("http://localhost:5000/")

if __name__ == "__main__":

    print("Lade die Garmin Aktivitäten herunter. Bitte warten... ")
    print("Drücke Ctrl+C, um abzubrechen.")

    start_date = get_last_entry_date()
    if start_date is None:
        quit()

    fetch_and_cache_activities(start_date=start_date, end_date=None)

    # this should automatically open a browser window
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        threading.Timer(1, open_browser).start()
    # run the app
    app.run(host="127.0.0.1", port=5000, debug=True)