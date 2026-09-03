from __future__ import annotations

import numpy as np
import pandas as pd

from cvstudio.calculations import calculate
from cvstudio.detection import detect_cv


def make_synthetic_cv():
    forward_v = np.linspace(-0.8, 0.3, 900)
    backward_v = np.linspace(0.3, -0.8, 900)

    forward_i = (
        -4.0e-5
        + 2.0e-5 * (forward_v + 0.8)
        + 9.0e-5 * np.exp(-((forward_v - 0.10) / 0.18) ** 2)
    )

    backward_i = (
        3.0e-5
        - 2.0e-5 * (0.3 - backward_v)
        - 1.20e-4 * np.exp(-((backward_v + 0.34) / 0.17) ** 2)
    )

    v = np.concatenate([forward_v, backward_v[1:]])
    i = np.concatenate([forward_i, backward_i[1:]])

    return pd.DataFrame(
        {
            "potential": v,
            "current": i,
            "raw_index": np.arange(len(v)),
        }
    )


def main():
    df = make_synthetic_cv()
    bundle = detect_cv(df)
    calc = calculate(bundle.points)

    assert bundle.points["APC"].current > 0
    assert bundle.points["CPC"].current < 0
    assert calc["IPA"] > 0
    assert calc["IPC"] > 0
    assert calc["IPA/IPC"] is not None
    assert 0.0 <= bundle.diagnostics["overall_confidence"] <= 1.0
    assert bundle.diagnostics["review_threshold"] == 0.75

    print("CV Analysis Studio v0.2.1 smoke test passed.")


if __name__ == "__main__":
    main()
