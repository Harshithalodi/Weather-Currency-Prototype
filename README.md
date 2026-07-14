# Prototype: Weather + Currency Integration into Google Sheets

## What's in this folder
- `weather_to_sheet.py` — pulls weather data for your chosen cities (day/week/month/year) into a Sheet
- `currency_to_sheet.py` — pulls INR vs 8 currencies (day/week/month/year) into a Sheet
- `requirements.txt` — Python dependencies

## Step-by-step

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Create a Google Cloud service account (one-time setup)
1. console.cloud.google.com → New Project
2. APIs & Services → Library → enable **Google Sheets API** (and **Google Drive API**)
3. APIs & Services → Credentials → Create Credentials → Service Account
4. Open the service account → Keys → Add Key → JSON → download it
5. Rename the downloaded file to `service_account.json` and put it in this folder

### 3. Create and share the Google Sheet
1. Create a blank Google Sheet in your browser
2. Open `service_account.json`, copy the `client_email` value
3. In the Sheet, click Share → paste that email → give it **Editor** access
4. Copy the Sheet ID from the URL (the long string between `/d/` and `/edit`)
5. Paste that ID into `SHEET_ID = "..."` at the top of both scripts

### 4. Customize inputs (optional)
- In `weather_to_sheet.py`, edit the `CITIES` dictionary to add/remove cities (needs lat/lon — just Google "[city] latitude longitude")
- Both scripts already cover day/week/month/year automatically — no changes needed there

### 5. Run it
```bash
python weather_to_sheet.py
python currency_to_sheet.py
```
Each run creates separate tabs in your Sheet: `Weather_day`, `Weather_week`, `Weather_month`, `Weather_year`, and `Currency_day`, `Currency_week`, `Currency_month`, `Currency_year`.

### 6. Add charts (the "if time permits" bonus)
Easiest path for a demo: open the Sheet in the browser, select a data range on any tab, then **Insert → Chart**. Google auto-suggests a line chart for time-series data — pick that, it's exactly the visual you want for "temperature over time" or "exchange rate over time."

If you want the chart created *by code* instead (stronger for a coding evaluation), you can extend the scripts using the Sheets API's `batchUpdate` with an `AddChartRequest` — let me know if you want that added in and I'll write it in.

### 7. For your demo/walkthrough
Be ready to explain:
- Why Open-Meteo and Frankfurter (free, no key friction, reliable, well-documented)
- The AED/RUB gap in Frankfurter and how the script handles it explicitly rather than hiding it — this is a good talking point, it shows you noticed and handled a real-world data limitation instead of pretending it wasn't there
- How the service account auth flow works (no OAuth popup needed, good for automation/scripts)
- Where you'd take it next: scheduling (cron / Cloud Scheduler), error handling/retries, a paid data source for full AED/RUB history if this were a real product

## Troubleshooting
- **`PermissionError` / 403 from Sheets API** → you forgot to share the Sheet with the service account's email
- **`SpreadsheetNotFound`** → double check `SHEET_ID` is correct (just the ID, not the full URL)
- **Empty currency fallback columns** → open.er-api.com may be rate-limited or down; the script still writes the row, just with blanks — mention this as a known limitation if it happens live
