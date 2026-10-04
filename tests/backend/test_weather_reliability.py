import unittest
import os
import sys
from datetime import datetime, timezone
from unittest.mock import patch

import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from app.services.weather_service import _forecast_cache, get_outdoor_class_weather


class TestWeatherReliability(unittest.TestCase):
    def setUp(self):
        _forecast_cache.clear()

    def tearDown(self):
        _forecast_cache.clear()

    def _response(self, payload, status_code=200):
        request = httpx.Request("GET", "https://api.open-meteo.com/v1/forecast")
        return httpx.Response(status_code, json=payload, request=request)

    def test_valid_forecast_uses_nearest_hour_in_returned_location_timezone(self):
        target = datetime(2026, 10, 6, 16, 40, tzinfo=timezone.utc)
        payload = {
            "timezone": "America/Los_Angeles",
            "utc_offset_seconds": -25200,
            "hourly": {
                "time": ["2026-10-06T09:00", "2026-10-06T10:00"],
                "temperature_2m": [18.0, 33.0],
                "precipitation_probability": [5, 35],
                "windspeed_10m": [8.0, 12.0],
                "weathercode": [0, 61],
            },
        }
        with patch("httpx.Client.get", return_value=self._response(payload)):
            result = get_outdoor_class_weather(34.05, -118.24, target)

        self.assertEqual(result["temperature"], 33.0)
        self.assertEqual(result["precipitation_probability"], 35)
        self.assertEqual(result["status"], "warning")

    def test_valid_forecast_is_cached(self):
        target = datetime(2026, 10, 6, 16, 0, tzinfo=timezone.utc)
        payload = {
            "timezone": "UTC",
            "utc_offset_seconds": 0,
            "hourly": {
                "time": ["2026-10-06T16:00"],
                "temperature_2m": [22.0],
                "precipitation_probability": [5],
                "windspeed_10m": [9.0],
                "weathercode": [0],
            },
        }
        with patch("httpx.Client.get", return_value=self._response(payload)) as get:
            first = get_outdoor_class_weather(10.0, 20.0, target)
            second = get_outdoor_class_weather(10.0, 20.0, target)

        self.assertEqual(first, second)
        self.assertEqual(get.call_count, 1)

    def test_api_failure_returns_unavailable_not_optimal(self):
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            result = get_outdoor_class_weather(40.0, -70.0, datetime(2026, 10, 8, tzinfo=timezone.utc))

        self.assertEqual(result["status"], "unavailable")
        self.assertIn("Weather unavailable", result["alert_message"])
        self.assertIsNone(result["temperature"])

    def test_invalid_forecast_response_returns_unavailable_not_optimal(self):
        payload = {"timezone": "UTC", "hourly": {"time": ["2026-10-06T16:00"], "temperature_2m": [None]}}
        with patch("httpx.Client.get", return_value=self._response(payload)):
            result = get_outdoor_class_weather(41.0, -71.0, datetime(2026, 10, 6, 16, tzinfo=timezone.utc))

        self.assertEqual(result["status"], "unavailable")
        self.assertNotEqual(result["status"], "optimal")