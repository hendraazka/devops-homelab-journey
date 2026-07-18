from app import app

def test_health():
    """Pastikan aplikasi bisa merespons"""
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200

def test_api_timings_default():
    """Pastikan endpoint API jadwal sholat merespons dengan benar"""
    client = app.test_client()
    response = client.get("/api/timings?city=Jakarta")
    assert response.status_code == 200
    data = response.get_json()
    assert "timings" in data
    assert "Fajr" in data["timings"]

def test_static_files_served():
    """Pastikan file CSS dan JS bisa diakses"""
    client = app.test_client()
    css_response = client.get("/static/css/style.css")
    js_response = client.get("/static/js/app.js")
    assert css_response.status_code == 200
    assert js_response.status_code == 200
