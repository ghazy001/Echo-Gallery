# main/utils.py
import logging
import requests
from django.conf import settings
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


# -------- PROFANITY FILTERING --------

def clean_profanity(text: str) -> str:
    """
    Send text to the profanity filter API and return the censored string.
    If anything goes wrong, just return the original text.

    Expected API Ninjas response:
    {
        "original": "damn it!",
        "censored": "**** it!",
        "has_profanity": true
    }
    """
    if not text:
        return text

    api_key = getattr(settings, "PROFANITY_API_KEY", "")
    if not api_key:
        logger.warning("PROFANITY_API_KEY not set in settings")
        return text

    base_url = getattr(settings, "PROFANITY_API_URL", "")
    timeout = getattr(settings, "PROFANITY_API_TIMEOUT", 5)

    # URL encode user text
    url = f"{base_url}?text={quote_plus(text)}"

    try:
        resp = requests.get(
            url,
            headers={"X-Api-Key": api_key},
            timeout=timeout,
        )

        if resp.status_code == requests.codes.ok:
            data = resp.json()

            # IMPORTANT: API uses "censored", not "clean"
            censored = data.get("censored")
            if censored:
                return censored

            # fallback if they ever rename
            return data.get("clean", text)

        else:
            logger.error(
                "Profanity API non-200: %s %s",
                resp.status_code,
                resp.text[:200],
            )
            return text

    except requests.RequestException as e:
        logger.exception("Profanity API request failed: %s", e)
        return text


# -------- WEATHER API --------
def get_weather_for_city(city: str) -> dict:
    """
    Use Open-Meteo (free) to get current weather for this city.
    Returns dict shaped for the frontend.
    {
        "ok": True,
        "city": "...",
        "temp": 21.3,
        "feels_like": 21.3,
        "humidity": 60,
        "wind_speed": 14.5,
        "cloud_pct": 40,
    }
    On failure:
    { "error": "..." }
    """

    if not city:
        return {"error": "No city provided."}

    try:
        # 1) Geocode city -> lat/lon
        geo_url = (
            f"{settings.OPENMETEO_GEOCODE_URL}"
            f"?name={quote_plus(city)}&count=1"
        )

        geo_resp = requests.get(
            geo_url,
            timeout=settings.OPENMETEO_TIMEOUT,
        )

        if geo_resp.status_code != 200:
            logger.error(
                "Geocoding non-200: %s %s",
                geo_resp.status_code,
                geo_resp.text[:200],
            )
            return {"error": "Could not locate city."}

        geo_json = geo_resp.json()
        results = geo_json.get("results")
        if not results:
            return {"error": "City not found."}

        first = results[0]
        lat = first.get("latitude")
        lon = first.get("longitude")
        resolved_name = first.get("name")  # use normalized/pretty name if available
        if lat is None or lon is None:
            return {"error": "Invalid location data."}

        # 2) Fetch current weather
        # We'll ask for current weather + humidity, etc.
        weather_url = (
            f"{settings.OPENMETEO_WEATHER_URL}"
            f"?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,cloud_cover"
            f"&timezone=auto"
        )

        w_resp = requests.get(
            weather_url,
            timeout=settings.OPENMETEO_TIMEOUT,
        )

        if w_resp.status_code != 200:
            logger.error(
                "Weather non-200: %s %s",
                w_resp.status_code,
                w_resp.text[:200],
            )
            return {"error": "Could not fetch weather."}

        w_json = w_resp.json()
        current = w_json.get("current", {})

        temp_c = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        wind_speed = current.get("wind_speed_10m")
        cloud_pct = current.get("cloud_cover")

        # Open-Meteo does not give 'feels_like' in this endpoint.
        # We'll just reuse temp as feels_like for display
        feels_like = temp_c

        return {
            "ok": True,
            "city": resolved_name or city,
            "temp": temp_c,
            "feels_like": feels_like,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "cloud_pct": cloud_pct,
        }

    except requests.RequestException as e:
        logger.exception("Weather request failed: %s", e)
        return {"error": "Weather service unreachable."}