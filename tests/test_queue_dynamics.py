"""Unit tests for Queue Dynamics and Vaikuntam Compartment calculations."""

import unittest
from src.core.queue_dynamics import QueueDynamics


class TestQueueDynamics(unittest.TestCase):

    def setUp(self):
        self.qd = QueueDynamics()

    def test_low_demand_metrics(self):
        """Test queue metrics for low demand (e.g. 50,000 pilgrims)."""
        res = self.qd.compute_queue_metrics(raw_pilgrim_demand=50000)
        self.assertEqual(res["rush_level"], "LOW")
        self.assertLessEqual(res["sarva_darshan_wait_hours"], 8.0)
        self.assertLessEqual(res["sed_wait_hours"], 2.5)
        self.assertLessEqual(res["compartments_filled"], 10)

    def test_peak_demand_capacity_clamping(self):
        """Test that excessive demand does not exceed sanctum physical bounds and produces spillover."""
        # 110,000 arriving pilgrims
        res = self.qd.compute_queue_metrics(raw_pilgrim_demand=110000, is_major_festival=True)
        self.assertEqual(res["rush_level"], "PEAK")
        # Realized pilgrims should be capped near absolute limit (~98,000)
        self.assertLessEqual(res["estimated_pilgrims"], 98000)
        self.assertGreater(res["spillover_unserved"], 0)
        self.assertEqual(res["compartments_filled"], 31)
        self.assertGreaterEqual(res["sarva_darshan_wait_hours"], 24.0)

    def test_sed_vs_sarva_relationship(self):
        """Special Entry Darshan (₹300) should always have significantly lower waiting time than Sarva Darshan."""
        for demand in [55000, 70000, 85000, 95000]:
            res = self.qd.compute_queue_metrics(raw_pilgrim_demand=demand)
            self.assertLess(res["sed_wait_hours"], res["sarva_darshan_wait_hours"])


if __name__ == "__main__":
    unittest.main()
