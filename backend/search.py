import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def get_travel_json(user_input: dict):
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema={
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "name": {"type": "STRING"},
                    "description": {"type": "STRING"},
                    "address": {"type": "STRING"},
                    "website": {"type": "STRING"},
                    "image": {"type": "STRING"},
                    "cost": {"type": "STRING"},
                    "category": {"type": "STRING"},
                },
                "required": [
                    "name",
                    "description",
                    "address",
                    "website",
                    "image",
                    "cost",
                    "category",
                ],
            },
        },
    )

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=(
            f"Generate 14 travel recommendations given the constraints of "
            f"{user_input['destination']} on {user_input['date_of_travel']}. "
            f"Keep in mind the following: {user_input['freeform_text']}."
        ),
        config=config,
    )

    return response.text


def generate_itinerary_json(constraints: dict, scored_events: list):
    events_description = "\n".join(
        f"- {e['event']['name']} (score: {e['score']}): {e['event'].get('description', '')}"
        for e in scored_events
    )

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema={
            "type": "OBJECT",
            "properties": {
                "events": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "event": {
                                "type": "OBJECT",
                                "properties": {
                                    "name": {"type": "STRING"},
                                    "description": {"type": "STRING"},
                                    "address": {"type": "STRING"},
                                    "website": {"type": "STRING"},
                                    "image": {"type": "STRING"},
                                    "cost": {"type": "STRING"},
                                    "category": {"type": "STRING"},
                                },
                                "required": [
                                    "name",
                                    "description",
                                    "address",
                                    "website",
                                    "image",
                                    "cost",
                                    "category",
                                ],
                            },
                            "start": {"type": "STRING"},
                            "end": {"type": "STRING"},
                            "pictures": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"},
                            },
                        },
                        "required": ["event", "start", "end", "pictures"],
                    },
                }
            },
            "required": ["events"],
        },
    )

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=(
            f"Create a timed travel itinerary for {constraints['destination']} "
            f"on {constraints['date_of_travel']}. "
            f"The traveler is staying at {constraints.get('address', 'N/A')}. "
            f"Preferences: {constraints.get('freeform_text', 'none')}.\n\n"
            f"Arrange the following events into a day itinerary with start/end times "
            f"(ISO 8601 datetime strings). Higher-scored events should be prioritized. "
            f"Include relevant image URLs in the pictures array if available.\n\n"
            f"Events:\n{events_description}"
        ),
        config=config,
    )

    return response.text


if __name__ == "__main__":
    input_data = {
        "destination": "Porto, Portugal",
        "date_of_travel": "May 9, 2026",
        "address": "130 Waterman St. Providence, RI 02906",
        "freeform_text": "i am a relaxed traveler who likes starting my day around 10 am",
    }
    print(get_travel_json(input_data))
