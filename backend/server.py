import json
import sqlite3
import uuid
import sys
from pathlib import Path

from flask import Flask, request, jsonify
from flask_cors import CORS

# Allow imports from sibling packages
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.search import get_travel_json, generate_itinerary_json
from db.setup import setup, DB_PATH

app = Flask(__name__)
CORS(app)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/generate_activities", methods=["POST"])
def generate_activities():
    constraints = request.get_json()
    raw = get_travel_json(constraints)
    events = json.loads(raw)
    return jsonify(events)


@app.route("/generate_itinerary", methods=["POST"])
def generate_itinerary():
    data = request.get_json()
    constraints = {
        "destination": data["destination"],
        "date_of_travel": data["date_of_travel"],
        "address": data.get("address", ""),
        "freeform_text": data.get("freeform_text", ""),
    }
    scored_events = data["events"]
    raw = generate_itinerary_json(constraints, scored_events)
    itinerary = json.loads(raw)
    return jsonify(itinerary)


@app.route("/upload_itinerary", methods=["POST"])
def upload_itinerary():
    data = request.get_json()
    email = data["email"]
    itinerary = data["itinerary"]
    itinerary_id = str(uuid.uuid4())

    db = get_db()
    try:
        db.execute(
            "INSERT INTO itineraries (id, user_email) VALUES (?, ?)",
            (itinerary_id, email),
        )
        for i, entry in enumerate(itinerary["events"]):
            event = entry["event"]
            cursor = db.execute(
                """INSERT INTO events
                   (itinerary_id, name, description, address, website, image, cost, category, start_time, end_time, sort_order)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    itinerary_id,
                    event.get("name", ""),
                    event.get("description", ""),
                    event.get("address", ""),
                    event.get("website", ""),
                    event.get("image", ""),
                    event.get("cost", ""),
                    event.get("category", ""),
                    entry.get("start", ""),
                    entry.get("end", ""),
                    i,
                ),
            )
            event_id = cursor.lastrowid
            for pic_url in entry.get("pictures", []):
                db.execute(
                    "INSERT INTO pictures (event_id, url) VALUES (?, ?)",
                    (event_id, pic_url),
                )
        db.commit()
    finally:
        db.close()

    return jsonify({"itinerary_id": itinerary_id})


@app.route("/get_itineraries", methods=["POST"])
def get_itineraries():
    data = request.get_json()
    email = data["email"]

    db = get_db()
    try:
        rows = db.execute(
            "SELECT id FROM itineraries WHERE user_email = ? ORDER BY created_at DESC",
            (email,),
        ).fetchall()
    finally:
        db.close()

    return jsonify([row["id"] for row in rows])


@app.route("/fetch_itinerary", methods=["POST"])
def fetch_itinerary():
    data = request.get_json()
    itinerary_id = data["itinerary_id"]

    db = get_db()
    try:
        itin = db.execute(
            "SELECT * FROM itineraries WHERE id = ?", (itinerary_id,)
        ).fetchone()
        if not itin:
            return jsonify({"error": "Itinerary not found"}), 404

        event_rows = db.execute(
            "SELECT * FROM events WHERE itinerary_id = ? ORDER BY sort_order",
            (itinerary_id,),
        ).fetchall()

        events = []
        for er in event_rows:
            pic_rows = db.execute(
                "SELECT url FROM pictures WHERE event_id = ?", (er["id"],)
            ).fetchall()
            events.append(
                {
                    "event": {
                        "name": er["name"],
                        "description": er["description"],
                        "address": er["address"],
                        "website": er["website"],
                        "image": er["image"],
                        "cost": er["cost"],
                        "category": er["category"],
                    },
                    "start": er["start_time"],
                    "end": er["end_time"],
                    "pictures": [p["url"] for p in pic_rows],
                }
            )
    finally:
        db.close()

    return jsonify({"events": events})


@app.route("/update_itinerary", methods=["POST"])
def update_itinerary():
    data = request.get_json()
    email = data["email"]
    itinerary_id = data["itinerary_id"]
    itinerary = data["itinerary"]

    db = get_db()
    try:
        row = db.execute(
            "SELECT * FROM itineraries WHERE id = ? AND user_email = ?",
            (itinerary_id, email),
        ).fetchone()
        if not row:
            return jsonify({"error": "Not found or unauthorized"}), 404

        # Delete old events (pictures cascade-deleted)
        db.execute("DELETE FROM events WHERE itinerary_id = ?", (itinerary_id,))

        # Insert new events
        for i, entry in enumerate(itinerary["events"]):
            event = entry["event"]
            cursor = db.execute(
                """INSERT INTO events
                   (itinerary_id, name, description, address, website, image, cost, category, start_time, end_time, sort_order)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    itinerary_id,
                    event.get("name", ""),
                    event.get("description", ""),
                    event.get("address", ""),
                    event.get("website", ""),
                    event.get("image", ""),
                    event.get("cost", ""),
                    event.get("category", ""),
                    entry.get("start", ""),
                    entry.get("end", ""),
                    i,
                ),
            )
            event_id = cursor.lastrowid
            for pic_url in entry.get("pictures", []):
                db.execute(
                    "INSERT INTO pictures (event_id, url) VALUES (?, ?)",
                    (event_id, pic_url),
                )
        db.commit()
    finally:
        db.close()

    return jsonify({"status": "OK"})


# Ensure tables exist on startup
setup()

if __name__ == "__main__":
    app.run(debug=True)
