from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# In-memory storage
itineraries = {}
id_counter = 0


@app.route("/generate_activities", methods=["POST"])
def generate_activities():
    constraints = request.get_json()

    events = [
        {
            "name": constraints["destination"],
            "description": constraints["freeform_text"],
            "address": constraints["address"],
            "website": "",
            "image": "",
            "cost": "",
            "category": "",
            "start": "",
            "end": ""
        }
    ]

    return jsonify(events)

@app.route("/generate_itinerary", methods=["POST"])
def generate_itinerary():
    data = request.get_json()

    scored_events = sorted(
        data["events"],
        key=lambda x: x["score"],
        reverse=True
    )

    itinerary = {
        "events": [
            {
                "event": e["event"],
                "start": e["event"]["start"],
                "end": e["event"]["end"],
                "pictures": e.get("pictures", [])
            }
            for e in scored_events
        ]
    }

    return jsonify(itinerary)

@app.route("/upload_itinerary", methods=["POST"])
def upload_itinerary():
    data = request.get_json()

    global id_counter
    id_counter += 1
    itinerary_id = str(id_counter)
    itineraries[itinerary_id] = {"username": data["username"], "itinerary": data["itinerary"]}

    return jsonify({"itinerary_id": itinerary_id})

@app.route("/get_itineraries", methods=["POST"])
def get_itineraries():
    data = request.get_json()
    username = data["username"]
    ids = [k for k, v in itineraries.items() if v["username"] == username]

    return jsonify(ids)

@app.route("/fetch_itinerary", methods=["POST"])
def fetch_itinerary():
    data = request.get_json()
    itinerary_id = data["itinerary_id"]
    if itinerary_id in itineraries:
        return jsonify(itineraries[itinerary_id]["itinerary"])
    else:
        return jsonify({"error": "Itinerary not found"}), 404

@app.route("/update_itinerary", methods=["POST"])
def update_itinerary():
    data = request.get_json()
    username = data["username"]
    itinerary_id = data["itinerary_id"]
    itinerary = data["itinerary"]
    if itinerary_id in itineraries and itineraries[itinerary_id]["username"] == username:
        itineraries[itinerary_id]["itinerary"] = itinerary
        return jsonify({"status": "OK"})
    else:
        return jsonify({"error": "Not found or unauthorized"}), 404


if __name__ == "__main__":
    app.run(debug=True)
