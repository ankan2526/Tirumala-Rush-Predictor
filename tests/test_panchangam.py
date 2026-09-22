"""Unit tests for Panchangam engine."""

import unittest
from datetime import date
from src.core.panchangam_engine import PanchangamEngine


class TestPanchangamEngine(unittest.TestCase):

    def setUp(self):
        self.engine = PanchangamEngine()

    def test_lunar_state_bounds(self):
        """Test that lunar calculations return valid tithi numbers and phases."""
        test_dates = [
            date(2026, 1, 1),
            date(2026, 6, 15),
            date(2026, 10, 10),
            date(2026, 12, 31)
        ]
        for d in test_dates:
            lunar = self.engine.get_lunar_state(d)
            self.assertGreaterEqual(lunar["tithi_num"], 1)
            self.assertLessEqual(lunar["tithi_num"], 30)
            self.assertIn(lunar["paksha"], ["Shukla", "Krishna"])
            self.assertGreaterEqual(lunar["illumination_pct"], 0.0)
            self.assertLessEqual(lunar["illumination_pct"], 100.0)

    def test_purattasi_saturday_detection(self):
        """Test that Purattasi Saturdays are accurately flagged."""
        # 2026-09-26 is a Saturday during Purattasi season
        sat = date(2026, 9, 26)
        res = self.engine.check_purattasi(sat)
        self.assertTrue(res["is_purattasi_season"])
        self.assertTrue(res["is_purattasi_saturday"])

        # 2026-09-23 is a Wednesday during Purattasi season
        wed = date(2026, 9, 23)
        res_wed = self.engine.check_purattasi(wed)
        self.assertTrue(res_wed["is_purattasi_season"])
        self.assertFalse(res_wed["is_purattasi_saturday"])

        # 2026-05-16 is a Saturday in May (not Purattasi)
        may_sat = date(2026, 5, 16)
        res_may = self.engine.check_purattasi(may_sat)
        self.assertFalse(res_may["is_purattasi_season"])
        self.assertFalse(res_may["is_purattasi_saturday"])

    def test_brahmotsavam_garuda_seva(self):
        """Test detection of flagship Brahmotsavam and Garuda Seva day."""
        # 2026-10-06 is Garuda Seva day for Salakatla Brahmotsavam
        garuda_date = date(2026, 10, 6)
        res = self.engine.evaluate_date(garuda_date)
        self.assertTrue(res["has_major_festival"])
        self.assertGreaterEqual(res["religious_multiplier"], 1.5)
        names = [f["name"] for f in res["festivals"]]
        self.assertTrue(any("Garuda Seva" in n for n in names))

    def test_eclipse_detection(self):
        """Test detection of temple closure during eclipses."""
        eclipse_date = date(2026, 3, 3)
        res = self.engine.evaluate_date(eclipse_date)
        self.assertIsNotNone(res["eclipse"])
        self.assertLess(res["religious_multiplier"], 1.0)  # Reduced darshan hours on closure


if __name__ == "__main__":
    unittest.main()
