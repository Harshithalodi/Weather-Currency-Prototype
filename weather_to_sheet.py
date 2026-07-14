"""
Weather Data Integration -> Google Sheets
------------------------------------------
Pulls weather data (day / week / month / year) for a set of cities
from the free Open-Meteo API and writes it into a Google Sheet.

Setup before running:
1. pip install -r requirements.txt
2. Place your Google service account JSON key file in this folder
   and rename it to: service_account.json
3. Share your target Google Sheet with the service account's email
   (found inside service_account.json as "client_email"), giving Editor access.
4. Set SHEET_ID below to your spreadsheet's ID (from its URL).
"""

import datetime as dt
import requests
import gspread
from google.oauth2.service_account import Credentials

# ---------------- CONFIG ----------------
SHEET_ID = "1iRzlDy0JE5_PHflXvRVcNpTljoWAsxvNNkRUNWqRCBI"
SERVICE_ACCOUNT_FILE = "service_account.json"

CITIES = {
    "Hyderabad": (17.3850, 78.4867),
    "Mumbai": (19.0760, 72.8777),
    "Delhi": (28.6139, 77.2090),
    "Bengaluru": (12.9716, 77.5946),
}

# duration -> (label, days_back)
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


def fetch_weather(lat, lon, days_back):
    """Fetch daily weather history using Open-Meteo's free archive API."""
    end = dt.date.today()
    start = end - dt.timedelta(days=days_back)
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max",
        "timezone": "auto",
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def build_rows(city, data):
    daily = data.get("daily", {})
    dates = daily.get("time", [])
    tmax = daily.get("temperature_2m_max", [])
    tmin = daily.get("temperature_2m_min", [])
    precip = daily.get("precipitation_sum", [])
    wind = daily.get("windspeed_10m_max", [])

    rows = []
    for i in range(len(dates)):
        rows.append([
            city, dates[i], tmax[i], tmin[i], precip[i], wind[i]
        ])
    return rows


def write_to_sheet(gc, tab_name, header, rows):
    sh = gc.open_by_key(SHEET_ID)
    try:
        ws = sh.worksheet(tab_name)
        sh.del_worksheet(ws)
    except gspread.exceptions.WorksheetNotFound:
        pass
    ws = sh.add_worksheet(title=tab_name, rows=str(len(rows) + 10), cols="10")
    ws.update("A1", [header] + rows)
    return ws


def main():
    gc = get_sheet_client()
    header = ["City", "Date", "Max Temp (C)", "Min Temp (C)", "Precipitation (mm)", "Max Wind (km/h)"]

    for duration_label, days_back in DURATIONS.items():
        all_rows = []
        for city, (lat, lon) in CITIES.items():
            print(f"Fetching {duration_label} weather for {city}...")
            data = fetch_weather(lat, lon, days_back)
            all_rows.extend(build_rows(city, data))

        tab_name = f"Weather_{duration_label}"
        write_to_sheet(gc, tab_name, header, all_rows)
        print(f"Wrote {len(all_rows)} rows to tab '{tab_name}'")

    print("Done. Open your Google Sheet to view the data.")


if __name__ == "__main__":
    main()
