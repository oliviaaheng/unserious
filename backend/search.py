import os

import requests
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional
from dataclasses import dataclass

load_dotenv()

client = OpenAI()


def fetch_image(keyword: str) -> str:
    api_key = os.environ.get("PIXABAY_API_KEY", "")
    if not api_key:
        return ""
    try:
        resp = requests.get(
            "https://pixabay.com/api/",
            params={
                "key": api_key,
                "q": keyword,
                "image_type": "photo",
                "per_page": 3,
            },
            timeout=5,
        )
        resp.raise_for_status()
        hits = resp.json().get("hits", [])
        if hits:
            return hits[0].get("webformatURL", "")
    except Exception:
        pass
    return ""


## DATA CLASSES


@dataclass
class Constraints:
    destination: str
    date_of_travel: str
    address: str
    freeform_text: str


def build_constraints(data) -> Constraints:
    return Constraints(
        destination=data.get("destination", ""),
        date_of_travel=data.get("date_of_travel", ""),
        address=data.get("address", ""),
        freeform_text=data.get("freeform_text", ""),
    )


## MODELS


class Event(BaseModel):
    name: str
    description: str
    address: str
    website: str
    image: str
    cost: str
    category: str


class GeneratedEvents(BaseModel):
    events: list[Event]


def events(constraints: Constraints) -> Optional[GeneratedEvents]:

    response = client.responses.parse(
        model="gpt-4o-2024-08-06",
        input=[
            {
                "role":
                "system",
                "content":
                "You are an expert travel guide who is all-knowledgeable about things to do in different destinations around the world. Generate 14 travel recommendations given some constraints. Make sure to follow the constraints!",
            },
            {
                "role":
                "user",
                "content":
                f"I am going to {constraints.destination} on {constraints.date_of_travel}. I will be staying around {constraints.address}, so find places nearby. Also, importantly, keep in mind the following: {constraints.freeform_text}"
            },
        ],
        text_format=GeneratedEvents,
    )

    result = response.output_parsed
    if result:
        for event in result.events:
            event.image = fetch_image(event.name)
    return result


class EventDetails(BaseModel):
    name: str
    description: str
    address: str
    website: str
    image: str
    cost: str
    category: str


class EventEntry(BaseModel):
    event: EventDetails
    start: str
    end: str
    pictures: list[str]


class Itinerary(BaseModel):
    events: list[EventEntry]


def itinerary(constraints: Constraints,
              event_preferences: list[dict]) -> Optional[Itinerary]:
    event_preferences = sorted(event_preferences,
                               key=lambda x: x["score"],
                               reverse=True)
    event_str = ""
    for entry in event_preferences:
        event = Event(**entry["event"])
        score = entry["score"]
        event_str += f"- {event.name} (Score: {score}) [{event.description}\n"

    response = client.responses.parse(
        model="gpt-4o-2024-08-06",
        input=[
            {
                "role":
                "system",
                "content":
                "You are an expert travel planner who creates detailed itineraries based on user preferences and event"
            },
            {
                "role":
                "user",
                "content":
                f"Given the following constraints: {constraints}, and the following ranked events: {event_str}, generate a detailed itinerary including event timings and pictures."
            },
        ],
        text_format=Itinerary,
    )
    if response.output_parsed:
        # set all pictures to empty list
        for event_entry in response.output_parsed.events:
            event_entry.pictures = []
    return response.output_parsed
