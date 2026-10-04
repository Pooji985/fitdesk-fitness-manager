from datetime import datetime, timezone, timedelta
from math import isfinite
from typing import Optional, Dict, Tuple
import logging
from zoneinfo import ZoneInfo
import httpx

logger = logging.getLogger(__name__)

# In-memory forecast cache: key -> (cached_at, data)
_forecast_cache: Dict[str, Tuple[datetime, dict]] = {}
CACHE_TTL_MINUTES = 15

# WMO Weather interpretation codes
WMO_WEATHER_CODES = {
    0: "Clear Sky",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing Rime Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    61: "Slight Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",
    71: "Slight Snow Fall",
    73: "Moderate Snow Fall",
    75: "Heavy Snow Fall",
    80: "Slight Rain Showers",
    81: "Moderate Rain Showers",
    82: "Violent Rain Showers",
    95: "Thunderstorm",
    96: "Thunderstorm with Slight Hail",
    99: "Thunderstorm with Heavy Hail",
}


def _weather_unavailable() -> dict:
    return {
        "status": "unavailable",
        "temperature": None,
        "precipitation_probability": None,
        "wind_speed": None,
        "condition": "Weather unavailable",
        "alert_message": "Weather unavailable — check manually.",
        "badge_color": "text-slate-300 bg-slate-500/10 border-slate-500/20",
    }


def _evaluate_weather_condition(
    temperature: float,
    precip_prob: int,
    wind_speed: float,
    weather_code: int,
) -> dict:
    """Classifies weather conditions into Optimal, Warning, or Inclement Weather."""
    condition_desc = WMO_WEATHER_CODES.get(weather_code, "Partly Cloudy")

    # 1. Inclement Weather (Red Flag)
    if (
        weather_code in [65, 82, 95, 96, 99]
        or precip_prob >= 70
        or temperature >= 36.0
        or wind_speed >= 45.0
    ):
        return {
            "status": "inclement",
            "temperature": round(temperature, 1),
            "precipitation_probability": precip_prob,
            "wind_speed": round(wind_speed, 1),
            "condition": condition_desc,
            "alert_message": "Heavy precipitation or severe weather forecast. Move session to indoor backup studio.",
            "badge_color": "text-rose-400 bg-rose-500/10 border-rose-500/20",
        }

    # 2. Warning (Yellow Flag)
    if (
        weather_code in [51, 53, 55, 61, 63, 71, 73, 80, 81]
        or precip_prob >= 30
        or temperature >= 31.0
        or wind_speed >= 30.0
    ):
        return {
            "status": "warning",
            "temperature": round(temperature, 1),
            "precipitation_probability": precip_prob,
            "wind_speed": round(wind_speed, 1),
            "condition": condition_desc,
            "alert_message": "Moderate rain risk or high heat forecast. Advise attendees on hydration and apparel.",
            "badge_color": "text-amber-400 bg-amber-500/10 border-amber-500/20",
        }

    # 3. Optimal (Green Flag)
    return {
        "status": "optimal",
        "temperature": round(temperature, 1),
        "precipitation_probability": precip_prob,
        "wind_speed": round(wind_speed, 1),
        "condition": condition_desc,
        "alert_message": "Optimal outdoor weather conditions. Clear skies and mild temperatures.",
        "badge_color": "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    }


def get_outdoor_class_weather(
    latitude: float,
    longitude: float,
    target_time: Optional[datetime] = None,
) -> dict:
    """Queries Open-Meteo API for target venue coordinates with in-memory caching and fallback."""
    now = datetime.now(timezone.utc)
    if target_time is None:
        target_time = now

    cache_key = f"{round(latitude, 2)}:{round(longitude, 2)}:{target_time.strftime('%Y%m%d%H')}"

    # Check in-memory cache
    if cache_key in _forecast_cache:
        cached_at, cached_result = _forecast_cache[cache_key]
        if now - cached_at < timedelta(minutes=CACHE_TTL_MINUTES):
            return cached_result

    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "temperature_2m,precipitation_probability,weathercode,windspeed_10m",
            "timezone": "auto",
        }
        with httpx.Client(timeout=3.0) as client:
            response = client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                hourly = data.get("hourly", {})
                times = hourly.get("time", [])
                timezone_name = data.get("timezone")
                temperature_values = hourly.get("temperature_2m")
                precipitation_values = hourly.get("precipitation_probability")
                wind_values = hourly.get("windspeed_10m")
                code_values = hourly.get("weathercode")
                if (
                    not isinstance(times, list)
                    or not times
                    or not isinstance(timezone_name, str)
                    or not isinstance(temperature_values, list)
                    or not isinstance(precipitation_values, list)
                    or not isinstance(wind_values, list)
                    or not isinstance(code_values, list)
                    or any(len(values) != len(times) for values in (temperature_values, precipitation_values, wind_values, code_values))
                ):
                    raise ValueError("Open-Meteo response is missing aligned hourly forecast fields")

                try:
                    local_timezone = ZoneInfo(timezone_name)
                except Exception:
                    utc_offset = data.get("utc_offset_seconds")
                    if not isinstance(utc_offset, (int, float)):
                        raise ValueError("Open-Meteo response lacks usable timezone information")
                    local_timezone = timezone(timedelta(seconds=int(utc_offset)))
                target_aware = target_time.replace(tzinfo=timezone.utc) if target_time.tzinfo is None else target_time
                target_local = target_aware.astimezone(local_timezone).replace(tzinfo=None)
                forecast_times = [datetime.fromisoformat(value) for value in times]
                match_index = min(range(len(forecast_times)), key=lambda index: abs(forecast_times[index] - target_local))
                if abs(forecast_times[match_index] - target_local) > timedelta(hours=1):
                    raise ValueError("No forecast hour close enough to the class start time")

                temp = float(temperature_values[match_index])
                precip = int(precipitation_values[match_index])
                wind = float(wind_values[match_index])
                code = int(code_values[match_index])
                if not isfinite(temp) or not isfinite(wind) or wind < 0 or not 0 <= precip <= 100 or code < 0:
                    raise ValueError("Open-Meteo returned invalid forecast values")

                result = _evaluate_weather_condition(
                    temperature=temp,
                    precip_prob=precip,
                    wind_speed=wind,
                    weather_code=code,
                )
                _forecast_cache[cache_key] = (now, result)
                return result
            raise ValueError(f"Open-Meteo returned HTTP {response.status_code}")
    except Exception as e:
        logger.warning("Open-Meteo forecast unavailable (%s).", e)

    unavailable = _weather_unavailable()
    _forecast_cache[cache_key] = (now, unavailable)
    return unavailable
