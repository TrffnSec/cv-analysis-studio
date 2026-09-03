from __future__ import annotations

from io import BytesIO
from datetime import datetime

import xlsxwriter


HEADERS = [
    "SL NO.",
    "GRAPH NAME",
    "APC",
    "FBC",
    "IPA",
    "BBC",
    "CPC",
    "IPC",
    "IPA/IPC",
    "EPA (V)",
    "EPC (V)",
    "ΔE (V)",
    "REMARKS",
]


def build_results_xlsx(rows):
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})

    ws = workbook.add_worksheet("CV Results")
    method = workbook.add_worksheet("Method")
    audit = workbook.add_worksheet("Analysis Log")

    title_fmt = workbook.add_format(
        {
            "bold": True,
            "font_size": 16,
            "font_color": "#FFFFFF",
            "bg_color": "#172033",
            "align": "left",
            "valign": "vcenter",
        }
    )
    subtitle_fmt = workbook.add_format(
        {"font_size": 9, "font_color": "#667085", "italic": True}
    )
    header_fmt = workbook.add_format(
        {
            "bold": True,
            "font_color": "#FFFFFF",
            "bg_color": "#2563EB",
            "align": "center",
            "valign": "vcenter",
        }
    )
    text_fmt = workbook.add_format(
        {
            "border": 1,
            "border_color": "#E4E7EC",
            "valign": "vcenter",
        }
    )
    num_fmt = workbook.add_format(
        {
            "border": 1,
            "border_color": "#E4E7EC",
            "num_format": "0.0000000000",
            "valign": "vcenter",
        }
    )
    formula_fmt = workbook.add_format(
        {
            "border": 1,
            "border_color": "#E4E7EC",
            "num_format": "0.0000000000",
            "bg_color": "#F8FAFC",
            "valign": "vcenter",
        }
    )
    ratio_fmt = workbook.add_format(
        {
            "border": 1,
            "border_color": "#E4E7EC",
            "num_format": "0.000000",
            "bg_color": "#F8FAFC",
            "valign": "vcenter",
        }
    )
    section_fmt = workbook.add_format(
        {"bold": True, "font_size": 13, "font_color": "#172033"}
    )
    body_fmt = workbook.add_format(
        {
            "font_color": "#344054",
            "text_wrap": True,
            "valign": "top",
        }
    )

    ws.merge_range("A1:M1", "CV Analysis Studio — Results", title_fmt)
    ws.set_row(0, 28)
    ws.merge_range(
        "A2:M2",
        f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} • CV Analysis Studio v0.2.2",
        subtitle_fmt,
    )

    for col, header in enumerate(HEADERS):
        ws.write(3, col, header, header_fmt)

    for i, item in enumerate(rows, start=4):
        excel_row = i + 1

        ws.write_number(i, 0, i - 3, text_fmt)
        ws.write(i, 1, item["GRAPH NAME"], text_fmt)
        ws.write_number(i, 2, item["APC"], num_fmt)
        ws.write_number(i, 3, item["FBC"], num_fmt)

        # Cache the already calculated result in addition to storing the formula.
        # This fixes the v0.1 issue where some viewers displayed zero before a
        # spreadsheet engine recalculated the workbook.
        ws.write_formula(
            i, 4, f"=C{excel_row}-D{excel_row}",
            formula_fmt, item["IPA"]
        )

        ws.write_number(i, 5, item["BBC"], num_fmt)
        ws.write_number(i, 6, item["CPC"], num_fmt)

        ws.write_formula(
            i, 7, f"=F{excel_row}-G{excel_row}",
            formula_fmt, item["IPC"]
        )

        ratio_value = item["IPA/IPC"]
        if ratio_value is None:
            ratio_value = ""
        ws.write_formula(
            i, 8, f'=IFERROR(E{excel_row}/H{excel_row},"")',
            ratio_fmt, ratio_value
        )

        ws.write_number(i, 9, item["EPA (V)"], num_fmt)
        ws.write_number(i, 10, item["EPC (V)"], num_fmt)

        ws.write_formula(
            i, 11, f"=J{excel_row}-K{excel_row}",
            formula_fmt, item["ΔE (V)"]
        )
        ws.write(i, 12, item.get("REMARKS", ""), text_fmt)

    ws.freeze_panes(4, 2)
    ws.autofilter(3, 0, max(3, len(rows) + 3), len(HEADERS) - 1)
    ws.set_column("A:A", 9)
    ws.set_column("B:B", 38)
    ws.set_column("C:L", 15)
    ws.set_column("M:M", 28)
    ws.set_row(3, 24)

    method.write("A1", "Calculation method", section_fmt)
    method.write(
        "A3",
        "IPA = APC − FBC\n"
        "IPC = BBC − CPC\n"
        "IPA/IPC = IPA ÷ IPC\n"
        "ΔE = EPA − EPC",
        body_fmt,
    )
    method.write("A6", "Point definitions", section_fmt)
    method.write(
        "A8",
        "APC / EPA: anodic peak current and its potential.\n"
        "CPC / EPC: cathodic peak current and its potential.\n"
        "FBC: current at the onset of the rapid forward-current rise.\n"
        "BBC: current at the onset of the rapid backward-current change.\n\n"
        "v0.2 uses multiple baseline-onset hypotheses and keeps baseline points "
        "reviewable. Human review remains recommended until the method is "
        "validated against a larger labelled dataset.",
        body_fmt,
    )
    method.set_column("A:A", 95)

    audit_headers = [
        "GRAPH NAME",
        "REVIEW STATUS",
        "OVERALL CONFIDENCE",
        "FBC CONFIDENCE",
        "BBC CONFIDENCE",
        "FBC SOURCE",
        "BBC SOURCE",
        "FBC METHOD",
        "BBC METHOD",
    ]
    for col, header in enumerate(audit_headers):
        audit.write(0, col, header, header_fmt)

    for row_idx, item in enumerate(rows, start=1):
        diag = item.get("_diagnostics", {})
        audit.write(row_idx, 0, item["GRAPH NAME"], text_fmt)
        audit.write(row_idx, 1, item.get("_review_status", ""), text_fmt)
        audit.write_number(
            row_idx, 2, float(diag.get("overall_confidence", 0.0)), num_fmt
        )
        audit.write_number(
            row_idx, 3, float(diag.get("fbc_confidence", 0.0)), num_fmt
        )
        audit.write_number(
            row_idx, 4, float(diag.get("bbc_confidence", 0.0)), num_fmt
        )
        audit.write(row_idx, 5, item.get("_fbc_source", ""), text_fmt)
        audit.write(row_idx, 6, item.get("_bbc_source", ""), text_fmt)
        audit.write(row_idx, 7, item.get("_fbc_method", ""), text_fmt)
        audit.write(row_idx, 8, item.get("_bbc_method", ""), text_fmt)

    audit.freeze_panes(1, 1)
    audit.set_column("A:A", 38)
    audit.set_column("B:G", 20)
    audit.set_column("H:I", 34)

    workbook.close()
    output.seek(0)
    return output.getvalue()
