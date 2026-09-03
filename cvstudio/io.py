from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re

import numpy as np
import pandas as pd


POTENTIAL_CANDIDATES = (
    "Working Electrode (V)",
    "Working Electrode vs. NHE (V)",
    "Potential (V)",
    "Voltage (V)",
    "Potential",
    "Voltage",
)

CURRENT_CANDIDATES = (
    "Current (A)",
    "Current",
    "I (A)",
)


class CVDataError(ValueError):
    pass


def _clean_name(name: str) -> str:
    return re.sub(r"\s+", " ", str(name)).strip()


def _find_column(columns, candidates, keywords):
    cleaned = {_clean_name(c): c for c in columns}

    for candidate in candidates:
        if candidate in cleaned:
            return cleaned[candidate]

    lowered = {str(c).lower(): c for c in columns}
    for col_lower, original in lowered.items():
        if all(word in col_lower for word in keywords):
            return original

    return None


def read_cv_bytes(filename: str, payload: bytes) -> pd.DataFrame:
    suffix = Path(filename).suffix.lower()
    stream = BytesIO(payload)

    if suffix == ".csv":
        try:
            df = pd.read_csv(stream)
        except UnicodeDecodeError:
            stream.seek(0)
            df = pd.read_csv(stream, encoding="latin-1")
    elif suffix in {".xlsx", ".xlsm", ".xls"}:
        # Calamine keeps the app independent of Microsoft Excel/OpenPyXL.
        df = pd.read_excel(stream, engine="calamine")
    else:
        raise CVDataError(f"Unsupported file type: {suffix}")

    if df.empty:
        raise CVDataError("The uploaded file has no data rows.")

    potential_col = _find_column(
        df.columns,
        POTENTIAL_CANDIDATES,
        keywords=("electrode",),
    )
    if potential_col is None:
        potential_col = _find_column(
            df.columns,
            POTENTIAL_CANDIDATES,
            keywords=("potential",),
        )

    current_col = _find_column(
        df.columns,
        CURRENT_CANDIDATES,
        keywords=("current",),
    )

    if potential_col is None or current_col is None:
        raise CVDataError(
            "Could not identify potential/current columns. "
            "Expected columns similar to 'Working Electrode (V)' and 'Current (A)'."
        )

    out = pd.DataFrame(
        {
            "potential": pd.to_numeric(df[potential_col], errors="coerce"),
            "current": pd.to_numeric(df[current_col], errors="coerce"),
        }
    ).dropna()

    if len(out) < 30:
        raise CVDataError("Not enough numeric CV points were found.")

    out = out.reset_index(drop=True)
    out["raw_index"] = np.arange(len(out), dtype=int)
    return out


def display_graph_name(filename: str) -> str:
    return Path(filename).stem
