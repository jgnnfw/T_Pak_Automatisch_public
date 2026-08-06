"""
This file provides a mapping of garmin to t-pak activity types.
"""
from garmin_client import TPAK_DATA

GARMIN_TO_TPAK_DEFAULT = { #garmin activity type, #t-pak activity type
    "running": "Dauerlauf",
    "street_running": "Dauerlauf",
    "track_running": "Dauerlauf",
    "treadmill_running": "Dauerlauf",
    "virtual_run": "Dauerlauf",
    "trail_running": "OL Training",
    "orienteering": "OL Training",
    "cycling": "Velo Training",
    "road_biking": "Velo Training",
    "mountain_biking": "Velo Training",
    "gravel_cycling": "Velo Training",
    "indoor_cycling": "Velo Training",
    "virtual_ride": "Velo Training",
    "swimming": "Ausdauer-Schwimmen",
    "lap_swimming": "Ausdauer-Schwimmen",
    "open_water_swimming": "Ausdauer-Schwimmen",
    "strength_training": "Kraftraining mit Geräten",
    "hiking": "Wandern / Walking",
    "walking": "Wandern / Walking",
    "casual_walking": "Regenerativer Spaziergang",
    "speed_walking": "Wandern / Walking",
    "mountaineering": "Klettern",
    "rock_climbing": "Klettern",
    "bouldering": "Klettern",
    "indoor_climbing": "Klettern",
    "via_ferrata": "Klettern",
    "cross_country_skiing": "LL Training",
    "skate_skiing": "LL Training",
    "backcountry_skiing_snowboarding" : "Ski/Snowboard",
    "resort_skiing_snowboarding": "Ski/Snowboard",
    "snowshoeing": "Ski/Snowboard",
    "rowing": "Rudern",
    "indoor_rowing": "Rudern",
    "elliptical": "Cardiogerät",
    "indoor_cardio": "Kraftraining ohne Geräte",
    "training": "Kraftraining ohne Geräte",
    "stair_climbing": "Kondi / allgemeine Fitness",
    "yoga": "Yoga, Pilates o.ä.",
    "pilates": "Yoga, Pilates o.ä,",
    "breathwork": "Atmen",
    "meditation": "Yoga, Pilates o.ä.",
}

ONLY_MOVING_TIME = [ # these are the activities that should only include the moving time not the total time.
    "hiking",
    "backcountry_skiing_snowboarding",
    "resort_skiing_snowboarding",
    "snowshoeing",
    "mountaineering",
    "via_ferrata",
    "walking",
    "rock_climbing",
]

MAIN_DURATION_SUBACTIVITY = { # t-pak id -> t-pak id
    16:  85,  # Posten setzen/einziehen -> Effektive OL-Laufzeit (Po setzen)
    30:  227, # Lauf- und Sprungschule -> 227 Laufschule / 226 Sprungschule
    31:  242, # Kraftraining ohne Geräte -> 242 Kraftausdauer / 243 Hypertrophie / 244 Maximalkraft / 395 Intermusk. Koord. / 396 Schnellkraft / 397 Reaktivkraft
    32:  242, # Krafttraining mit Geräten -> same candidates as 31
    33:  242, # Circuit -> same candidates as 31
    34:  242, # Fussgymnastik -> Kraftausdauer (only option)
    133: 242, # Kombitraining -> same candidates as 31, plus 227/226/259
    168: 169, # Wandern / Walking -> Effektive Marschzeit
    50:  51,  # Yoga, Pilates o.ä. -> 51 Yoga / 52 Pilates / 53 Qigong / 54 Tai-Chi / 55 anderes
}

HR_ZONE_DESCRIPTIONS = {1 : 2, 2 : 3, 3 : 5, 4 : 6, 5 : 7} # idx in garmin :index in t-pak

LIST_SUGGESTED_SPORTS = [ #t-pak
    ["OL Wettkampf", "OL Training", "Posten setzen/einziehen u.ä.", "Dauerlauf", "Intervalltraining", "Laufwettkampf", ],
    ["Kraftraining ohne Geräte", "Krafttraining mit Geräten", "Cardiogerät", "Wetvest/Aquajogging", "Schulsport", "OL-Spiel", "Physio", ],
    ["Velo Wettkampf", "Velo Training", "Bike-OL Wettkampf", "Bike-OL Training", ],
    ["LL Wettkampf", "LL Training", "Ski-OL Wettkampf", "Ski-OL Training", "Inline/Eisskaten", ],
    ["Ausdauer-Schwimmen", "Spass-Schwimmen", "Rudern", ],
    ["Wandern / Walking", "Regenerativer Spaziergang", "Klettern", "Ski/Snowboard", ],
]

ALL_SPORTS = sorted([ #t-pak
    "OL Wettkampf", "OL Training", "Posten setzen/einziehen u.ä.",
    "Dauerlauf", "Intervalltraining", "Laufwettkampf", "Steeple/Hürdenlauf",
    "Stufentest", "Conconitest", "Testrunde(n)",
    "Lauf- und Sprungschule", "Kraftraining ohne Geräte", "Krafttraining mit Geräten",
    "Circuit", "Fussgymnastik", "Kombitraining", "Beweglichkeitstraining", "Atemtraining",
    "Ski-OL Wettkampf", "Ski-OL Training", "Bike-OL Wettkampf", "Bike-OL Training",
    "Velo Wettkampf", "Velo Training", "LL Wettkampf", "LL Training",
    "Inline/Eisskaten", "Wetvest/Aquajogging", "Rudern", "Ausdauer-Schwimmen", "Cardiogerät",
    "Kondi / allgemeine Fitness", "Spielsport", "Schulsport", "Tanzen", "Klettern",
    "Ski/Snowboard", "Kampfsport", "Kanu/Kajak/SUP", "Wandern / Walking",
    "Eiskunstlauf", "Spass-Schwimmen", "Yoga, Pilates o.ä.",
    "Stretching", "Kurzschlaf", "Massage", "Wellness",
    "Regenerativer Spaziergang", "Physio",
    "Psychophysische Regeneration", "Visualisierungstraining", "Atmen", "Selbstgespräche",
    "Planung und Auswertung", "Vorbereitung Training/Wettkampf", "Auswertung Training/Wettkampf",
    "Trockentraining", "OL-Spiel",
])

ALL_TRAININGSGEFAESSE = [
    "Verein", "Talentstützpunkt", "Regionalkader", "Juniorenkader",
    "Ski-O Juniorenkader", "NLZ Bern", "NLZ Zürich", "Leichtathletik Verein",
    "Schulsport", "Lager",
]


def t_pak_id_mapper(name: str, activity_type : str | None = None) -> int | None:
    """
    This function uses the t_pak_ids.json file to convert names into ids. This mapping must be used before passing any type to the api, since it can only handle ids.
    :param name: the name that should be mapped
    :param activity_type: optional specification. function will only search for id in the given activity type.
    :return: the id as int or None if the name is non-existing or out of scope of the specified activity type
    """
    def search(obj):
        if isinstance(obj, dict):
            if obj.get("description") == name and "id" in obj:
                return obj["id"]
            for v in obj.values():
                r = search(v)
                if r is not None:
                    return r
        elif isinstance(obj, list):
            for item in obj:
                r = search(item)
                if r is not None:
                    return r
        return None

    if activity_type is None:
        return search(TPAK_DATA)

    # else if activity_type
    for dict1 in TPAK_DATA["activityTypes"]:
        for dict2 in dict1["children"]:
            for dict3 in dict2["children"]:
                if dict3["description"] == activity_type:
                    return search([dict3])
    return None
