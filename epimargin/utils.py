import argparse
import logging
import sys
import os
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

# code readability
days     = 1
weeks    = 7
years    = 365
percent  = 1/100
annually = 1/years
million  = 1e6

def cwd() -> Path:
    argv0 = Path(sys.argv[0]).parent
    # check if it is writable by user, if not, default to current working
    # directory.
    # NOTE: This looked like a decent way to do it, See more options here
    # https://stackoverflow.com/q/2113427/1805129
    if os.access(argv0, os.W_OK | os.X_OK):
        return argv0
    return Path(".").resolve()

def fmt_params(**kwargs) -> str:
    """  get useful experiment tag from a dictionary of experiment settings """
    return ", ".join(f"{k.replace('_', ' ')}: {v}" for (k, v) in kwargs.items())

def assume_missing_0(df: pd.DataFrame, col: str):
    return df[col] if col in df.columns else 0

def mkdir(p: Path, exist_ok: bool = True) -> Path:
    p.mkdir(exist_ok = exist_ok)
    return p

def setup(**kwargs) -> Tuple[Path, Path]:
    root = cwd()
    if len(sys.argv) > 2:
        parser = argparse.ArgumentParser()
        parser.add_argument("--level", type=str)
        flags = parser.parse_args()
        kwargs["level"] = flags.level
    logging.basicConfig(**kwargs)
    logging.getLogger('flat_table').addFilter(lambda _: 0)
    return (mkdir(root / "data"), mkdir(root / "figs"))

def fillna(array):
    return np.nan_to_num(array, nan = 0, posinf = 0, neginf = 0)

def normalize(array, axis = 0):
    return fillna(array/array.sum(axis = axis)[:, None])
