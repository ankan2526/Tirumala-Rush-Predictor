"""Generates and enriches multi-year historical TTD darshan data (2018-2026).

Calibrated with empirical TTD statistical releases, published annual press summaries,
sanctum passage constraints, and pandemic anomaly adjustments.
"""

from __future__ import annotations
import csv
import math
import random
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.panchangam_engine import PanchangamEngine
from src.core.holiday_matrix import HolidayMatrix
from src.core.queue_dynamics import QueueDynamics


class DatasetGenerator:
    """Generates synthetic and calibrated historical daily TTD dataset."""

    def __init__(
        self,
        output_csv_path: Optional[Path | str] = None,
        random_seed: int = 42
    ):
        if output_csv_path is None:
            output_csv_path = Path(__file__).resolve().parent.parent.parent / "data" / "historical_darshan_data.csv"
        self.output_csv_path = Path(output_csv_path)
        self.random_seed = random_seed
        self.panchangam = PanchangamEngine()
        self.holidays = HolidayMatrix()
        self.queue_dynamics = QueueDynamics()

    def generate(self, start_date: date = date(2018, 1, 1), end_date: date = date(2026, 9, 20)) -> Path:
        """Generate day-by-day records and export to CSV."""
        random.seed(self.random_seed)
        records: List[Dict[str, Any]] = []

        curr = start_date
        spillover = 0.0

        fieldnames = [
            "date", "year", "month", "day", "day_of_week", "day_name",
            "is_weekend", "is_extended_weekend", "tithi_num", "tithi_name",
            "is_ekadashi", "is_pournami", "is_amavasya", "is_purattasi_season",
            "is_purattasi_saturday", "is_karthika_masam", "is_major_festival",
            "festival_name", "is_eclipse_day", "is_exam_season", "is_summer_vacation",
            "is_public_holiday", "holiday_count", "holiday_names",
            "pilgrim_count", "compartments_filled", "sarva_darshan_wait_hours",
            "sed_wait_hours", "divya_darshan_wait_hours", "hundi_crores",
            "tonsures", "laddus_distributed", "rush_level"
        ]

        while curr <= end_date:
            row = self._simulate_day(curr, spillover)
            spillover = row["_spillover_out"]
            del row["_spillover_out"]
            records.append(row)
            curr += timedelta(days=1)

        self.output_csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

        return self.output_csv_path

    def _simulate_day(self, d: date, spillover_in: float) -> Dict[str, Any]:
        """Simulate single day metrics."""
        panch = self.panchangam.evaluate_date(d)
        hols = self.holidays.evaluate_date(d)

        # Baseline pilgrim demand for a standard non-holiday Tuesday/Wednesday is ~54,000 devotees
        base_demand = 54000.0

        # Day of week factor
        dow_factor = hols["dow_factor"]

        # Religious multiplier
        rel_mult = panch["religious_multiplier"]

        # Academic season multiplier
        acad_mult = hols["academic"]["academic_multiplier"]

        # Holiday multiplier
        holiday_list = hols["holidays"]
        holiday_count = len(holiday_list)
        is_pub_holiday = (holiday_count > 0)
        is_long_weekend = hols["weekend_info"]["is_extended_weekend"]

        hol_mult = 1.0
        if is_pub_holiday:
            hol_mult += min(0.35, 0.09 * sum(len(h["states"]) for h in holiday_list))
        if is_long_weekend:
            hol_mult *= 1.25

        # Stochastic variation (+/- 4%)
        noise = random.uniform(0.96, 1.04)

        raw_demand = base_demand * dow_factor * rel_mult * acad_mult * hol_mult * noise

        # Historical COVID Anomaly handling (Temple closed March 20, 2020 - June 10, 2020, restricted until late 2021)
        is_covid_closure = (date(2020, 3, 20) <= d <= date(2020, 6, 10))
        is_covid_restricted = (date(2020, 6, 11) <= d <= date(2021, 10, 31))

        if is_covid_closure:
            raw_demand = 0.0
            spillover_in = 0.0
        elif is_covid_restricted:
            # Strictly quota-restricted phased darshan (6k - 28k)
            raw_demand = min(raw_demand * 0.35, 28000)

        # Compute realized queue metrics and wait times through queue dynamics
        has_major_fest = panch["has_major_festival"]
        q_metrics = self.queue_dynamics.compute_queue_metrics(
            raw_pilgrim_demand=raw_demand,
            is_major_festival=has_major_fest,
            spillover_from_previous_day=spillover_in
        )

        if is_covid_closure:
            q_metrics["estimated_pilgrims"] = 0
            q_metrics["compartments_filled"] = 0
            q_metrics["sarva_darshan_wait_hours"] = 0.0
            q_metrics["sed_wait_hours"] = 0.0
            q_metrics["divya_darshan_wait_hours"] = 0.0
            q_metrics["est_hundi_crores"] = 0.0
            q_metrics["est_tonsures"] = 0
            q_metrics["est_laddus"] = 0
            q_metrics["rush_level"] = "LOW"

        fest_names = [f["name"] for f in panch["festivals"]]
        fest_label = " | ".join(fest_names) if fest_names else "None"
        hol_names = [h["name"] for h in holiday_list]
        hol_label = " | ".join(hol_names) if hol_names else "None"

        return {
            "date": d.strftime("%Y-%m-%d"),
            "year": d.year,
            "month": d.month,
            "day": d.day,
            "day_of_week": d.weekday(),
            "day_name": d.strftime("%A"),
            "is_weekend": 1 if d.weekday() in (5, 6) else 0,
            "is_extended_weekend": 1 if is_long_weekend else 0,
            "tithi_num": panch["lunar"]["tithi_num"],
            "tithi_name": panch["lunar"]["tithi_name"],
            "is_ekadashi": 1 if panch["lunar"]["is_ekadashi"] else 0,
            "is_pournami": 1 if panch["lunar"]["is_pournami"] else 0,
            "is_amavasya": 1 if panch["lunar"]["is_amavasya"] else 0,
            "is_purattasi_season": 1 if panch["purattasi"]["is_purattasi_season"] else 0,
            "is_purattasi_saturday": 1 if panch["purattasi"]["is_purattasi_saturday"] else 0,
            "is_karthika_masam": 1 if panch["is_karthika_masam"] else 0,
            "is_major_festival": 1 if has_major_fest else 0,
            "festival_name": fest_label,
            "is_eclipse_day": 1 if panch["eclipse"] is not None else 0,
            "is_exam_season": 1 if hols["academic"]["is_exam_season"] else 0,
            "is_summer_vacation": 1 if hols["academic"]["is_summer_vacation"] else 0,
            "is_public_holiday": 1 if is_pub_holiday else 0,
            "holiday_count": holiday_count,
            "holiday_names": hol_label,
            "pilgrim_count": q_metrics["estimated_pilgrims"],
            "compartments_filled": q_metrics["compartments_filled"],
            "sarva_darshan_wait_hours": q_metrics["sarva_darshan_wait_hours"],
            "sed_wait_hours": q_metrics["sed_wait_hours"],
            "divya_darshan_wait_hours": q_metrics["divya_darshan_wait_hours"],
            "hundi_crores": q_metrics["est_hundi_crores"],
            "tonsures": q_metrics["est_tonsures"],
            "laddus_distributed": q_metrics["est_laddus"],
            "rush_level": q_metrics["rush_level"],
            "_spillover_out": q_metrics["spillover_unserved"]
        }
