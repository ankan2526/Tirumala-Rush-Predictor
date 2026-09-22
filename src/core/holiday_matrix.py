"""Multi-State Holiday and Academic Vacation Matrix.

Models public/bank holidays across South Indian states (AP, TS, TN, KA)
and academic cycles (Summer vacation surge vs. School exam lean season).
"""

from __future__ import annotations
from datetime import date, timedelta
from typing import Any, Dict, List, Set


class HolidayMatrix:
    """Detects multi-state holidays, extended weekends, and vacation seasons influencing Tirumala."""

    STATES = ["AP", "TS", "TN", "KA"]

    # Fixed annual holidays (month, day, name, list of affected states)
    FIXED_HOLIDAYS = [
        (1, 1, "New Year's Day", ["AP", "TS", "TN", "KA"]),
        (1, 14, "Makara Sankranti / Pongal", ["AP", "TS", "TN", "KA"]),
        (1, 15, "Kanuma / Thiruvalluvar Day", ["AP", "TS", "TN"]),
        (1, 16, "Mukkanuma / Uzhavar Thirunal", ["AP", "TN"]),
        (1, 26, "Republic Day", ["AP", "TS", "TN", "KA"]),
        (4, 14, "Dr. B.R. Ambedkar Jayanti / Tamil New Year", ["AP", "TS", "TN", "KA"]),
        (5, 1, "May Day / Labour Day", ["AP", "TS", "TN", "KA"]),
        (8, 15, "Independence Day", ["AP", "TS", "TN", "KA"]),
        (10, 2, "Gandhi Jayanti", ["AP", "TS", "TN", "KA"]),
        (11, 1, "Kannada Rajyotsava / AP Formation Day", ["KA", "AP"]),
        (12, 25, "Christmas", ["AP", "TS", "TN", "KA"]),
    ]

    # Dynamically dated gazetted holidays per year
    FLOATING_HOLIDAYS = {
        2022: [
            ("2022-03-01", "Maha Shivaratri", ["AP", "TS", "KA"]),
            ("2022-03-18", "Holi", ["AP", "TS"]),
            ("2022-04-02", "Ugadi", ["AP", "TS", "KA"]),
            ("2022-04-15", "Good Friday", ["AP", "TS", "TN", "KA"]),
            ("2022-05-03", "Ramzan / Eid-ul-Fitr", ["AP", "TS", "TN", "KA"]),
            ("2022-07-10", "Bakrid / Eid-ul-Adha", ["AP", "TS", "TN", "KA"]),
            ("2022-08-09", "Muharram", ["AP", "TS", "TN", "KA"]),
            ("2022-08-31", "Vinayaka Chavithi", ["AP", "TS", "TN", "KA"]),
            ("2022-10-04", "Maha Navami / Ayudha Puja", ["AP", "TS", "TN", "KA"]),
            ("2022-10-05", "Vijayadasami / Dussehra", ["AP", "TS", "TN", "KA"]),
            ("2022-10-24", "Deepavali", ["AP", "TS", "TN", "KA"]),
        ],
        2023: [
            ("2023-02-18", "Maha Shivaratri", ["AP", "TS", "KA"]),
            ("2023-03-08", "Holi", ["AP", "TS"]),
            ("2023-03-22", "Ugadi", ["AP", "TS", "KA"]),
            ("2023-04-07", "Good Friday", ["AP", "TS", "TN", "KA"]),
            ("2023-04-22", "Ramzan / Eid-ul-Fitr", ["AP", "TS", "TN", "KA"]),
            ("2023-06-29", "Bakrid", ["AP", "TS", "TN", "KA"]),
            ("2023-07-29", "Muharram", ["AP", "TS", "TN", "KA"]),
            ("2023-09-19", "Ganesh Chaturthi", ["AP", "TS", "TN", "KA"]),
            ("2023-09-28", "Milad-un-Nabi", ["AP", "TS", "TN", "KA"]),
            ("2023-10-23", "Maha Navami / Ayudha Puja", ["AP", "TS", "TN", "KA"]),
            ("2023-10-24", "Vijayadasami / Dussehra", ["AP", "TS", "TN", "KA"]),
            ("2023-11-12", "Deepavali", ["AP", "TS", "TN", "KA"]),
        ],
        2024: [
            ("2024-03-08", "Maha Shivaratri", ["AP", "TS", "KA"]),
            ("2024-03-25", "Holi", ["AP", "TS"]),
            ("2024-03-29", "Good Friday", ["AP", "TS", "TN", "KA"]),
            ("2024-04-09", "Ugadi", ["AP", "TS", "KA"]),
            ("2024-04-11", "Eid-ul-Fitr", ["AP", "TS", "TN", "KA"]),
            ("2024-06-17", "Bakrid", ["AP", "TS", "TN", "KA"]),
            ("2024-07-17", "Muharram", ["AP", "TS", "TN", "KA"]),
            ("2024-09-07", "Vinayaka Chavithi", ["AP", "TS", "TN", "KA"]),
            ("2024-09-16", "Milad-un-Nabi", ["AP", "TS", "TN", "KA"]),
            ("2024-10-11", "Ayudha Puja", ["TN", "KA", "AP"]),
            ("2024-10-12", "Vijayadasami", ["AP", "TS", "TN", "KA"]),
            ("2024-10-31", "Deepavali", ["AP", "TS", "TN", "KA"]),
        ],
        2025: [
            ("2025-02-26", "Maha Shivaratri", ["AP", "TS", "KA"]),
            ("2025-03-14", "Holi", ["AP", "TS"]),
            ("2025-03-30", "Ugadi", ["AP", "TS", "KA"]),
            ("2025-03-31", "Eid-ul-Fitr", ["AP", "TS", "TN", "KA"]),
            ("2025-04-18", "Good Friday", ["AP", "TS", "TN", "KA"]),
            ("2025-06-07", "Bakrid", ["AP", "TS", "TN", "KA"]),
            ("2025-07-06", "Muharram", ["AP", "TS", "TN", "KA"]),
            ("2025-08-27", "Vinayaka Chavithi", ["AP", "TS", "TN", "KA"]),
            ("2025-10-01", "Ayudha Puja", ["TN", "KA", "AP"]),
            ("2025-10-02", "Vijayadasami / Gandhi Jayanti", ["AP", "TS", "TN", "KA"]),
            ("2025-10-20", "Deepavali", ["AP", "TS", "TN", "KA"]),
        ],
        2026: [
            ("2026-02-15", "Maha Shivaratri", ["AP", "TS", "KA"]),
            ("2026-03-04", "Holi", ["AP", "TS"]),
            ("2026-03-19", "Ugadi", ["AP", "TS", "KA"]),
            ("2026-03-20", "Eid-ul-Fitr", ["AP", "TS", "TN", "KA"]),
            ("2026-04-03", "Good Friday", ["AP", "TS", "TN", "KA"]),
            ("2026-05-27", "Bakrid", ["AP", "TS", "TN", "KA"]),
            ("2026-06-25", "Muharram", ["AP", "TS", "TN", "KA"]),
            ("2026-09-14", "Vinayaka Chavithi", ["AP", "TS", "TN", "KA"]),
            ("2026-10-19", "Ayudha Puja", ["TN", "KA", "AP"]),
            ("2026-10-20", "Vijayadasami", ["AP", "TS", "TN", "KA"]),
            ("2026-11-08", "Deepavali", ["AP", "TS", "TN", "KA"]),
        ],
        2027: [
            ("2027-03-06", "Maha Shivaratri", ["AP", "TS", "KA"]),
            ("2027-03-10", "Eid-ul-Fitr", ["AP", "TS", "TN", "KA"]),
            ("2027-03-23", "Holi", ["AP", "TS"]),
            ("2027-03-26", "Good Friday", ["AP", "TS", "TN", "KA"]),
            ("2027-04-07", "Ugadi", ["AP", "TS", "KA"]),
            ("2027-05-17", "Bakrid", ["AP", "TS", "TN", "KA"]),
            ("2027-06-15", "Muharram", ["AP", "TS", "TN", "KA"]),
            ("2027-09-04", "Vinayaka Chavithi", ["AP", "TS", "TN", "KA"]),
            ("2027-10-09", "Ayudha Puja / Dussehra", ["AP", "TS", "TN", "KA"]),
            ("2027-10-29", "Deepavali", ["AP", "TS", "TN", "KA"]),
        ]
    }

    def get_holidays_on_date(self, target_date: date) -> List[Dict[str, Any]]:
        """Return list of gazetted holidays occurring on target_date."""
        holidays: List[Dict[str, Any]] = []
        date_str = target_date.strftime("%Y-%m-%d")

        # Fixed holidays
        for m, d, name, states in self.FIXED_HOLIDAYS:
            if target_date.month == m and target_date.day == d:
                holidays.append({
                    "name": name,
                    "type": "national_or_fixed",
                    "states": states,
                    "is_all_states": (len(states) >= 3)
                })

        # Floating holidays
        year_floaters = self.FLOATING_HOLIDAYS.get(target_date.year, [])
        for fdate, fname, fstates in year_floaters:
            if fdate == date_str:
                holidays.append({
                    "name": fname,
                    "type": "religious_or_regional",
                    "states": fstates,
                    "is_all_states": (len(fstates) >= 3)
                })

        return holidays

    def is_public_holiday(self, target_date: date) -> bool:
        """True if any major multi-state holiday exists on target_date."""
        return len(self.get_holidays_on_date(target_date)) > 0

    def check_long_weekend(self, target_date: date) -> Dict[str, Any]:
        """Detect whether target_date is part of a 3-day or 4-day extended holiday weekend."""
        weekday = target_date.weekday()  # 0=Mon, 4=Fri, 5=Sat, 6=Sun
        is_weekend = (weekday in (5, 6))

        # Check surrounding Friday and Monday
        friday = target_date + timedelta(days=(4 - weekday)) if weekday in (5, 6) else (target_date if weekday == 4 else None)
        monday = target_date + timedelta(days=(7 - weekday)) if weekday in (5, 6) else (target_date if weekday == 0 else None)

        fri_holiday = self.is_public_holiday(friday) if friday else False
        mon_holiday = self.is_public_holiday(monday) if monday else False

        is_long_weekend = False
        description = None

        if weekday == 4 and self.is_public_holiday(target_date):
            is_long_weekend = True
            description = "Friday Holiday (3-day weekend starts)"
        elif weekday == 0 and self.is_public_holiday(target_date):
            is_long_weekend = True
            description = "Monday Holiday (Extended weekend continues)"
        elif is_weekend:
            if fri_holiday and mon_holiday:
                is_long_weekend = True
                description = "4-Day Super Long Weekend (Friday & Monday both holidays)"
            elif fri_holiday:
                is_long_weekend = True
                description = "3-Day Long Weekend (Friday was a holiday)"
            elif mon_holiday:
                is_long_weekend = True
                description = "3-Day Long Weekend (Monday is a holiday)"

        return {
            "is_weekend": is_weekend,
            "is_extended_weekend": is_long_weekend,
            "long_weekend_description": description
        }

    def check_academic_season(self, target_date: date) -> Dict[str, Any]:
        """Classify academic calendar period (Exam lean period vs Summer rush vs Festival breaks)."""
        m = target_date.month
        d = target_date.day

        # 1. School Exam Season: Feb 15 - April 10 (LEANEST PERIOD OF THE YEAR)
        is_exam_season = (m == 2 and d >= 15) or (m == 3) or (m == 4 and d <= 10)

        # 2. Summer Vacation: April 15 - June 10 (PEAK SUSTAINED SUMMER SURGE)
        is_summer_vacation = (m == 4 and d >= 15) or (m == 5) or (m == 6 and d <= 10)

        # 3. Dussehra School Holidays: typically first half of October
        is_dussehra_vacation = (m == 10 and 1 <= d <= 18)

        # 4. Sankranti Holidays: mid January
        is_sankranti_vacation = (m == 1 and 10 <= d <= 19)

        season_name = "Normal Academic Term"
        crowd_impact = 1.0
        badge_hint = "Regular"

        if is_exam_season:
            season_name = "School / Board Exam Season"
            crowd_impact = 0.78  # Devotees with kids delay trips; queues are notably shorter
            badge_hint = "Low Rush Window"
        elif is_summer_vacation:
            season_name = "Summer School Vacation"
            crowd_impact = 1.35  # Sustained family pilgrimage rush across all days
            badge_hint = "High Summer Surge"
        elif is_dussehra_vacation:
            season_name = "Dussehra School Holidays"
            crowd_impact = 1.25
            badge_hint = "Festival Vacation"
        elif is_sankranti_vacation:
            season_name = "Sankranti Holidays"
            crowd_impact = 1.30
            badge_hint = "Holiday Rush"

        return {
            "season_name": season_name,
            "is_exam_season": is_exam_season,
            "is_summer_vacation": is_summer_vacation,
            "is_school_holiday": (is_summer_vacation or is_dussehra_vacation or is_sankranti_vacation),
            "academic_multiplier": crowd_impact,
            "badge_hint": badge_hint
        }

    def evaluate_date(self, target_date: date) -> Dict[str, Any]:
        """Comprehensive holiday and calendar matrix evaluation."""
        holidays = self.get_holidays_on_date(target_date)
        weekend_info = self.check_long_weekend(target_date)
        academic = self.check_academic_season(target_date)

        # Day of week multiplier
        weekday = target_date.weekday()
        # Monday=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6
        weekday_weights = {
            0: 0.98,  # Monday (return rush / moderate)
            1: 0.88,  # Tuesday (lowest crowd day of week)
            2: 0.86,  # Wednesday (lowest crowd day of week)
            3: 0.90,  # Thursday (pre-weekend buildup)
            4: 1.15,  # Friday (Friday weekend start / Thiruvenkatam)
            5: 1.32,  # Saturday (absolute peak day of week)
            6: 1.25   # Sunday (high weekend crowd)
        }
        dow_factor = weekday_weights[weekday]

        # Holiday multiplier
        holiday_multiplier = 1.0
        reasons: List[str] = []

        if holidays:
            # More states affected = bigger surge
            total_states = sum(len(h["states"]) for h in holidays)
            holiday_multiplier += min(0.35, 0.08 * total_states)
            for h in holidays:
                reasons.append(f"Public Holiday: {h['name']}")

        if weekend_info["is_extended_weekend"]:
            holiday_multiplier *= 1.25
            if weekend_info["long_weekend_description"]:
                reasons.append(weekend_info["long_weekend_description"])

        combined_calendar_mult = dow_factor * holiday_multiplier * academic["academic_multiplier"]

        return {
            "date": target_date.strftime("%Y-%m-%d"),
            "weekday_num": weekday,
            "weekday_name": target_date.strftime("%A"),
            "dow_factor": dow_factor,
            "holidays": holidays,
            "is_public_holiday": len(holidays) > 0,
            "weekend_info": weekend_info,
            "academic": academic,
            "combined_calendar_multiplier": round(combined_calendar_mult, 3),
            "calendar_reasons": reasons
        }
