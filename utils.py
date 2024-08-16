import typing
from os.path import exists

import geopy.distance
import requests
import urllib3


def download_file(f_path: str, url: str, overwrite: bool) -> bool:
    if exists(f_path) and not overwrite:
        return False

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    response = requests.get(url, verify=False)
    response.raise_for_status()

    with open(f_path, 'wb') as file:
        file.write(response.content)

    return True


def calc_distance(loc1: typing.Tuple[float, float], loc2: typing.Tuple[float, float]) -> float:
    return geopy.distance.great_circle(loc1, loc2).km


def write_text_file(f_path: str, text: str) -> None:
    with open(f_path, "wt") as f:
        f.write(text)
