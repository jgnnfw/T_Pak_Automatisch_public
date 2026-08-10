import re
from datetime import date
from html import escape
from User_Information_parser import get_name
from playwright.sync_api import sync_playwright
from typing import TypedDict, Union
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.console import Console

### classes of Typed Dict ###
class Course(TypedDict):
    distance: float
    climb: int
    controls: int


class Competitor(TypedDict):
    rank: int | None
    name: str
    time: str | None


class Category(TypedDict):
    category: str | None
    course: Course
    competitors: list[Competitor]


# class definition of RankingParameters
RankingParameters = TypedDict(
    "RankingParameters",
    {
        "Anzahl Athleten am Start": int,
        "Siegerzeit": Union[float, int, str, None],
        "Wettkampfzeit": Union[float, int, str, None],
        "Rang": Union[int, None],
        "Distanz (Bahndaten)": Union[float, None],
        "Steigung (Bahndaten)": Union[int, None],
        "Anzahl Posten": Union[int, None],
    },
)

german_months = [
    "Jan.", "Feb.", "März", "Apr.", "Mai", "Juni",
    "Juli", "Aug.", "Sept.", "Okt.", "Nov.", "Dez."
]


def _german_date(d):
    return f"{d.day}. {german_months[d.month - 1]} {d.year}"


def _find_all_matches(text: str, start: str, end: str) -> list[str]:
    """
    returns all occurrences in text between start and end as list, start and end not inclusive. spaces are stripped.
    :param text: text to search
    :param start: start marker
    :param end: end marker
    """
    return [occ.strip() for occ in re.findall(re.escape(start) + r"(.*?)" + re.escape(end), text)]


def find_date_links(o_l_view_source_page_text: str, activity_date: date, debug: bool = False) -> list[str]:
    """
    This function returns the rankings links in an o-l raking view-source page text, matching the given date.
    :param o_l_view_source_page_text: o-l raking view source page text. example at link: view-source:https://www.o-l.ch/cgi-bin/results?event=Auswahl&year=2025
    :param activity_date: date as date object
    :param debug: If enabled, some variables are printed to the console
    :return: list with links to matched rankings. Empty if no links are found (on given date).
    """

    start = r"<br><input type=radio name=result_event_id value="
    end = escape(_german_date(activity_date))

    if debug:
        print(f"start: {start}, end: {end}")

    between_lines = _find_all_matches(o_l_view_source_page_text, start, end)

    if not between_lines:
        return []

    result_list = []
    for line in between_lines:
        link_text = re.search(r'<a href="(.*?)">', line, )
        if link_text:
            link = link_text.group(1)
            result_list.append("https://www.o-l.ch/cgi-bin/" + link + "&kind=all")

    return result_list


def _time_to_minutes(result: str | None) -> float | str | None:
    if result is None:
        return None

    # MM:SS or H:MM:SS
    if not re.fullmatch(r"\d+:\d{2}(?::\d{2})?", result):
        return result

    parts = [int(part) for part in result.split(":")]

    if len(parts) == 2:
        minutes, seconds = parts
        return float(minutes + seconds / 60)
    elif len(parts) == 3:
        hours, minutes, seconds = parts
        return float(hours * 60 + minutes + seconds / 60)

    return None


