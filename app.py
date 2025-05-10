from flask import Flask, jsonify
import time, requests
from bs4 import BeautifulSoup

app = Flask(__name__)

MATCH_URL = "https://www.foxsports.com.au/nrl/nrl-premiership/match-centre/NRL20251003"
API_ENDPOINT = "https://supression-sniper-live.onrender.com"

def detect_phase(clock_str):
    try:
        mins = int(clock_str.split(":")[0])
        if mins <= 8:
            return "Phase 1", 35.0
        elif mins <= 20:
            return "Phase 2", 31.5
        elif mins <= 40:
            return "Phase 3", 29.0
        else:
            return "Post-Halftime", 0.0
    except:
        return "Unknown", 0.0

def fetch_live_data():
    try:
        res = requests.get(MATCH_URL, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        team_names = [e.text.strip() for e in soup.select('.scoreboard__team-name')]
        score = soup.select_one('.scoreboard__score')
        clock = soup.select_one('.scoreboard__time')
        status = soup.select_one('.scoreboard__status')

        clock_str = clock.text.strip() if clock else "00:00"
        status_text = status.text.strip() if status else "Unknown"
        score_text = score.text.strip() if score else "N/A"

        phase, confidence = detect_phase(clock_str)
        trigger_ready = status_text in ["1st Half", "In Progress"] and phase != "Post-Halftime"

        return {
            "trigger": trigger_ready,
            "phase": phase,
            "confidence": f"{confidence}%",
            "teams": team_names,
            "score": score_text,
            "clock": clock_str,
            "status": status_text,
            "timestamp": time.time(),
            "api": API_ENDPOINT
        }

    except Exception as e:
        return {"error": str(e), "trigger": False, "api": API_ENDPOINT, "timestamp": time.time()}

@app.route("/trigger")
def trigger():
    return jsonify(fetch_live_data())

@app.route("/")
def health():
    return jsonify({"status": "Live bot active", "api": API_ENDPOINT})
