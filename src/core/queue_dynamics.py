"""Queue Dynamics and Waiting Time Physics for Vaikuntam Queue Complex (VKC 1 & 2).

Translates pilgrim arrival pressure into:
- Realized Daily Darshan Count (clamped to physical temple passage capacity)
- Vaikuntam Compartment Occupancy (0 to 31+ compartments)
- Sarva Darshan (Free/SSD) Waiting Time in Hours (4 hrs to 36+ hrs)
- Special Entry Darshan (SED Rs 300) Waiting Time in Hours (1.5 hrs to 7+ hrs)
- Divya Darshan (Pedestrian Trekking) Waiting Time
- Multi-day Queue Spillover (e.g. Saturday night overflow impacting Sunday)
"""

from __future__ import annotations
import json
import math
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


class QueueDynamics:
    """Models physical devotee throughput, queue compartment accumulation, and waiting times."""

    def __init__(self, benchmarks_path: Optional[Path | str] = None):
        if benchmarks_path is None:
            benchmarks_path = Path(__file__).resolve().parent.parent.parent / "data" / "ttd_benchmarks.json"
        self.benchmarks_path = Path(benchmarks_path)
        self.benchmarks = self._load_benchmarks()

    def _load_benchmarks(self) -> Dict[str, Any]:
        if self.benchmarks_path.exists():
            with open(self.benchmarks_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "throughput": {
                "sanctum_hourly_capacity": 3800,
                "sanctum_operational_hours_normal": 21,
                "sanctum_operational_hours_festival": 22.5,
                "max_daily_sanctum_capacity": 85000,
                "absolute_surge_limit": 98000
            },
            "compartments": {
                "vkc1_compartments": 18,
                "vkc2_compartments": 31,
                "total_compartments": 49,
                "average_pilgrims_per_compartment": 1800
            }
        }

    def compute_queue_metrics(
        self,
        raw_pilgrim_demand: float,
        is_major_festival: bool = False,
        spillover_from_previous_day: float = 0.0
    ) -> Dict[str, Any]:
        """Compute realized darshan count, compartments filled, and waiting times.

        Parameters
        ----------
        raw_pilgrim_demand : float
            Estimated total devotees attempting or arriving for darshan.
        is_major_festival : bool
            If true, TTD cancels VIP break darshan and extends general darshan hours.
        spillover_from_previous_day : float
            Devotees already queued in compartments from previous day's surge.
        """
        throughput = self.benchmarks["throughput"]
        comp_cfg = self.benchmarks["compartments"]

        op_hours = throughput["sanctum_operational_hours_festival"] if is_major_festival else throughput["sanctum_operational_hours_normal"]
        hourly_rate = throughput["sanctum_hourly_capacity"]
        max_daily_capacity = int(op_hours * hourly_rate)
        absolute_limit = throughput["absolute_surge_limit"]

        # Total load facing the temple today
        total_load = raw_pilgrim_demand + spillover_from_previous_day

        # Actual pilgrims who complete darshan today is bounded by sanctum passage limit
        if total_load <= max_daily_capacity:
            realized_pilgrims = int(total_load)
            unserved_spillover = 0.0
        else:
            # Under extreme crowd pressure, TTD accelerates line speed ("Jaya Vijaya" pushes),
            # approaching absolute surge limit
            excess = total_load - max_daily_capacity
            surge_absorption = min(excess * 0.45, absolute_limit - max_daily_capacity)
            realized_pilgrims = int(max_daily_capacity + surge_absorption)
            unserved_spillover = max(0.0, total_load - realized_pilgrims)

        # Ensure realistic baseline floor (even quietest days rarely fall below 48,000)
        realized_pilgrims = max(48000, realized_pilgrims)

        # -------------------------------------------------------------
        # 1. Compartments Filled Modeling (VKC 2 has 31 compartments)
        # -------------------------------------------------------------
        # Low rush (<60k): 2 to 10 compartments
        # Moderate (60k-72k): 10 to 20 compartments
        # High (72k-84k): 20 to 30 compartments
        # Peak (>84k): 31 compartments (all full, spillover to Narayanagiri sheds)
        if realized_pilgrims < 58000:
            compartments_filled = int(2 + (realized_pilgrims - 48000) / (58000 - 48000) * 8)
        elif realized_pilgrims < 72000:
            compartments_filled = int(10 + (realized_pilgrims - 58000) / (72000 - 58000) * 10)
        elif realized_pilgrims < 84000:
            compartments_filled = int(20 + (realized_pilgrims - 72000) / (84000 - 72000) * 10)
        else:
            compartments_filled = 31  # Saturated; queue extends outside

        compartments_note = (
            f"{compartments_filled} compartments occupied inside Vaikuntam Queue Complex."
            if compartments_filled < 31
            else "All 31 Vaikuntam compartments full; queue extending outside into Narayanagiri Gardens shed!"
        )

        # -------------------------------------------------------------
        # 2. Sarva Darshan (Free) Waiting Time (Non-linear hockey stick)
        # -------------------------------------------------------------
        # Base walking & transit time: ~4 hours minimum
        # Scales steeply once compartments exceed 15
        if realized_pilgrims <= 58000:
            sarva_hours = 4.0 + (realized_pilgrims - 48000) / 10000.0 * 3.5
        elif realized_pilgrims <= 72000:
            sarva_hours = 7.5 + (realized_pilgrims - 58000) / 14000.0 * 6.5
        elif realized_pilgrims <= 84000:
            sarva_hours = 14.0 + (realized_pilgrims - 72000) / 12000.0 * 8.0
        else:
            # Peak surge non-linear queue explosion
            sarva_hours = 22.0 + (min(realized_pilgrims, absolute_limit) - 84000) / 14000.0 * 14.0

        sarva_wait_hours = round(min(38.0, max(4.0, sarva_hours)), 1)

        # -------------------------------------------------------------
        # 3. Special Entry Darshan (SED Rs 300 quota) Waiting Time
        # -------------------------------------------------------------
        # SED bypasses primary VKC compartments, entering via Krishna Teja corridor.
        # But sanctum merge point causes backups during peak crowd.
        # Typical: 1.5 - 2.5 hrs on calm days, 3 - 4.5 hrs on weekends, 5 - 7 hrs on mega festivals.
        if realized_pilgrims <= 60000:
            sed_hours = 1.5 + (realized_pilgrims - 48000) / 12000.0 * 0.8
        elif realized_pilgrims <= 75000:
            sed_hours = 2.3 + (realized_pilgrims - 60000) / 15000.0 * 1.5
        elif realized_pilgrims <= 85000:
            sed_hours = 3.8 + (realized_pilgrims - 75000) / 10000.0 * 1.7
        else:
            sed_hours = 5.5 + (min(realized_pilgrims, absolute_limit) - 85000) / 13000.0 * 1.8

        sed_wait_hours = round(min(7.5, max(1.5, sed_hours)), 1)

        # -------------------------------------------------------------
        # 4. Divya Darshan (Pedestrian Trekking via Alipiri/Srivari Mettu)
        # -------------------------------------------------------------
        # Divya darshan tokens get priority over normal Sarva Darshan but behind SED.
        divya_wait_hours = round(max(3.5, sarva_wait_hours * 0.55), 1)

        # -------------------------------------------------------------
        # 5. Rush Classification & Color Coding
        # -------------------------------------------------------------
        if realized_pilgrims < 62000:
            rush_level = "LOW"
            rush_label = "Low Rush / Peaceful Darshanam"
            rush_color = "#10b981"  # Emerald Green
            badge_class = "badge-low"
            advice = "Excellent time to visit. Short waiting times; minimal delay in compartments."
        elif realized_pilgrims < 73000:
            rush_level = "MODERATE"
            rush_label = "Moderate / Regular Crowd"
            rush_color = "#f59e0b"  # Amber/Yellow
            badge_class = "badge-moderate"
            advice = "Normal operational day. Ensure timely arrival at ticket/token verification points."
        elif realized_pilgrims < 84000:
            rush_level = "HIGH"
            rush_label = "High Rush / Heavy Devotee Influx"
            rush_color = "#f97316"  # Orange
            badge_class = "badge-high"
            advice = "High rush. Carry water, biscuits for children/elderly. SED Rs 300 recommended over Sarva Darshan."
        else:
            rush_level = "PEAK"
            rush_label = "Peak Rush / Extreme Festive Surge"
            rush_color = "#ef4444"  # Red
            badge_class = "badge-peak"
            advice = "Extreme crowd warning! Sarva Darshan wait can exceed 24-30 hours. Avoid visiting with infants/infirm unless mandatory."

        # Secondary indicators estimated based on empirical TTD correlations
        # Hundi: typically Rs 3.0 to 4.8 Crores daily
        est_hundi_crores = round(2.8 + (realized_pilgrims / 100000.0) * 1.9, 2)
        # Tonsures: typically 35% to 45% of total pilgrims
        est_tonsures = int(realized_pilgrims * 0.40)
        # Laddus distributed: ~4 to 5 laddus per pilgrim average
        est_laddus = int(realized_pilgrims * 4.4)

        return {
            "estimated_pilgrims": realized_pilgrims,
            "raw_demand": int(raw_pilgrim_demand),
            "spillover_unserved": int(unserved_spillover),
            "rush_level": rush_level,
            "rush_label": rush_label,
            "rush_color": rush_color,
            "badge_class": badge_class,
            "sarva_darshan_wait_hours": sarva_wait_hours,
            "sarva_darshan_wait_range": f"{int(sarva_wait_hours - 1.5)}-{int(sarva_wait_hours + 2.0)} hrs" if sarva_wait_hours > 6 else f"{int(sarva_wait_hours - 1)}-{int(sarva_wait_hours + 1.5)} hrs",
            "sed_wait_hours": sed_wait_hours,
            "sed_wait_range": f"{round(sed_wait_hours - 0.5, 1)}-{round(sed_wait_hours + 0.8, 1)} hrs",
            "divya_darshan_wait_hours": divya_wait_hours,
            "compartments_filled": compartments_filled,
            "compartments_note": compartments_note,
            "advice": advice,
            "est_hundi_crores": est_hundi_crores,
            "est_tonsures": est_tonsures,
            "est_laddus": est_laddus
        }
