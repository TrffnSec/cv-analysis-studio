# CV Analysis Studio v0.2.1

Professional local web application for CV data extraction, review, calculation,
and Excel export.

## Simplified v0.2.1 workflow

1. Import source files using either:
   - **Upload files** — one or many files selected in the browser.
   - **Import local folder** — provide a folder path on the same machine running the app.
2. Automatic CV analysis.
3. Review the reconstructed graph and automatically selected:
   - FBC
   - APC / EPA
   - BBC
   - CPC / EPC
4. Manually adjust any point by entering its potential, exactly like v0.1.
5. Export the final Excel workbook.

## Removed from v0.2

- Validation Lab
- Alternative candidate-selection workflow
- Extra calibration screens

## Confidence

- Review threshold: **75%**
- The number is based on detector stability when the onset threshold is varied slightly.
- It is not presented as a guaranteed scientific accuracy percentage.
- Anything below 75% is marked `Needs review`.
- Manual adjustment is available for every graph.

## Supported import formats

- CSV
- XLS
- XLSX
- XLSM

## Folder import

Because this is a local Streamlit application, you can enter a folder path such as:

```text
/Users/name/Desktop/CV Data
```

or on Windows:

```text
C:\Users\Name\Desktop\CV Data
```

The app can optionally include supported files inside subfolders.

## Run on macOS / Linux

```bash
chmod +x run_mac_linux.sh
./run_mac_linux.sh
```

Or manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Run on Windows

```bat
run_windows.bat
```
