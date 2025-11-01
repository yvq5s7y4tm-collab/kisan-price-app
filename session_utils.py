import json
from pathlib import Path


TRACK_FILE = Path("tracklist_data.json")

def save_tracklist(data):
    try:
        TRACK_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as e:
        print("Error saving tracklist:", e)

def load_tracklist():
    if TRACK_FILE.exists():
        try:
            return json.loads(TRACK_FILE.read_text(encoding="utf-8"))
        except:
            return []
    return []
