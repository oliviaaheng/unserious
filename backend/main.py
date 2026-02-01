from flask import Flask, request, jsonify
from flask_cors import CORS
from search import build_constraints
import search
import uuid

database = {
    "itineraries": {},  # itinerary_id -> { email, itinerary }
    "user_itineraries": {},  # email -> [itinerary_id, ...]
}

app = Flask(__name__)
CORS(
    app,
    origins=[
        "http://localhost:4321",
        "http://127.0.0.1:4321",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
    ],
)


@app.route("/generate_activities", methods=["POST"])
def generate_activities():
    constraints = build_constraints(request.get_json())
    events = search.events(constraints)
    if events:
        return jsonify([e.model_dump() for e in events.events]), 200
    else:
        return jsonify({"error": "Failed to generate events"}), 500


@app.route("/generate_itinerary", methods=["POST"])
def generate_itinerary():
    req = request.get_json()
    constraints = build_constraints(req)
    itinerary = search.itinerary(constraints, req["events"])
    if itinerary:
        return jsonify(itinerary.model_dump()), 200
    else:
        return jsonify({"error": "Failed to generate itinerary"}), 500


@app.route("/upload_itinerary", methods=["POST"])
def upload_itinerary():
    req = request.get_json()
    email = req["email"]
    itinerary = req["itinerary"]
    itinerary_id = str(uuid.uuid4())
    database["itineraries"][itinerary_id] = {
        "email": email,
        "itinerary": itinerary,
    }
    if email not in database["user_itineraries"]:
        database["user_itineraries"][email] = []
    database["user_itineraries"][email].append(itinerary_id)
    return jsonify({"itinerary_id": itinerary_id}), 200


@app.route("/get_itineraries", methods=["POST"])
def get_itineraries():
    req = request.get_json()
    email = req["email"]
    ids = database["user_itineraries"].get(email, [])
    return jsonify(ids), 200


@app.route("/fetch_itinerary", methods=["POST"])
def fetch_itinerary():
    req = request.get_json()
    itinerary_id = req["itinerary_id"]
    record = database["itineraries"].get(itinerary_id)
    if record is None:
        return jsonify({"error": "Itinerary not found"}), 404
    return jsonify(record["itinerary"]), 200


@app.route("/add_photo", methods=["POST"])
def add_photo():
    req = request.get_json()
    itinerary_id = req["itinerary_id"]
    event_index = req["event_index"]
    photo = req["photo"]
    record = database["itineraries"].get(itinerary_id)
    if record is None:
        return jsonify({"error": "Itinerary not found"}), 404
    events = record["itinerary"]["events"]
    if event_index < 0 or event_index >= len(events):
        return jsonify({"error": "Invalid event index"}), 400
    events[event_index]["pictures"].append(photo)
    return jsonify({
        "status": "ok",
        "pictures": events[event_index]["pictures"],
    }), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
