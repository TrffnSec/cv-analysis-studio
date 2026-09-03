from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter


@dataclass
class CVPoint:
    label: str
    index: int
    potential: float
    current: float
    source: str = "automatic"
    confidence: float = 1.0
    method: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class DetectionBundle:
    points: Dict[str, CVPoint]
    diagnostics: Dict[str, object]


def _odd_window(n: int, requested: int) -> int:
    requested = max(5, int(requested))
    if requested % 2 == 0:
        requested += 1
    max_window = n if n % 2 else n - 1
    return max(5, min(requested, max_window))


def smooth_current(values: np.ndarray, requested_window: int = 31) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if len(values) < 7:
        return values.copy()
    window = _odd_window(len(values), requested_window)
    return savgol_filter(
        values,
        window_length=window,
        polyorder=3,
        mode="interp",
    )


def split_sweeps(df: pd.DataFrame):
    potential = df["potential"].to_numpy(float)
    turn = int(np.argmax(potential))

    min_side = max(10, len(df) // 10)
    if turn < min_side or turn > len(df) - min_side:
        raise ValueError(
            "Could not identify a reliable forward/backward turning point."
        )

    forward = df.iloc[: turn + 1].copy().reset_index(drop=True)
    backward = df.iloc[turn:].copy().reset_index(drop=True)
    return forward, backward, turn


def _point_from_local(
    sweep: pd.DataFrame,
    local_idx: int,
    label: str,
    *,
    source: str = "automatic",
    confidence: float = 1.0,
    method: str = "",
) -> CVPoint:
    local_idx = int(np.clip(local_idx, 0, len(sweep) - 1))
    row = sweep.iloc[local_idx]
    return CVPoint(
        label=label,
        index=int(row["raw_index"]),
        potential=float(row["potential"]),
        current=float(row["current"]),
        source=source,
        confidence=float(np.clip(confidence, 0.0, 1.0)),
        method=method,
    )


def _first_sustained(mask: np.ndarray, start: int, stop: int, sustain: int):
    run = 0
    for i in range(max(0, start), min(stop, len(mask))):
        if bool(mask[i]):
            run += 1
            if run >= sustain:
                return i - sustain + 1
        else:
            run = 0
    return None


def _onset_idx(
    sweep: pd.DataFrame,
    peak_local_idx: int,
    *,
    direction: str,
    sensitivity: float,
    smoothing_window: int,
) -> int:
    current = smooth_current(
        sweep["current"].to_numpy(float),
        smoothing_window,
    )
    slope = np.gradient(current)
    signal = slope if direction == "forward" else -slope

    stop = max(8, peak_local_idx - 2)

    if direction == "forward":
        search_start = max(3, int(stop * 0.08))
    else:
        # Ignore the turnaround transient at the start of the reverse scan.
        search_start = max(3, int(stop * 0.35))

    region = signal[search_start:stop]
    if len(region) < 10:
        return max(0, peak_local_idx // 2)

    positive = np.maximum(region, 0.0)
    reference = float(np.quantile(positive, 0.97))
    if reference <= 0:
        return max(0, peak_local_idx // 2)

    threshold = reference * float(sensitivity)
    mask = signal >= threshold
    sustain = max(4, min(14, len(sweep) // 120))

    found = _first_sustained(mask, search_start, stop, sustain)
    if found is None:
        candidates = np.flatnonzero(mask[search_start:stop])
        if len(candidates):
            return int(candidates[0] + search_start)
        return int(np.argmax(signal[search_start:stop]) + search_start)

    return int(found)


def _stability_confidence(
    sweep: pd.DataFrame,
    peak_idx: int,
    *,
    direction: str,
    sensitivity: float,
    smoothing_window: int,
) -> float:
    # Confidence is based on how stable the selected onset remains when the
    # threshold is nudged slightly. This is more meaningful than inventing a
    # fixed confidence number.
    shifts = (-0.05, -0.025, 0.0, 0.025, 0.05)
    indices = []

    for shift in shifts:
        s = float(np.clip(sensitivity + shift, 0.08, 0.92))
        indices.append(
            _onset_idx(
                sweep,
                peak_idx,
                direction=direction,
                sensitivity=s,
                smoothing_window=smoothing_window,
            )
        )

    spread = max(indices) - min(indices)
    scale = max(12, int(peak_idx * 0.12))

    # Map stable selections toward high confidence, but cap auto-confidence
    # below certainty because FBC/BBC remain method-dependent selections.
    confidence = 0.92 - (spread / scale) * 0.55
    return float(np.clip(confidence, 0.35, 0.92))


def detect_cv(
    df: pd.DataFrame,
    *,
    forward_sensitivity: float = 0.36,
    backward_sensitivity: float = 0.585,
    smoothing_window: int = 31,
    review_threshold: float = 0.75,
) -> DetectionBundle:
    forward, backward, turn = split_sweeps(df)

    apc_idx = int(np.argmax(forward["current"].to_numpy(float)))
    cpc_idx = int(np.argmin(backward["current"].to_numpy(float)))

    fbc_idx = _onset_idx(
        forward,
        apc_idx,
        direction="forward",
        sensitivity=forward_sensitivity,
        smoothing_window=smoothing_window,
    )
    bbc_idx = _onset_idx(
        backward,
        cpc_idx,
        direction="backward",
        sensitivity=backward_sensitivity,
        smoothing_window=smoothing_window,
    )

    fbc_conf = _stability_confidence(
        forward,
        apc_idx,
        direction="forward",
        sensitivity=forward_sensitivity,
        smoothing_window=smoothing_window,
    )
    bbc_conf = _stability_confidence(
        backward,
        cpc_idx,
        direction="backward",
        sensitivity=backward_sensitivity,
        smoothing_window=smoothing_window,
    )

    points = {
        "FBC": _point_from_local(
            forward,
            fbc_idx,
            "FBC",
            confidence=fbc_conf,
            method="forward rapid-rise onset",
        ),
        "APC": _point_from_local(
            forward,
            apc_idx,
            "APC",
            confidence=0.98,
            method="forward current maximum",
        ),
        "BBC": _point_from_local(
            backward,
            bbc_idx,
            "BBC",
            confidence=bbc_conf,
            method="backward rapid-change onset",
        ),
        "CPC": _point_from_local(
            backward,
            cpc_idx,
            "CPC",
            confidence=0.98,
            method="backward current minimum",
        ),
    }

    overall = min(fbc_conf, bbc_conf, 0.98)

    return DetectionBundle(
        points=points,
        diagnostics={
            "turn_index": int(turn),
            "forward_points": int(len(forward)),
            "backward_points": int(len(backward)),
            "fbc_confidence": float(fbc_conf),
            "bbc_confidence": float(bbc_conf),
            "overall_confidence": float(overall),
            "review_threshold": float(review_threshold),
            "needs_review": bool(overall < review_threshold),
            "forward_sensitivity": float(forward_sensitivity),
            "backward_sensitivity": float(backward_sensitivity),
            "smoothing_window": int(smoothing_window),
        },
    )


def snap_point_to_potential(
    df: pd.DataFrame,
    label: str,
    target_potential: float,
) -> CVPoint:
    forward, backward, _ = split_sweeps(df)
    sweep = forward if label in {"FBC", "APC"} else backward

    potentials = sweep["potential"].to_numpy(float)
    idx = int(np.argmin(np.abs(potentials - float(target_potential))))

    return _point_from_local(
        sweep,
        idx,
        label,
        source="manual",
        confidence=1.0,
        method="manual potential snap",
    )
