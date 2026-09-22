"""Unit tests for Holiday Matrix and Academic Calendar cycles."""

import unittest
from datetime import date
from src.core.holiday_matrix import HolidayMatrix


class TestHolidayMatrix(unittest.TestCase):

    def setUp(self):
        self.matrix = HolidayMatrix()

    def test_republic_day(self):
        """Test fixed national holidays across all states."""
        rep_day = date(2026, 1, 26)
        hols = self.matrix.get_holidays_on_date(rep_day)
        self.assertTrue(len(hols) > 0)
        self.assertEqual(hols[0]["name"], "Republic Day")
        self.assertTrue(hols[0]["is_all_states"])

    def test_academic_exam_season(self):
        """Test lean exam season in February/March."""
        exam_day = date(2026, 3, 10)
        acad = self.matrix.check_academic_season(exam_day)
        self.assertTrue(acad["is_exam_season"])
        self.assertFalse(acad["is_summer_vacation"])
        self.assertLess(acad["academic_multiplier"], 1.0)

    def test_summer_vacation_surge(self):
        """Test high summer vacation period in May."""
        summer_day = date(2026, 5, 20)
        acad = self.matrix.check_academic_season(summer_day)
        self.assertFalse(acad["is_exam_season"])
        self.assertTrue(acad["is_summer_vacation"])
        self.assertGreater(acad["academic_multiplier"], 1.2)

    def test_day_of_week_weights(self):
        """Verify Tuesday/Wednesday are weighted lowest and Saturday is highest."""
        tue = date(2026, 11, 10)  # Tuesday
        sat = date(2026, 11, 14)  # Saturday
        eval_tue = self.matrix.evaluate_date(tue)
        eval_sat = self.matrix.evaluate_date(sat)

        self.assertLess(eval_tue["dow_factor"], 0.95)
        self.assertGreater(eval_sat["dow_factor"], 1.25)


if __name__ == "__main__":
    unittest.main()
