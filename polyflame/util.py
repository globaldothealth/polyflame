import hashlib
import tomllib
from pathlib import Path
from typing import Callable

import pandas as pd

from .types import SourceInfo, Taxonomy


def _readable_term(tx: Taxonomy, section: str) -> Callable[[list[str]], str | bool | None]:
    def func(x: list[str]) -> str | bool | None:
        if x is None:
            return None
        else:
            # Looks up terminology in section, otherwise returns None.
            # This could be a potential source of errors if the taxonomy
            # is manually written instead of being generated from the
            # mapping file or the data itself.
            return tx[section].get(x[0])

    return func


def use_readable_terms(
    data: pd.DataFrame,
    tx: Taxonomy,
    column: str,
    taxonomy_section: str | None = None,
    drop_nulls: bool = False,
):
    "In place replacement of codes with readable terms"
    data[column] = data[column].map(_readable_term(tx, taxonomy_section or column))
    if drop_nulls:
        data = data[~pd.isnull(data)]


def get_checksum(file: str | Path) -> str:
    "Calculate the SHA-256 checksum of a file"
    h = hashlib.sha256()
    with open(file, "rb") as fp:
        while True:
            data = fp.read(4096)
            if len(data) == 0:
                break
            h.update(data)
    return h.hexdigest()


def load_taxonomy(file_part: str) -> Taxonomy:
    tx_file = Path(__file__).parent / "taxonomy" / (file_part + ".toml")
    if not tx_file.exists():
        raise FileNotFoundError(
            f"""load_taxonomy('{file_part}') could not find file under 'taxonomy' folder.
Expected location: {tx_file}"""
        )
    with tx_file.open("rb") as fp:
        return tomllib.load(fp)


def msg_part_not_found(data: SourceInfo, part: str) -> str:
    return f"Data at path={data['path']} missing part={part}"
