from fastapi import FastAPI

import requests
import os
import json
import datetime
from datetime import timezone

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# ======================================================
# FASTAPI APP
# ======================================================

app = FastAPI()

# ======================================================
# GOOGLE CALENDAR CONFIG
# ======================================================

SCOPES = [
    "https://www.googleapis.com/auth/calendar"
]

# ======================================================
# GOOGLE CALENDAR SERVICE
# ======================================================

def get_calendar_service():

    token_info = json.loads(
        os.getenv("GOOGLE_TOKEN")
    )

    creds = Credentials.from_authorized_user_info(
        token_info,
        SCOPES
    )

    service = build(
        "calendar",
        "v3",
        credentials=creds
    )

    return service

# ======================================================
# ROOT ROUTE
# ======================================================

@app.get("/")
def home():

    return {
        "message":
        "ESP32 AI Assistant Backend Running"
    }

# ======================================================
# WEATHER ROUTE
# ======================================================

@app.get("/weather")
def get_weather():

    api_key = os.getenv(
        "OPENWEATHER_API_KEY"
    )

    city = "Haldia"

    # =========================
    # CURRENT WEATHER
    # =========================

    current_url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}"
        f"&appid={api_key}"
        f"&units=metric"
    )

    # =========================
    # FORECAST API
    # =========================

    forecast_url = (
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?q={city}"
        f"&appid={api_key}"
        f"&units=metric"
    )

    current_response = requests.get(
        current_url
    )

    forecast_response = requests.get(
        forecast_url
    )

    current_data = current_response.json()

    forecast_data = forecast_response.json()

    # =========================
    # BUILD FORECAST LIST
    # =========================

    daily_forecast = []

    added_days = set()

    for item in forecast_data["list"]:

        date = item["dt_txt"].split(" ")[0]

        if date not in added_days:

            added_days.add(date)

            daily_forecast.append({

                "day": date,

                "temp": round(
                    item["main"]["temp"]
                ),

                "condition":
                item["weather"][0]["main"]

            })

        if len(daily_forecast) >= 7:
            break

    # =========================
    # FINAL RESPONSE
    # =========================

    return {

        "city": city,

        "temp": round(
            current_data["main"]["temp"]
        ),

        "humidity":
        current_data["main"]["humidity"],

        "condition":
        current_data["weather"][0]["main"],

        "wind": round(
            current_data["wind"]["speed"]
        ),

        "feels_like": round(
            current_data["main"]["feels_like"]
        ),

        "forecast": daily_forecast
    }

# ======================================================
# CALENDAR ROUTE
# ======================================================

@app.get("/get_events")
def get_events():

    service = get_calendar_service()

    now = (
        datetime.datetime.utcnow()
        .isoformat()
        + "Z"
    )

    events_result = (
        service.events()
        .list(
            calendarId="primary",

            timeMin=now,

            maxResults=10,

            singleEvents=True,

            orderBy="startTime"
        )
        .execute()
    )

    events = events_result.get(
        "items",
        []
    )

    formatted_events = []

    for event in events:

        # =====================
        # RAW DATE/TIME
        # =====================

        start_raw = event["start"].get(
            "dateTime",
            event["start"].get("date")
        )

        # =====================
        # FORMAT DATE/TIME
        # =====================

        try:

            dt = (
                datetime.datetime
                .fromisoformat(
                    start_raw.replace(
                        "Z",
                        "+00:00"
                    )
                )
            )

            formatted_date = dt.strftime(
                "%d-%m-%Y"
            )

            formatted_time = dt.strftime(
                "%I:%M %p"
            )

        except:

            formatted_date = start_raw

            formatted_time = "All Day"

        # =====================
        # APPEND EVENT
        # =====================

        formatted_events.append({

            "title":
            event.get(
                "summary",
                "No Title"
            ),

            "date":
            formatted_date,

            "time":
            formatted_time
        })

    return formatted_events

# ======================================================
# NEXT EVENT ROUTE
# ======================================================

@app.get("/next_event")
def next_event():

    service = get_calendar_service()

    now = datetime.datetime.now(
        datetime.timezone.utc
    )

    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now.isoformat(),
            maxResults=20,
            singleEvents=True,
            orderBy="startTime"
        )
        .execute()
    )

    events = events_result.get(
        "items",
        []
    )

    # =====================================
    # FIND FIRST TIMED EVENT
    # =====================================

    for event in events:

        # Skip birthdays/all-day events
        if "dateTime" not in event["start"]:
            continue

        start_raw = event["start"]["dateTime"]

        try:

            event_dt = (
                datetime.datetime
                .fromisoformat(
                    start_raw.replace(
                        "Z",
                        "+00:00"
                    )
                )
            )

            minutes_remaining = int(
                (
                    event_dt - now
                ).total_seconds() / 60
            )

            return {

                "title":
                event.get(
                    "summary",
                    "No Title"
                ),

                "date":
                event_dt.strftime(
                    "%d-%m-%Y"
                ),

                "time":
                event_dt.strftime(
                    "%I:%M %p"
                ),

                "minutes_remaining":
                minutes_remaining
            }

        except Exception as e:

            print(
                "NEXT EVENT ERROR:",
                e
            )

            continue

    # =====================================
    # NO TIMED EVENTS FOUND
    # =====================================

    return {

        "title":
        "No Upcoming Events",

        "date":
        "",

        "time":
        "",

        "minutes_remaining":
        -1
    }