from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional, Tuple
from dataclasses import dataclass

load_dotenv()

client = OpenAI()

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

    return response.output_parsed


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


def itinerary(
        constraints: Constraints,
        event_preferences: list[Tuple[Event, float]]) -> Optional[Itinerary]:
    event_preferences = sorted(event_preferences,
                               key=lambda x: x[1],
                               reverse=True)
    event_str = ""
    for event, score in event_preferences:
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
    return response.output_parsed
