# CV Analysis Studio v0.2.2

Hosted-ready professional Streamlit application for CV data extraction,
review, calculation, and Excel export.

## Import options

### Upload files

Select one or multiple supported CV files manually.

### Upload folder

Choose a single folder from your computer. The browser uploads all supported
CSV/Excel files from that folder together.

This works correctly when the application is hosted on Streamlit Community Cloud;
no local filesystem path is required.

## Supported formats

- CSV
- XLS
- XLSX
- XLSM

## Workflow

1. Upload files or upload a folder.
2. Run automatic CV analysis.
3. Review FBC, APC, BBC and CPC markers.
4. Manually adjust any point when necessary.
5. Review calculated IPA, IPC, IPA/IPC and ΔE.
6. Export the final Excel workbook.

## Review threshold

Automatic FBC/BBC review threshold: **75%**.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Community Cloud

Deploy the repository using:

- Branch: `main`
- Main file: `app.py`

When new commits are pushed to the deployed branch, Streamlit Community Cloud
updates the same application URL.
