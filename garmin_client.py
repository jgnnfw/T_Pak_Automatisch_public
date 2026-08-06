"""
This file fetches and caches activities from Garmin.
"""

from garminconnect import Garmin
from User_Information_parser import get_email, get_password
import json
import zipfile
import io
from pathlib import Path
from typing import Any
from datetime import date

DATA_DIR = Path("./Activity_Data")
PENDING_PATH = DATA_DIR / "pending_upload.json"
with open("t_pak_ids.json", "r", encoding="utf-8") as fh:
    TPAK_DATA = json.load(fh)

# ---------- pending-upload list ----------

def _load_pending() -> list[int]:
    if PENDING_PATH.exists():
        with open(PENDING_PATH, "r") as f:
            return json.load(f)
    return []

def _save_pending(pending: list[int]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(PENDING_PATH, "w") as f:
        json.dump(pending, f, indent=2)

def _add_pending(activity_id: int) -> None:
    pending = _load_pending()
    if activity_id not in pending:
        pending.append(activity_id)
        _save_pending(pending)

def mark_uploaded(activity_id: int, delete_cache: bool = False) -> None:
    """
    Call after a successful upload to remove the activity from the pending list.
    :param activity_id: The activity id to mark uploaded
    :param delete_cache: if True, also deletes the cached folder on disk (future option).
    """
    pending = _load_pending()
    if activity_id in pending:
        pending.remove(activity_id)
        _save_pending(pending)
    else:
        print('\033[91m {}\033[00m'.format('Attention: ') +
              f"Activity {activity_id} could not be marked uploaded since it was not found in the pending list."
        )

    if delete_cache:
        folder = _find_activity_folder(activity_id)
        if folder:
            for f in folder.iterdir():
                f.unlink()
            folder.rmdir()


# ---------- cache folder helpers ----------

def _folder_for_activity(activity_id: int, start_time: str) -> Path:
    safe_time = start_time.replace(":", "-").replace(" ", "_")
    return DATA_DIR / f"Activity_{safe_time}_{activity_id}"


def _find_activity_folder(activity_id: int) -> Path | None:
    if not DATA_DIR.exists():
        return None
    for folder in DATA_DIR.glob(f"Activity_*_{activity_id}"):
        return folder
    return None


def _cache_activity(activity_id: int, fit_bytes: bytes, activity_dict: dict, details_dict: dict) -> None:
    start_time : str | None = activity_dict.get("startTimeLocal", None)
    if start_time is None:
        raise ValueError("Activity start time is required!")
    folder = _folder_for_activity(activity_id, start_time)
    folder.mkdir(parents=True, exist_ok=True)

    with open(folder / "fit_bytes.fit", "wb") as f:
        f.write(fit_bytes)
    with open(folder / "activity.json", "w") as f:
        json.dump(activity_dict, f, indent=2)
    with open(folder / "details.json", "w") as f:
        json.dump(details_dict, f, indent=2)

    _add_pending(activity_id)


# ---------- fetching (network, no return) ----------

def fetch_and_cache_activities(start_date: date, end_date: date | None = None) -> None:
    """
    Fetch all activities strictly after ``start_date``, up to and including ``end_date``
    (default: today), and cache them to disk. Skips activities already cached.
    Does not `return` anything -- use ``load_cached_activities()`` afterwards.
    """
    if end_date is None:
        end_date = date.today()

    client = Garmin(get_email(), get_password())
    client.login()

    activities = client.get_activities_by_date(start_date.isoformat(), end_date.isoformat()) # this method exists

    for activity_dict in activities:
        activity_id = activity_dict["activityId"]

        # skip strictly-after filter (API range is inclusive on both ends)
        activity_date_str : str = activity_dict.get("startTimeLocal", "")[:10]
        try:
            activity_date = date.fromisoformat(activity_date_str)
        except ValueError:
            print('\033[91m {}\033[00m'.format('Attention: ') +
              f"The start time of activity {activity_id} (date_str: {activity_date_str}) could not be parsed and is skipped.")
            continue  # skip if date unparsable
        if activity_date <= start_date:
            print(f"The start time of activity {activity_id} is at the last entry date ({activity_date}) and is skipped")
            continue

        if _find_activity_folder(activity_id) is not None:
            continue  # already cached

        details_dict = client.get_activity(activity_id)
        fit_data = client.download_activity(activity_id, dl_fmt=client.ActivityDownloadFormat.ORIGINAL)
        z = zipfile.ZipFile(io.BytesIO(fit_data))
        fit_bytes = z.read(z.namelist()[0])

        _cache_activity(activity_id, fit_bytes, activity_dict, details_dict)


# ---------- reading from cache (no network) ----------

def load_cached_activities(only_pending: bool = True) -> list[tuple[int, bytes, dict[str, Any], dict[str, Any]]]:
    """
    Load cached activities from disk without network calls.
    Path to Cache: ./{DATA_DIR}/Activity_{safe_start_time}_{activity_id}/{fit_bytes.fit, activity.json, details.json}
    :param only_pending: If True, only returns activities not yet marked uploaded.
    :return: list of (activity_id, fit_bytes, activity_dict, details_dict)
    """
    if not DATA_DIR.exists():
        return []

    pending = set(_load_pending()) if only_pending else None # _load_pending() returns [] if nothing is pending, therefore safe to use None for All
    results = []

    for folder in sorted(DATA_DIR.glob("Activity_*")):
        try:
            activity_id = int(folder.name.rsplit("_", 1)[-1])
        except ValueError:
            continue

        if only_pending and activity_id not in pending:
            continue

        with open(folder / "fit_bytes.fit", "rb") as f:
            fit_bytes = f.read()
        with open(folder / "activity.json", "r") as f:
            activity_dict = json.load(f)
        with open(folder / "details.json", "r") as f:
            details_dict = json.load(f)

        results.append((activity_id, fit_bytes, activity_dict, details_dict))

    return results

