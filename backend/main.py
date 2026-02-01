from flask import Flask, request, jsonify
from flask_cors import CORS
from search import build_constraints
import search

database = {}

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
        return jsonify(events.model_dump()), 200
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
