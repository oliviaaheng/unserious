import os
from google import genai
from google.genai import types  # pip install -q -U google-genai
# https://ai.google.dev/gemini-api/docs/quickstart
from dotenv import load_dotenv

load_dotenv()

# Initialize without forcing 'v1' to avoid the 400 error
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# EXAMPLE FROM GOOGLE QUICKSTART
# response = client.models.generate_content(
#     model="gemini-3-flash-preview", contents="Explain how AI works in a few words"
# )
# print(response.text)

def get_travel_json(user_input: dict):
    # Use types.GenerateContentConfig for strict parameter naming
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
                    "cost": {"type": "STRING"},
                    "category": {"type": "STRING"}
                },
                "required": ["name", "description", "address","website", "cost", "category"]
            }
        }
    )

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=f"Generate 14 travel recommendations given the constraints of {user_input['destination']} on {user_input['date_of_travel']}. Keep in mind the following: {user_input['freeform_text']}.",
        config=config  # Use 'config', not 'generation_config'
    )
    
    return response.text

# test data
input_data = {
    "destination": "Porto, Portugal",
    "date_of_travel": "May 9, 2026",
    "address": "130 Waterman St. Providence, RI 02906",
    "freeform_text": "i am a relaxed traveler who likes starting my day around 10 am"
}

if __name__ == "__main__":
    print(get_travel_json(input_data))