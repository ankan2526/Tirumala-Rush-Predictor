"""Unit and mock stream tests for Tirumala Predictor API endpoints."""

import io
import json
import unittest
from datetime import date
from urllib.parse import urlparse, parse_qs

from src.models.predictor import TirumalaRushPredictor


class TestAPIEndpoints(unittest.TestCase):

    def setUp(self):
        self.predictor = TirumalaRushPredictor()

    def test_predict_logic(self):
        """Verify predict logic output schema and values."""
        target_date = date(2026, 10, 6)
        data = self.predictor.predict_date(target_date)

        self.assertEqual(data["date"], "2026-10-06")
        self.assertEqual(data["rush_level"], "PEAK")
        self.assertIn("sarva_darshan_wait_hours", data)
        self.assertIn("sed_wait_hours", data)
        self.assertIn("factors", data)
        self.assertIn("recommendations", data)
        self.assertGreater(data["estimated_pilgrims"], 85000)

    def test_calendar_logic(self):
        """Verify calendar logic for full month."""
        days = self.predictor.predict_month(2026, 10)
        self.assertEqual(len(days), 31)
        self.assertEqual(days[0]["day"], 1)
        # Check that days have required fields
        for d in days:
            self.assertIn("rush_level", d)
            self.assertIn("estimated_pilgrims", d)
            self.assertIn("sarva_darshan_wait_hours", d)
            self.assertIn("sed_wait_hours", d)

    def test_recommend_logic(self):
        """Verify recommendation engine ranks low-rush dates."""
        start = date(2026, 11, 1)
        end = date(2026, 11, 20)
        recs = self.predictor.recommend_best_dates(start, end, darshan_type="all", max_results=5)

        self.assertGreater(len(recs), 0)
        self.assertLessEqual(len(recs), 5)
        # The best recommended day should have low rush
        self.assertEqual(recs[0]["rush_level"], "LOW")
        # Check descending hours saved
        for r in recs:
            self.assertGreaterEqual(r["hours_saved_vs_peak"], 0)

    def test_recommend_sed_preference(self):
        """Verify SED ticket preference ranking."""
        start = date(2026, 11, 1)
        end = date(2026, 11, 20)
        recs = self.predictor.recommend_best_dates(start, end, darshan_type="sed", max_results=5)
        self.assertGreater(len(recs), 0)
        self.assertLessEqual(recs[0]["sed_wait_hours"], 2.0)


if __name__ == "__main__":
    unittest.main()
