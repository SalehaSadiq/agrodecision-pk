def get_weather_context(district, province):

    demo_weather = {
        "source_type": "Demo assumption",
        "source": "AGRODECISION PK demonstration scenario",
        "title": "Demonstration weather context",
        "url": "",
        "timestamp": "Demo timestamp",
        "demo": True,
        "summary": (
            "Recent conditions are represented using demonstration "
            "data. The scenario assumes moderate water availability "
            "and conditions that could contribute to crop water stress."
        ),
        "temperature_c": 30,
        "recent_rainfall_mm": 5,
        "humidity_percent": 55,
    }

    return demo_weather
