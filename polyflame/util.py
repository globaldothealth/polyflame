import hashlib
import tomllib
from pathlib import Path

from .types import SourceInfo, Taxonomy


def get_checksum(file: str) -> str:
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
    with tx_file.open() as fp:
        return tomllib.load(fp)


def msg_part_not_found(data: SourceInfo, part: str) -> str:
    return f"Data at path={data['path']} missing part={part}"