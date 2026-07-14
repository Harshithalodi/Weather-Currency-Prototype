"""
Currency Exchange Integration -> Google Sheets
------------------------------------------------
Pulls INR exchange rates against USD, EUR, GBP, JPY, CNY, AUD, SGD, AED, RUB
for day / week / month / year durations, and writes them into a Google Sheet.

Data source note:
- Frankfurter API (free, no key, ECB-based) covers: USD, EUR, GBP, JPY, CNY, AUD, SGD
  with full historical data.
- Frankfurter does NOT carry AED or RUB (ECB doesn't publish reference rates for them).
  For those two, this script falls back to open.er-api.com, which is free/no-key
  but only gives the LATEST rate (no free historical series). This limitation is
  called out clearly in the sheet output/console log rather than silently guessed at
  -- worth mentioning in your demo as a deliberate design decision.

Setup before running:
1. pip install -r requirements.txt
2. Place your Google service account JSON key in this folder as service_account.json
3. Share your target Sheet with the service account's client_email (Editor access)
4. Set SHEET_ID below.
"""

import datetime as dt
import requests
import gspread
from google.oauth2.service_account import Credentials

# ---------------- CONFIG ----------------
SHEET_ID = "1iRzlDy0JE5_PHflXvRVcNpTljoWAsxvNNkRUNWqRCBI"
SERVICE_ACCOUNT_FILE = "service_account.json"

BASE = "INR"
FRANKFURTER_CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CNY", "AUD", "SGD"]
FALLBACK_CURRENCIES = ["AED", "RUB"]  # not on Frankfurter/ECB

DURATIONS = {
    "day": 1,
    "week": 7,
    "month": 30,
    "year": 365,
}

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_sheet_client():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return gspread.authorize(creds)


def fetch_frankfurter_series(days_back):
    end = dt.date.today()
    start = end - dt.timedelta(days=days_back)
    symbols = ",".join(FRANKFURTER_CURRENCIES)
    url = f"https://api.frankfurter.app/{start.isoformat()}..{end.isoformat()}"
    params = {"from": BASE, "to": symbols}
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("rates", {})


def fetch_fallback_latest():
    """Latest-only rates for currencies Frankfurter doesn't cover."""
    url = f"https://open.er-api.com/v6/latest/{BASE}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json().get("rates", {})
    today = dt.date.today().isoformat()
    return {today: {c: data.get(c) for c in FALLBACK_CURRENCIES}}


def build_rows(frank_rates, fallback_rates):
    rows = []
    for date, rates in sorted(frank_rates.items()):
        row = [date] + [rates.get(c, "") for c in FRANKFURTER_CURRENCIES] + ["", ""]
        rows.append(row)
    for date, rates in fallback_rates.items():
        row = [date] + ["" for _ in FRANKFURTER_CURRENCIES] + [rates.get(c, "") for c in FALLBACK_CURRENCIES]
        rows.append(row)
    return rows


def write_to_sheet(gc, tab_name, header, rows):
    sh = gc.open_by_key(SHEET_ID)
    try:
        ws = sh.worksheet(tab_name)
        sh.del_worksheet(ws)
    except gspread.exceptions.WorksheetNotFound:
        pass
    ws = sh.add_worksheet(title=tab_name, rows=str(len(rows) + 10), cols="12")
    ws.update("A1", [header] + rows)
    return ws


def main():
    gc = get_sheet_client()
    header = ["Date"] + FRANKFURTER_CURRENCIES + FALLBACK_CURRENCIES

    fallback_rates = fetch_fallback_latest()
    print(f"Note: AED/RUB only available as latest-day rate ({list(fallback_rates.keys())[0]}), "
          f"since the free tier has no historical source for these two currencies.")

    for duration_label, days_back in DURATIONS.items():
        print(f"Fetching {duration_label} exchange rates...")
        frank_rates = fetch_frankfurter_series(days_back)
        rows = build_rows(frank_rates, fallback_rates)

        tab_name = f"Currency_{duration_label}"
        write_to_sheet(gc, tab_name, header, rows)
        print(f"Wrote {len(rows)} rows to tab '{tab_name}'")

    print("Done. Open your Google Sheet to view the data.")


if __name__ == "__main__":
    main()