def find_ranking_parameters(text: str, debug: bool = False) -> RankingParameters | None:
    """
    This function finds all ranking parameters of the given person (ini - File) in the rankings_page_body_text.
    :param text: body text of the rankings page with ?kind=all
    :param debug: If enabled, some variables are printed to the console
    :return: a dictionary of activity parameters, if a ranking is found, else None.
    The returned dictionary contains "Wettkampfzeit", the runners time, which is not an activity parameter.
    """

    name_to_find = get_name()
    if not name_to_find.lower().strip()[:22] in text.lower():  # short-circuit if name not found.
        if debug:
            print(f"Name {name_to_find} not found in rankings_page_body_text.")
        return None

    lines = text.splitlines()

    # Patterns that match the competitor / course with re.search(pattern, line)
    competitor_pattern = re.compile(
        r"^\s*(?:(\d+)\.\s+)?(.+?)\s+(\d{2})\s+")  # beginning of line, 0 or more spaces, optional group(one or more digits, literal ., one or more spaces), ...
    course_pattern = re.compile(r"\(\s*([\d.]+)\s*km,\s*([\d.]+)\s*m,\s*(\d+)\s*Po\.\)")

    # idea of the function: go through all lines, collect all data by category,
    # then extract useful data
    categories: list[Category] = []

    current_category: str | None = None
    current_course: Course | None = None
    competitors: list[Competitor] = []

    for line_number, line in enumerate(lines):

        if line_number == 0:  # this is due to category heading being searched above current line
            continue

        line = line.rstrip()

        # ---Course information---
        course_match = course_pattern.search(line)
        if course_match:

            # Save previous category before starting a new one
            if current_course is not None:
                categories.append({
                    "category": current_category,
                    "course": current_course,
                    "competitors": competitors,
                })

            # search the next non-empty line above course info
            category_index = line_number - 1
            while category_index >= 0 and not lines[category_index].strip():
                category_index -= 1

            # create info of new category
            current_category = lines[category_index].strip()
            current_course: Course = {
                "distance": float(course_match.group(1)),
                "climb": int(course_match.group(2)),
                "controls": int(course_match.group(3)),
            }
            competitors = []

            continue

        # ---Competitor---
        competitor_match = competitor_pattern.match(line)
        if competitor_match:
            rank = int(competitor_match.group(1)) if competitor_match.group(1) else None
            competitor_name = competitor_match.group(2).strip()

            # Time or other result at the end of the line.
            result_match = re.search(r"(\d+:\d{2}(?::\d{2})?|\S+)\s*$", line)
            result = result_match.group(1).strip() if result_match else None

            competitors.append({
                "rank": rank,
                "name": competitor_name,
                "time": result,
            })

            continue

    # Add the LAST category
    if current_course is not None:
        categories.append({
            "category": current_category,
            "course": current_course,
            "competitors": competitors,
        })

    if debug:
        print(f"{len(categories)} categories found")

    # Find requested person
    name_lower = name_to_find.lower().strip()

    for category in categories:
        for competitor in category["competitors"]:

            competitor_name_lower = competitor["name"].lower().strip()

            # First try an exact match.
            # If the website has truncated the name, compare the first 22 characters.
            name_matches = (competitor_name_lower == name_lower) or (competitor_name_lower[:22] == name_lower[:22])

            if name_matches:

                # First ranked competitor = winner
                winner = next((c for c in category["competitors"] if c["rank"] is not None), None)

                # round times if possible
                wettkampfzeit = _time_to_minutes(competitor["time"])
                if isinstance(wettkampfzeit, float):
                    wettkampfzeit = round(wettkampfzeit, 2)
                if winner is not None:
                    siegerzeit = _time_to_minutes(winner["time"])
                else:
                    siegerzeit = None
                if isinstance(siegerzeit, float):
                    siegerzeit = round(siegerzeit, 2)

                result: RankingParameters = {
                    "Anzahl Athleten am Start": len(category["competitors"]),
                    "Siegerzeit": siegerzeit,
                    "Wettkampfzeit": wettkampfzeit,
                    "Rang": competitor["rank"],
                    "Distanz (Bahndaten)": category["course"]["distance"] if category["course"] else None,
                    "Steigung (Bahndaten)": category["course"]["climb"] if category["course"] else None,
                    "Anzahl Posten": category["course"]["controls"] if category["course"] else None,
                }

                return result

    return None


