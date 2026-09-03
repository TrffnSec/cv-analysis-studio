from __future__ import annotations


def calculate(points):
    apc = float(points["APC"].current)
    fbc = float(points["FBC"].current)
    bbc = float(points["BBC"].current)
    cpc = float(points["CPC"].current)

    epa = float(points["APC"].potential)
    epc = float(points["CPC"].potential)

    ipa = apc - fbc
    ipc = bbc - cpc
    ratio = ipa / ipc if abs(ipc) > 1e-18 else None
    delta_e = epa - epc

    return {
        "APC": apc,
        "FBC": fbc,
        "IPA": ipa,
        "BBC": bbc,
        "CPC": cpc,
        "IPC": ipc,
        "IPA/IPC": ratio,
        "EPA (V)": epa,
        "EPC (V)": epc,
        "ΔE (V)": delta_e,
    }
