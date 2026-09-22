"""Unified Tirumala Darshan Rush & Waiting Time Predictor.

Integrates Panchangam lunar calculations, multi-state holiday matrices,
and Vaikuntam Queue Complex physical capacity dynamics.
"""

from __future__ import annotations
import calendar
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.panchangam_engine import PanchangamEngine
from src.core.holiday_matrix import HolidayMatrix
from src.core.queue_dynamics import QueueDynamics


class TirumalaRushPredictor:
    """Production predictor for Tirumala Tirupati daily rush and waiting times."""

    def __init__(
        self,
        festivals_path: Optional[Path | str] = None,
        benchmarks_path: Optional[Path | str] = None
    ):
        self.panchangam = PanchangamEngine(festivals_path)
        self.holidays = HolidayMatrix()
        self.queue_dynamics = QueueDynamics(benchmarks_path)

    def predict_date(
        self,
        target_date: date,
        previous_day_demand: Optional[float] = None
    ) -> Dict[str, Any]:
        """Predict rush level, devotee count, and waiting hours for a single day."""
        date_str = target_date.strftime("%Y-%m-%d")
        panch = self.panchangam.evaluate_date(target_date)
        hols = self.holidays.evaluate_date(target_date)

        # Baseline pilgrim demand for a standard non-holiday Tuesday/Wednesday (~54,000 devotees)
        base_demand = 54000.0

        # Day of week factor
        dow_factor = hols["dow_factor"]

        # Religious multiplier
        rel_mult = panch["religious_multiplier"]

        # Academic season multiplier
        acad_mult = hols["academic"]["academic_multiplier"]

        # Holiday multiplier
        holiday_list = hols["holidays"]
        hol_mult = 1.0
        if holiday_list:
            total_states = sum(len(h["states"]) for h in holiday_list)
            hol_mult += min(0.38, 0.09 * total_states)

        # Extended long weekend bonus
        if hols["weekend_info"]["is_extended_weekend"]:
            hol_mult *= 1.25

        # Compute raw arrival demand
        raw_demand = base_demand * dow_factor * rel_mult * acad_mult * hol_mult

        # Spillover estimation from previous day if not explicitly passed
        spillover_in = 0.0
        if previous_day_demand is None:
            # Estimate yesterday's crowd to calculate carryover into today
            prev_date = target_date - timedelta(days=1)
            prev_panch = self.panchangam.evaluate_date(prev_date)
            prev_hols = self.holidays.evaluate_date(prev_date)
            prev_raw = base_demand * prev_hols["dow_factor"] * prev_panch["religious_multiplier"] * prev_hols["academic"]["academic_multiplier"]
            if prev_raw > 85000:
                spillover_in = (prev_raw - 85000) * 0.40
        else:
            if previous_day_demand > 85000:
                spillover_in = (previous_day_demand - 85000) * 0.40

        # Run through physical queue and capacity transfer functions
        has_major_fest = panch["has_major_festival"]
        q_metrics = self.queue_dynamics.compute_queue_metrics(
            raw_pilgrim_demand=raw_demand,
            is_major_festival=has_major_fest,
            spillover_from_previous_day=spillover_in
        )

        # Build human-readable factor breakdown
        factors: List[Dict[str, Any]] = []

        # DOW
        dow_pct = int((dow_factor - 1.0) * 100)
        dow_direction = f"+{dow_pct}%" if dow_pct >= 0 else f"{dow_pct}%"
        factors.append({
            "category": "Day of Week",
            "name": hols["weekday_name"],
            "impact": dow_direction,
            "favorable": dow_pct <= 0,
            "detail": f"{hols['weekday_name']} typical traffic factor"
        })

        # Academic season
        acad_pct = int((acad_mult - 1.0) * 100)
        if acad_pct != 0:
            factors.append({
                "category": "Academic Season",
                "name": hols["academic"]["season_name"],
                "impact": f"+{acad_pct}%" if acad_pct > 0 else f"{acad_pct}%",
                "favorable": acad_pct < 0,
                "detail": hols["academic"]["badge_hint"]
            })

        # Purattasi
        if panch["purattasi"]["is_purattasi_saturday"]:
            factors.append({
                "category": "Auspicious Occasion",
                "name": "Purattasi Saturday",
                "impact": "+35%",
                "favorable": False,
                "detail": "Huge footfall surge from Tamil Nadu devotees trekking on foot"
            })
        elif panch["purattasi"]["is_purattasi_season"]:
            factors.append({
                "category": "Season",
                "name": "Purattasi Masam",
                "impact": "+15%",
                "favorable": False,
                "detail": "Sacred month for Sri Venkateswara"
            })

        # Karthika
        if panch["is_karthika_masam"]:
            factors.append({
                "category": "Season",
                "name": "Karthika Masam",
                "impact": "+12%",
                "favorable": False,
                "detail": "Deepotsavam and Shiva-Vishnu auspicious month"
            })

        # Tithi
        if panch["lunar"]["is_ekadashi"]:
            factors.append({
                "category": "Lunar Tithi",
                "name": panch["lunar"]["tithi_name"],
                "impact": "+20%",
                "favorable": False,
                "detail": "Fasting day with high darshan footfall"
            })
        elif panch["lunar"]["is_pournami"]:
            factors.append({
                "category": "Lunar Tithi",
                "name": "Pournami (Full Moon)",
                "impact": "+18%",
                "favorable": False,
                "detail": "Garuda Seva day around Four Mada Streets"
            })

        # Festivals
        for fest in panch["festivals"]:
            factors.append({
                "category": "Festival / Event",
                "name": fest["name"],
                "impact": f"+{int((fest.get('multiplier', 1.2) - 1.0) * 100)}%",
                "favorable": False,
                "detail": fest.get("description", "")
            })

        # Holidays
        for hol in holiday_list:
            factors.append({
                "category": "Public Holiday",
                "name": hol["name"],
                "impact": "+18% to +30%",
                "favorable": False,
                "detail": f"Gazetted holiday in {', '.join(hol['states'])}"
            })

        if hols["weekend_info"]["is_extended_weekend"]:
            factors.append({
                "category": "Weekend Surge",
                "name": "Extended Long Weekend",
                "impact": "+25%",
                "favorable": False,
                "detail": hols["weekend_info"]["long_weekend_description"] or "3 or 4 day holiday stretch"
            })

        # Eclipse
        if panch["eclipse"]:
            factors.append({
                "category": "Eclipse Closure",
                "name": panch["eclipse"]["name"],
                "impact": "-35% (Closure)",
                "favorable": False,
                "detail": f"Temple closed for {panch['eclipse']['closure_hours']} hours during eclipse"
            })

        # Specialized recommendations
        recommendations = self._generate_recommendations(
            q_metrics["rush_level"],
            hols["weekday_num"],
            q_metrics["sarva_darshan_wait_hours"],
            q_metrics["sed_wait_hours"],
            panch["purattasi"]["is_purattasi_saturday"]
        )

        return {
            "date": date_str,
            "day_name": hols["weekday_name"],
            "weekday_num": hols["weekday_num"],
            "tithi": panch["lunar"]["tithi_name"],
            "moon_illumination": f"{panch['lunar']['illumination_pct']}%",
            "paksha": panch["lunar"]["paksha"],
            "rush_level": q_metrics["rush_level"],
            "rush_label": q_metrics["rush_label"],
            "rush_color": q_metrics["rush_color"],
            "badge_class": q_metrics["badge_class"],
            "estimated_pilgrims": q_metrics["estimated_pilgrims"],
            "sarva_darshan_wait_hours": q_metrics["sarva_darshan_wait_hours"],
            "sarva_darshan_wait_range": q_metrics["sarva_darshan_wait_range"],
            "sed_wait_hours": q_metrics["sed_wait_hours"],
            "sed_wait_range": q_metrics["sed_wait_range"],
            "divya_darshan_wait_hours": q_metrics["divya_darshan_wait_hours"],
            "compartments_filled": q_metrics["compartments_filled"],
            "compartments_note": q_metrics["compartments_note"],
            "advice": q_metrics["advice"],
            "est_hundi_crores": q_metrics["est_hundi_crores"],
            "est_tonsures": q_metrics["est_tonsures"],
            "est_laddus": q_metrics["est_laddus"],
            "factors": factors,
            "recommendations": recommendations,
            "is_weekend": hols["weekend_info"]["is_weekend"],
            "is_long_weekend": hols["weekend_info"]["is_extended_weekend"],
            "is_purattasi_saturday": panch["purattasi"]["is_purattasi_saturday"],
            "is_major_festival": panch["has_major_festival"]
        }

    def predict_month(self, year: int, month: int) -> List[Dict[str, Any]]:
        """Generate day-by-day rush forecasts for an entire calendar month."""
        num_days = calendar.monthrange(year, month)[1]
        days: List[Dict[str, Any]] = []

        last_demand: Optional[float] = None
        for day in range(1, num_days + 1):
            d = date(year, month, day)
            pred = self.predict_date(d, previous_day_demand=last_demand)
            last_demand = float(pred["estimated_pilgrims"])

            # Compact summary for calendar display
            days.append({
                "date": pred["date"],
                "day": day,
                "day_name": pred["day_name"],
                "weekday_num": pred["weekday_num"],
                "rush_level": pred["rush_level"],
                "rush_label": pred["rush_label"],
                "rush_color": pred["rush_color"],
                "badge_class": pred["badge_class"],
                "estimated_pilgrims": pred["estimated_pilgrims"],
                "sarva_darshan_wait_hours": pred["sarva_darshan_wait_hours"],
                "sed_wait_hours": pred["sed_wait_hours"],
                "compartments_filled": pred["compartments_filled"],
                "tithi": pred["tithi"],
                "highlight_event": self._get_highlight_event(pred)
            })

        return days

    def recommend_best_dates(
        self,
        start_date: date,
        end_date: date,
        darshan_type: str = "all",
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Rank and recommend optimal low-crowd darshan dates in a date range."""
        curr = start_date
        all_dates: List[Dict[str, Any]] = []

        last_demand: Optional[float] = None
        while curr <= end_date:
            pred = self.predict_date(curr, previous_day_demand=last_demand)
            last_demand = float(pred["estimated_pilgrims"])

            # Scoring: lower score = better (less waiting, less crowd)
            if darshan_type == "sed":
                score = pred["sed_wait_hours"] * 10.0 + (pred["estimated_pilgrims"] / 10000.0)
            else:
                score = pred["sarva_darshan_wait_hours"] * 3.0 + (pred["estimated_pilgrims"] / 10000.0)

            all_dates.append({
                "date": pred["date"],
                "day_name": pred["day_name"],
                "rush_level": pred["rush_level"],
                "estimated_pilgrims": pred["estimated_pilgrims"],
                "sarva_darshan_wait_hours": pred["sarva_darshan_wait_hours"],
                "sarva_darshan_wait_range": pred["sarva_darshan_wait_range"],
                "sed_wait_hours": pred["sed_wait_hours"],
                "sed_wait_range": pred["sed_wait_range"],
                "compartments_filled": pred["compartments_filled"],
                "tithi": pred["tithi"],
                "advice": pred["advice"],
                "score": score
            })
            curr += timedelta(days=1)

        # Sort ascending by wait score
        all_dates.sort(key=lambda x: x["score"])

        # Calculate time savings compared to worst peak day in the range
        if all_dates:
            worst_sarva = max(d["sarva_darshan_wait_hours"] for d in all_dates)
            for d in all_dates:
                sarva_saved = max(0.0, round(worst_sarva - d["sarva_darshan_wait_hours"], 1))
                d["hours_saved_vs_peak"] = sarva_saved

        return all_dates[:max_results]

    def _get_highlight_event(self, pred: Dict[str, Any]) -> Optional[str]:
        """Get shortest label for calendar cell preview."""
        for f in pred["factors"]:
            if f["category"] in ("Festival / Event", "Auspicious Occasion"):
                return f["name"]
            if f["category"] == "Public Holiday":
                return f["name"]
        if pred["is_long_weekend"]:
            return "Long Weekend"
        return None

    def _generate_recommendations(
        self,
        rush_level: str,
        weekday: int,
        sarva_wait: float,
        sed_wait: float,
        is_purattasi_sat: bool
    ) -> Dict[str, Any]:
        """Produce tactical devotee arrival advice."""
        # Best entry slots
        if rush_level in ("LOW", "MODERATE"):
            best_sarva_entry = "Early Morning (4:00 AM - 6:00 AM) or Late Evening (8:00 PM - 10:00 PM)"
            best_sed_entry = "Midday slots (1:00 PM - 3:00 PM) typically move fastest through Krishna Teja"
        else:
            best_sarva_entry = "Night before token counters open (queue at Bhudevi / Srinivasam before 4:00 AM)"
            best_sed_entry = "Book earliest morning slot (9:00 AM) or after 7:00 PM to avoid peak heat"

        tips = [
            "Free Annaprasadam, buttermilk, and milk for infants are served round-the-clock inside Vaikuntam compartments.",
            "Laddus: Standard quota is 1 free laddu per token; additional laddus available at counters for ₹50 each.",
            "Traditional dress code is mandatory: Dhoti/Kurta for men, Saree/Chudidar with Dupatta for women."
        ]

        if sarva_wait > 16.0:
            tips.append("Long wait alert: If traveling with infants (<1 yr) or elderly (>65 yrs), use Supatham or Senior Citizen quota instead.")

        if is_purattasi_sat:
            tips.append("Purattasi Saturday Warning: Trekking pathways (Alipiri Mettu) will have massive footfall. Start trek before 3:00 AM.")

        return {
            "best_sarva_entry": best_sarva_entry,
            "best_sed_entry": best_sed_entry,
            "travel_tips": tips,
            "cloakroom_tip": "Deposit luggage, mobile phones, and footwear at Tirupati Railway Station or Alipiri to avoid delays in Tirumala lockers."
        }
