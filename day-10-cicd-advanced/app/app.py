from flask import Flask, render_template, jsonify, request
import requests
import logging
from pythonjsonlogger import jsonlogger

logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s"
)
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

app = Flask(__name__)

ALADHAN_BASE = "https://api.aladhan.com/v1"
METHOD = 20  # Kemenag Indonesia

INDONESIAN_CITIES = [
    "Jakarta", "Bandung", "Surabaya", "Medan", "Makassar",
    "Semarang", "Palembang", "Yogyakarta", "Denpasar", "Banjarmasin",
    "Pontianak", "Padang", "Pekanbaru", "Manado", "Aceh",
    "Balikpapan", "Cirebon", "Solo", "Bogor", "Tangerang",
]

PRAYER_ORDER = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]
PRAYER_LABELS = {
    "Fajr": "Subuh", "Sunrise": "Terbit", "Dhuhr": "Dzuhur",
    "Asr": "Ashar", "Maghrib": "Maghrib", "Isha": "Isya",
}


def normalize(data):
    timings = data.get("timings", {})
    hijri = data.get("date", {}).get("hijri", {})
    gregorian = data.get("date", {}).get("gregorian", {})
    meta = data.get("meta", {})
    timezone = meta.get("timezone", "")
    city = timezone.split("/")[-1].replace("_", " ") if "/" in timezone else ""
    return {
        "timings": {k: timings.get(k, "") for k in PRAYER_ORDER},
        "hijri": {
            "day": hijri.get("day"),
            "month": (hijri.get("month") or {}).get("en"),
            "year": hijri.get("year"),
            "weekday": (hijri.get("weekday") or {}).get("en"),
        },
        "gregorian": {
            "day": gregorian.get("day"),
            "month": (gregorian.get("month") or {}).get("en"),
            "year": gregorian.get("year"),
            "weekday": (gregorian.get("weekday") or {}).get("en"),
        },
        "city": city,
        "timezone": timezone,
    }


@app.route("/")
def index():
    return render_template("index.html", cities=INDONESIAN_CITIES)


@app.route("/api/timings")
def api_timings():
    city = request.args.get("city", "Jakarta")
    lat = request.args.get("lat")
    lng = request.args.get("lng")

    try:
        if lat and lng:
            url = f"{ALADHAN_BASE}/timings?latitude={lat}&longitude={lng}&method={METHOD}"
            logger.info("prayer_timings_request", extra={"mode": "geolocation", "lat": lat, "lng": lng})
        else:
            url = f"{ALADHAN_BASE}/timingsByCity"
            url += f"?city={requests.utils.quote(city)}&country=Indonesia&method={METHOD}"
            logger.info("prayer_timings_request", extra={"mode": "city_search", "city": city})

        res = requests.get(url, timeout=10)
        res.raise_for_status()
        json_data = res.json()
        if json_data.get("code") != 200:
            logger.warning("prayer_timings_invalid_response", extra={"city": city, "api_code": json_data.get("code")})
            return jsonify({"error": "Respons API tidak valid"}), 502
        logger.info("prayer_timings_success", extra={"city": city})
        return jsonify(normalize(json_data["data"]))
    except requests.RequestException as e:
        logger.error("prayer_timings_failed", extra={"city": city, "error": str(e)})
        return jsonify({"error": f"Gagal mengambil jadwal: {e}"}), 502


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
