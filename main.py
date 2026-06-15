from fastapi import FastAPI
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

import datetime
import os.path
import requests

app = FastAPI()

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def get_calendar_service():

    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file(
            "token.json",
            SCOPES
        )

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    service = build("calendar", "v3", credentials=creds)

    return service

@app.get("/")
def home():

    return {
        "message": "AI Calendar Assistant Backend Running"
    }

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
            "start": event["start"].get(
                "dateTime",
                event["start"].get("date")
            ),
            "title": event.get("summary", "No Title")
        })

    return formatted_events

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

@app.get("/weather")
def get_weather():

    api_key = "e4801ed7d319483ccd046026e9182882"

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