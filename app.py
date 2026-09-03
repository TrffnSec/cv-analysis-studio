from __future__ import annotations

import pandas as pd
import streamlit as st

from cvstudio.calculations import calculate
from cvstudio.detection import detect_cv, snap_point_to_potential
from cvstudio.exporter import build_results_xlsx
from cvstudio.io import display_graph_name, read_cv_bytes
from cvstudio.ui import inject_css, make_cv_figure


APP_NAME = "CV Analysis Studio"

st.set_page_config(
    page_title=APP_NAME,
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css(st)


if "records" not in st.session_state:
    st.session_state.records = {}

if "analysis_settings" not in st.session_state:
    st.session_state.analysis_settings = {
        "forward_sensitivity": 0.36,
        "backward_sensitivity": 0.585,
        "smoothing_window": 31,
        "review_threshold": 0.75,
    }


def refresh_calculation(record):
    record["calculation"] = calculate(record["points"])


def analyse_payload(name: str, payload: bytes):
    settings = st.session_state.analysis_settings

    df = read_cv_bytes(name, payload)

    bundle = detect_cv(
        df,
        forward_sensitivity=settings["forward_sensitivity"],
        backward_sensitivity=settings["backward_sensitivity"],
        smoothing_window=settings["smoothing_window"],
        review_threshold=settings["review_threshold"],
    )

    record = {
        "filename": name,
        "graph_name": display_graph_name(name),
        "df": df,
        "points": bundle.points,
        "bundle": bundle,
        "remarks": "",
        "review_status": (
            "Needs review"
            if bundle.diagnostics["needs_review"]
            else "Ready"
        ),
    }

    refresh_calculation(record)
    return record


def analyse_uploaded_files(uploaded_files):
    created = {}
    failures = []

    for uploaded in uploaded_files:
        try:
            # Directory upload may preserve a relative path in uploaded.name.
            # Keep the path as a unique key but use only the basename as graph name.
            key = uploaded.name
            basename = uploaded.name.replace("\\", "/").split("/")[-1]

            created[key] = analyse_payload(
                basename,
                uploaded.getvalue(),
            )

            # Preserve relative folder context only for uniqueness/reference.
            created[key]["source_path"] = uploaded.name

        except Exception as exc:
            failures.append((uploaded.name, str(exc)))

    st.session_state.records = created
    return failures


def rerun_record(key):
    record = st.session_state.records[key]
    settings = st.session_state.analysis_settings

    bundle = detect_cv(
        record["df"],
        forward_sensitivity=settings["forward_sensitivity"],
        backward_sensitivity=settings["backward_sensitivity"],
        smoothing_window=settings["smoothing_window"],
        review_threshold=settings["review_threshold"],
    )

    record["bundle"] = bundle
    record["points"] = bundle.points
    record["review_status"] = (
        "Needs review"
        if bundle.diagnostics["needs_review"]
        else "Ready"
    )

    refresh_calculation(record)


def export_rows():
    rows = []

    for record in st.session_state.records.values():
        calc = record["calculation"]
        bundle = record["bundle"]

        rows.append(
            {
                "GRAPH NAME": record["graph_name"],
                **calc,
                "REMARKS": record.get("remarks", ""),
                "_review_status": record.get("review_status", ""),
                "_diagnostics": bundle.diagnostics,
                "_fbc_source": record["points"]["FBC"].source,
                "_bbc_source": record["points"]["BBC"].source,
                "_fbc_method": record["points"]["FBC"].method,
                "_bbc_method": record["points"]["BBC"].method,
            }
        )

    return rows


def render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div class="cv-brand">
                <div class="cv-brand-title">◈ CV Analysis Studio</div>
                <div class="cv-brand-subtitle">
                    Biomedical CV extraction workspace · v0.2.2
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### Detection settings")

        forward = st.slider(
            "Forward onset sensitivity",
            0.10,
            0.90,
            float(
                st.session_state.analysis_settings["forward_sensitivity"]
            ),
            0.005,
            help="Controls automatic FBC onset detection.",
        )

        backward = st.slider(
            "Backward onset sensitivity",
            0.10,
            0.90,
            float(
                st.session_state.analysis_settings["backward_sensitivity"]
            ),
            0.005,
            help="Controls automatic BBC onset detection.",
        )

        smoothing = st.slider(
            "Signal smoothing",
            9,
            81,
            int(st.session_state.analysis_settings["smoothing_window"]),
            2,
        )

        st.session_state.analysis_settings = {
            "forward_sensitivity": forward,
            "backward_sensitivity": backward,
            "smoothing_window": smoothing,
            "review_threshold": 0.75,
        }

        st.divider()

        st.markdown(
            """
            <div class="small-note">
            <b>Review threshold: 75%</b><br>
            Confidence is based on how stable FBC/BBC remain when the detector
            threshold is slightly changed. Anything below 75% is marked for review.
            Manual adjustment remains available for every graph.
            </div>
            """,
            unsafe_allow_html=True,
        )


def hero():
    st.markdown(
        """
        <div class="hero">
            <h1>CV Analysis Studio <span style="opacity:.55">v0.2.2</span></h1>
            <p>
                Upload individual CV files or choose an entire folder from your
                computer, automatically extract peak/baseline values, review the
                detected points visually, manually correct any value when required,
                and export the final calculated Excel workbook.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


render_sidebar()
hero()

tab_import, tab_review, tab_results, tab_method = st.tabs(
    [
        "01  Import",
        "02  Review",
        "03  Results & Export",
        "04  Method",
    ]
)


with tab_import:
    st.markdown(
        '<div class="section-title">Import CV source data</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-copy">'
        "Choose individual files or select a complete folder. "
        "One supported source file becomes one result row."
        "</div>",
        unsafe_allow_html=True,
    )

    import_mode = st.radio(
        "Import method",
        ["Upload files", "Upload folder"],
        horizontal=True,
    )

    failures = []
    selected_files = None

    if import_mode == "Upload files":
        selected_files = st.file_uploader(
            "Select one or more CV files",
            type=["csv", "xlsx", "xls", "xlsm"],
            accept_multiple_files=True,
            key="cv-file-uploader",
            help="Select one file or multiple files at once.",
        )

        if selected_files:
            st.caption(
                f"{len(selected_files)} supported file(s) selected."
            )

        analyse_clicked = st.button(
            "Analyze uploaded files",
            type="primary",
            disabled=not selected_files,
            key="analyse-files",
        )

    else:
        st.info(
            "Choose a folder from your computer. "
            "The browser will upload the supported CV files from that folder."
        )

        selected_files = st.file_uploader(
            "Choose folder containing CV files",
            type=["csv", "xlsx", "xls", "xlsm"],
            accept_multiple_files="directory",
            key="cv-folder-uploader",
            help=(
                "Select one folder. Supported CSV/Excel files inside it "
                "will be uploaded together."
            ),
        )

        if selected_files:
            st.caption(
                f"{len(selected_files)} supported file(s) found in the selected folder."
            )

            preview_names = [
                f.name for f in selected_files[:15]
            ]
            st.code("\n".join(preview_names))

            if len(selected_files) > 15:
                st.caption(
                    f"...and {len(selected_files) - 15} more file(s)."
                )

        analyse_clicked = st.button(
            "Analyze uploaded folder",
            type="primary",
            disabled=not selected_files,
            key="analyse-folder",
        )

    if analyse_clicked:
        with st.spinner("Analysing CV files..."):
            failures = analyse_uploaded_files(selected_files)

        if st.session_state.records:
            st.success(
                f"Analysed {len(st.session_state.records)} file(s). "
                "Continue to the Review tab."
            )

    for name, error in failures:
        st.error(f"{name}: {error}")

    if st.session_state.records:
        records = list(st.session_state.records.values())

        below_threshold = sum(
            1
            for r in records
            if r["bundle"].diagnostics["overall_confidence"] < 0.75
        )

        m1, m2, m3, m4 = st.columns(4)

        m1.metric("Files loaded", len(records))

        m2.metric(
            "Data points",
            f"{sum(len(r['df']) for r in records):,}",
        )

        m3.metric("Below 75%", below_threshold)

        m4.metric(
            "Mean confidence",
            f"{sum(r['bundle'].diagnostics['overall_confidence'] for r in records) / len(records):.0%}",
        )

        summary = []

        for r in records:
            d = r["bundle"].diagnostics

            summary.append(
                {
                    "Graph": r["graph_name"],
                    "Status": r["review_status"],
                    "Confidence": d["overall_confidence"] * 100,
                    "Points": len(r["df"]),
                }
            )

        st.dataframe(
            pd.DataFrame(summary),
            hide_index=True,
            use_container_width=True,
            column_config={
                "Confidence": st.column_config.ProgressColumn(
                    min_value=0,
                    max_value=100,
                    format="%.0f%%",
                ),
            },
        )


with tab_review:
    if not st.session_state.records:
        st.info("Import and analyse CV files first.")

    else:
        keys = list(st.session_state.records)

        selected = st.selectbox(
            "Graph under review",
            keys,
            format_func=lambda k: (
                f"{st.session_state.records[k]['graph_name']} · "
                f"{st.session_state.records[k]['review_status']}"
            ),
        )

        record = st.session_state.records[selected]
        diagnostics = record["bundle"].diagnostics

        top1, top2, top3 = st.columns([1.2, 1.2, 3.6])

        top1.metric(
            "Confidence",
            f"{diagnostics['overall_confidence']:.0%}",
        )

        top2.metric(
            "Threshold",
            "75%",
        )

        if st.button(
            "Re-run automatic detection",
            use_container_width=True,
            key=f"rerun-{selected}",
        ):
            rerun_record(selected)
            st.rerun()

        st.plotly_chart(
            make_cv_figure(
                record["df"],
                record["points"],
                record["graph_name"],
            ),
            use_container_width=True,
            config={
                "displaylogo": False,
                "scrollZoom": True,
            },
        )

        calc = record["calculation"]

        m1, m2, m3, m4 = st.columns(4)

        m1.metric(
            "IPA",
            f"{calc['IPA']:.8e} A",
        )

        m2.metric(
            "IPC",
            f"{calc['IPC']:.8e} A",
        )

        m3.metric(
            "IPA / IPC",
            "—"
            if calc["IPA/IPC"] is None
            else f"{calc['IPA/IPC']:.6f}",
        )

        m4.metric(
            "ΔE",
            f"{calc['ΔE (V)']:.6f} V",
        )

        st.markdown(
            '<div class="section-title">Manual point adjustment</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="section-copy">'
            "Enter the desired potential and the app snaps that marker to the "
            "nearest measured raw point on the correct scan direction."
            "</div>",
            unsafe_allow_html=True,
        )

        edit_cols = st.columns(4)
        edits = {}

        for col, label in zip(
            edit_cols,
            ["FBC", "APC", "BBC", "CPC"],
        ):
            p = record["points"][label]

            with col:
                edits[label] = st.number_input(
                    f"{label} potential (V)",
                    value=float(p.potential),
                    format="%.8f",
                    key=f"{selected}-{label}-manual-{p.index}",
                )

                st.caption(
                    f"Current: `{p.current:.10e} A`"
                )

                st.caption(
                    "Manual"
                    if p.source == "manual"
                    else "Automatic"
                )

        if st.button(
            "Apply manual adjustments",
            type="primary",
            key=f"manual-apply-{selected}",
        ):
            changed = False

            for label, potential in edits.items():
                old = record["points"][label]

                if abs(float(potential) - old.potential) > 1e-12:
                    record["points"][label] = snap_point_to_potential(
                        record["df"],
                        label,
                        float(potential),
                    )
                    changed = True

            if changed:
                record["review_status"] = "Manually reviewed"
                refresh_calculation(record)

                st.success(
                    "Manual point adjustments applied."
                )

                st.rerun()

            else:
                st.info("No point values were changed.")

        record["remarks"] = st.text_input(
            "Remarks",
            value=record.get("remarks", ""),
            key=f"remarks-{selected}",
            placeholder="Optional note",
        )


with tab_results:
    if not st.session_state.records:
        st.info("Import and analyse CV files first.")

    else:
        rows = export_rows()
        preview = []

        for idx, item in enumerate(rows, 1):
            preview.append(
                {
                    "SL NO.": idx,
                    "GRAPH NAME": item["GRAPH NAME"],
                    "APC": item["APC"],
                    "FBC": item["FBC"],
                    "IPA": item["IPA"],
                    "BBC": item["BBC"],
                    "CPC": item["CPC"],
                    "IPC": item["IPC"],
                    "IPA/IPC": item["IPA/IPC"],
                    "EPA (V)": item["EPA (V)"],
                    "EPC (V)": item["EPC (V)"],
                    "ΔE (V)": item["ΔE (V)"],
                    "STATUS": item["_review_status"],
                }
            )

        st.markdown(
            '<div class="section-title">Final calculation preview</div>',
            unsafe_allow_html=True,
        )

        st.dataframe(
            pd.DataFrame(preview),
            hide_index=True,
            use_container_width=True,
        )

        excel_bytes = build_results_xlsx(rows)

        st.download_button(
            "Export final Excel workbook",
            data=excel_bytes,
            file_name="CV_Analysis_Results_v0.2.2.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            type="primary",
        )


with tab_method:
    st.markdown(
        '<div class="section-title">Project calculation method</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        **APC / EPA** — anodic peak current and its potential.  
        **CPC / EPC** — cathodic peak current and its potential.  
        **FBC** — current at the onset of the rapid forward-current rise.  
        **BBC** — current at the onset of the rapid backward-current change.

        **Calculations**

        `IPA = APC − FBC`

        `IPC = BBC − CPC`

        `IPA/IPC = IPA ÷ IPC`

        `ΔE = EPA − EPC`
        """
    )

    st.info(
        "Automatic FBC/BBC confidence is based on onset stability. "
        "75% is the review threshold. Every graph can still be manually corrected."
    )
