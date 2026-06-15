from fastapi import FastAPI

import requests
import os
import json
import datetime

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

app = FastAPI()

# =====================================
# GOOGLE CALENDAR CONFIG
# =====================================

SCOPES = ["https://www.googleapis.com/auth/calendar"]


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


# =====================================
# ROOT ROUTE
# =====================================

@app.get("/")
def home():

    return {
        "message": "ESP32 AI Assistant Backend Running"
    }


# =====================================
# WEATHER ROUTE
# =====================================

@app.get("/weather")
def get_weather():

    api_key = os.getenv("OPENWEATHER_API_KEY")

    city = "Haldia"

    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}"
        f"&appid={api_key}"
        f"&units=metric"
    )

    response = requests.get(url)

    data = response.json()

    return {
        "city": city,
        "temp": round(data["main"]["temp"]),
        "humidity": data["main"]["humidity"],
        "condition": data["weather"][0]["main"],
        "wind": round(data["wind"]["speed"]),
        "feels_like": round(data["main"]["feels_like"])
    }


# =====================================
# CALENDAR ROUTE
# =====================================

@app.get("/get_events")
def get_events():

    service = get_calendar_service()

    now = datetime.datetime.utcnow().isoformat() + "Z"

    events_result = service.events().list(
        calendarId="primary",
        timeMin=now,
        maxResults=10,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    events = events_result.get("items", [])

    formatted_events = []

    for event in events:

        formatted_events.append({
            "title": event.get("summary", "No Title"),

            "start": event["start"].get(
                "dateTime",
                event["start"].get("date")
            )
        })

    return formatted_events