def _get_rankings_page_text(page_link: str) -> str | tuple[None, Exception]:
    # EVERYTHING OF THIS FUNCTION IS ALREADY INCLUDED IN search_ranking_on_date
    """
    Returns the visible page text of the link by using playwright.
    :param page_link: The link of the page to return.
    :return: The text of the page. If an Error occurs, returns None and the Exception.
    """

    try:
        with sync_playwright() as p:
            browser = p.firefox.launch()
            page = browser.new_page()
            page.goto(page_link, wait_until="networkidle", timeout=15000)
            text = page.locator("body").inner_text()
            browser.close()
            return text

    except Exception as e:
        return None, e


def search_ranking_on_date(activity_date: date, debug: bool = False) -> RankingParameters | tuple[
    None, Exception] | None:
    o_l_view_source_page_link = f"view-source:https://www.o-l.ch/cgi-bin/results?event=Auswahl&year={activity_date.year}"

    try:
        with sync_playwright() as p:

            if debug:
                print("opening browser...")

            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(o_l_view_source_page_link, wait_until="networkidle", timeout=15000)
            o_l_view_source_page_text = page.locator("body").inner_text()

            if debug:
                possible_rankings_link_list = find_date_links(o_l_view_source_page_text, activity_date, debug=True)
                print(f"list of links of possible rankings: {possible_rankings_link_list}")
            else:
                possible_rankings_link_list = find_date_links(o_l_view_source_page_text, activity_date)

            for rankings_link in possible_rankings_link_list:
                page = browser.new_page()
                page.goto(rankings_link, wait_until="networkidle", timeout=15000)

                rankings_text = page.locator("body").inner_text()
                rankings_parameters = find_ranking_parameters(rankings_text, debug=(True if debug else False))

                if rankings_parameters is not None:
                    return rankings_parameters

            browser.close()

    except Exception as e:
        return None, e


def search_rankings_on_dates(activity_dates: list[date], debug: bool = False) -> dict[date, RankingParameters | tuple[None, Exception] | None]:

    results: dict[date, RankingParameters | tuple[None, Exception] | None] = {}

    dates_by_year: dict[int, list[date]] = {}
    for d in activity_dates:
        dates_by_year.setdefault(d.year, []).append(d)

    with sync_playwright() as p:
        browser = p.chromium.launch()

        # progress bar setup
        console = Console(force_terminal=True, color_system="truecolor")
        with Progress(
                SpinnerColumn(style="cyan"),
                TextColumn("[bold cyan]{task.description}"),
                BarColumn(complete_style="green", finished_style="bold green"),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                console=console,
        ) as progress:
            task = progress.add_task("Searching rankings...", total=len(activity_dates))

            for year, dates_in_year in dates_by_year.items():

                o_l_view_source_page_link = f"view-source:https://www.o-l.ch/cgi-bin/results?event=Auswahl&year={year}"

                page = browser.new_page()
                try:
                    page.goto(o_l_view_source_page_link, wait_until="networkidle", timeout=15000)
                    o_l_view_source_page_text = page.locator("body").inner_text()
                except Exception as e:
                    for d in dates_in_year:
                        results[d] = (None, e)
                    continue
                finally:
                    page.close()

                for activity_date in dates_in_year:

                    possible_rankings_link_list = find_date_links(o_l_view_source_page_text, activity_date, debug=debug)
                    if not possible_rankings_link_list:
                        results[activity_date] = None
                        progress.advance(task)
                        continue

                    found = None
                    for rankings_link in possible_rankings_link_list:
                        browser_page = browser.new_page()
                        try:
                            browser_page.goto(rankings_link, wait_until="networkidle", timeout=15000)
                            rankings_text = browser_page.locator("body").inner_text()
                            rankings_parameters = find_ranking_parameters(rankings_text, debug=debug)
                            if rankings_parameters is not None:
                                found = rankings_parameters
                                break # finally is still executed
                        except Exception as e:
                            found = (None, e)
                            break
                        finally:
                            browser_page.close()

                    results[activity_date] = found
                    progress.advance(task)

        browser.close()

    return results