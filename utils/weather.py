import requests
from data.demo_data import DEMO_WEATHER


def get_weather(district, coords):
    lat, lon = coords
    url = "https://api.open-meteo.com/v1/forecast"
    params = {"latitude": lat, "longitude": lon, "current": "temperature_2m,relative_humidity_2m,precipitation", "hourly": "temperature_2m,relative_humidity_2m,precipitation", "past_days": 2, "forecast_days": 2, "timezone": "auto"}
    try:
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        data = r.json()
        current = data.get("current", {})
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        rain = hourly.get("precipitation", [])
        temp = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        current_precip = current.get("precipitation", 0) or 0
        recent = sum(float(x or 0) for x in rain[-24:]) if rain else current_precip
        next24 = sum(float(x or 0) for x in rain[-24:]) if rain else current_precip
        # Keep chart small and robust.
        daily = []
        for i in range(min(4, len(rain) // 24)):
            chunk = rain[i*24:(i+1)*24]
            daily.append({"date": times[i*24][:10] if i*24 < len(times) else f"Period {i+1}", "rain_mm": round(sum(float(x or 0) for x in chunk), 2)})
        return {"temperature_c": float(temp or 0), "humidity_pct": float(humidity or 0), "recent_rain_mm": round(recent, 2), "next_24h_rain_mm": round(next24, 2), "label": "LIVE WEATHER DATA", "source_type": "PUBLIC SOURCE — Open-Meteo", "daily": daily}
    except Exception:
        return {**DEMO_WEATHER, "label": "DEMO WEATHER DATA", "source_type": "DEMO ASSUMPTION — live weather unavailable"}
