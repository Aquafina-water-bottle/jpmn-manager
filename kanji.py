import json
import sqlite3
import os
from typing import Any
from dataclasses import dataclass

@dataclass
class KanjiData:
    decomposition: dict[str, Any]
    components: list[str] # in
    combinations: list[str] # out

    def json_repr(self):
        data = {
            "decomposition": self.decomposition,
            "components": self.components,
            "combinations": self.combinations,
        }
        return data


def get_root_folder() -> str:
    """
    grabs the repository root folder
    """
    root_folder = os.path.dirname(os.path.abspath(__file__))
    return root_folder


def get_kanji_data(kanji) -> KanjiData:
    path = os.path.join(get_root_folder(), "kanjivg.db")
    if not os.path.isfile(path):
        raise RuntimeError(f"invalid path for db '{path}'")

    with sqlite3.connect(path) as conn:
        cur = conn.cursor()

        SQL = "SELECT * FROM kanjivg WHERE element = ?"
        data_list = cur.execute(SQL, kanji).fetchall()
        cur.close()

        if len(data_list) > 1:
            print(f"Found more than one entry in kanjivg for {kanji}?")
        data = data_list[0]
        return KanjiData(json.loads(data[2]), json.loads(data[3]), json.loads(data[4]))
    raise RuntimeError(f"cannot get kanjivg data for '{kanji}'")

