import requests


# Representative coordinates for districts used by the MVP.
# These are only used to query public weather data.
DISTRICT_COORDS = {
    # Punjab
    "Lahore": (31.5204, 74.3587),
    "Faisalabad": (31.4504, 73.1350),
    "Multan": (30.1575, 71.5249),
    "Rawalpindi": (33.5651, 73.0169),
    "Gujranwala": (32.1877, 74.1945),
    "Sargodha": (32.0836, 72.6711),
    "Bahawalpur": (29.3956, 71.6836),
    "Sahiwal": (30.6682, 73.1114),
    "Dera Ghazi Khan": (30.0561, 70.6348),

    # Sindh
    "Karachi": (24.8607, 67.0011),
    "Hyderabad": (25.3960, 68.3578),
    "Sukkur": (27.7052, 68.8574),
    "Larkana": (27.5589, 68.2120),
    "Nawabshah": (26.2442, 68.4100),
    "Mirpur Khas": (25.5251, 69.0159),
    "Thatta": (24.7475, 67.9235),

    # Khyber Pakhtunkhwa
    "Peshawar": (34.0151, 71.5249),
    "Mardan": (34.1989, 72.0407),
    "Swat": (35.2227, 72.4258),
    "Abbottabad": (34.1688, 73.2215),
    "Kohat": (33.5869, 71.4414),
    "Bannu": (32.9861, 70.6042),
    "Dera Ismail Khan": (31.8327, 70.9024),

    # Balochistan
    "Quetta": (30.1798, 66.9750),
    "Sibi": (29.5430, 67.8773),
    "Ziarat": (30.3811, 67.7250),
    "Khuzdar": (27.8000, 66.6167),
    "Turbat": (26.0023, 63.0544),
    "Chaman": (30.9177, 66.4599),
}

def get_district_coordinates(district):
    """
    Return representative latitude/longitude for a district.

    If the district is not in the lookup table, return None.
    """

    return DISTRICT_COORDS.get(district)


def get_weather(district, coords=None):
    """
    Retrieve public weather information when possible.

    If the public weather service is unavailable, the function
    returns clearly labelled demonstration weather data.

    No weather result is treated as proof of crop causation.
    """

    if coords is None:
        coords = get_district_coordinates(district)

    if coords is None:
        return get_demo_weather(district)

    latitude, longitude = coords

    try:
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": (
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "precipitation"
                ),
                "daily": (
                    "temperature_2m_max,"
                    "temperature_2m_min,"
                    "precipitation_sum"
                ),
                "past_days": 3,
                "forecast_days": 1,
                "timezone": "auto",
            },
            timeout=10,
        )

        response.raise_for_status()
        data = response.json()

        current = data.get("current", {})
        daily = data.get("daily", {})

        precipitation_values = daily.get(
            "precipitation_sum",
            [],
        )

        recent_rainfall = sum(
            float(value or 0)
            for value in precipitation_values
        )

        return {
            "source_type": "External evidence",
            "source": "Open-Meteo",
            "title": "Public weather data",
            "url": "https://open-meteo.com/",
            "timestamp": current.get("time", ""),
            "demo": False,
            "summary": (
                f"Public weather data for {district} were retrieved. "
                "These conditions may be relevant to crop water "
                "stress but do not establish its cause."
            ),
            "temperature_c": current.get(
                "temperature_2m"
            ),
            "recent_rainfall_mm": recent_rainfall,
            "humidity_percent": current.get(
                "relative_humidity_2m"
            ),
            "coordinates": {
                "latitude": latitude,
                "longitude": longitude,
            },
        }

    except Exception:
        return get_demo_weather(district)


def get_demo_weather(district):
    """
    Deterministic fallback weather data.

    This is demonstration data and must not be presented
    as real weather information.
    """

    return {
        "source_type": "Demo assumption",
        "source": "AGRODECISION PK demonstration scenario",
        "title": "Demonstration weather context",
        "url": "",
        "timestamp": "Demo timestamp",
        "demo": True,
        "summary": (
            f"Live weather data were unavailable for {district}. "
            "The application is continuing in demonstration mode. "
            "The scenario assumes conditions that could contribute "
            "to crop water stress."
        ),
        "temperature_c": 30,
        "recent_rainfall_mm": 5,
        "humidity_percent": 55,
    }


def get_weather_context(district, province=None):
    """
    Backward-compatible wrapper for the rest of the application.
    """

    return get_weather(district)
