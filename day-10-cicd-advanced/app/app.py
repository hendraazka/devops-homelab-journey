from flask import Flask, render_template, jsonify, request
import requests

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
        else:
            url = f"{ALADHAN_BASE}/timingsByCity"
            url += f"?city={requests.utils.quote(city)}&country=Indonesia&method={METHOD}"

        res = requests.get(url, timeout=10)
        res.raise_for_status()
        json = res.json()
        if json.get("code") != 200:
            return jsonify({"error": "Respons API tidak valid"}), 502
        return jsonify(normalize(json["data"]))
    except requests.RequestException as e:
        return jsonify({"error": f"Gagal mengambil jadwal: {e}"}), 502


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
