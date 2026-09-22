"""Panchangam (Hindu Lunar Calendar) and Festival Engine for Tirumala Tirupati Devasthanams.

Accurately detects:
- Lunar Tithis (Ekadashi, Pournami, Amavasya, Dwadasi)
- Tamil Purattasi Masam & Purattasi Saturdays (major surge catalyst)
- Karthika Masam (auspicious Deepotsavam month)
- Annual Brahmotsavams (Salakatla & Navaratri) and Garuda Seva day
- Vaikunta Dwara Darshanam (10-day peak gateway opening)
- Rathasapthami (One-day 7 vahanams mini-Brahmotsavam)
- Solar & Lunar Eclipses with sanctum closure impact
"""

from __future__ import annotations
import json
import math
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class PanchangamEngine:
    """Calculates lunar tithis and correlates dates with Tirumala temple religious calendar."""

    # Reference New Moon (Amavasya): 2000-01-06 18:14 UTC
    REF_NEW_MOON = datetime(2000, 1, 6, 18, 14)
    SYNODIC_MONTH = 29.53058867  # Mean synodic lunar month in days

    TITHI_NAMES = [
        "Pratipada (Shukla)", "Dwitiya (Shukla)", "Tritiya (Shukla)", "Chaturthi (Shukla)",
        "Panchami (Shukla)", "Shasthi (Shukla)", "Saptami (Shukla)", "Ashtami (Shukla)",
        "Navami (Shukla)", "Dashami (Shukla)", "Ekadashi (Shukla)", "Dwadashi (Shukla)",
        "Trayodashi (Shukla)", "Chaturdashi (Shukla)", "Pournami (Full Moon)",
        "Pratipada (Krishna)", "Dwitiya (Krishna)", "Tritiya (Krishna)", "Chaturthi (Krishna)",
        "Panchami (Krishna)", "Shasthi (Krishna)", "Saptami (Krishna)", "Ashtami (Krishna)",
        "Navami (Krishna)", "Dashami (Krishna)", "Ekadashi (Krishna)", "Dwadashi (Krishna)",
        "Trayodashi (Krishna)", "Chaturdashi (Krishna)", "Amavasya (New Moon)"
    ]

    def __init__(self, calendar_path: Optional[Path | str] = None):
        if calendar_path is None:
            calendar_path = Path(__file__).resolve().parent.parent.parent / "data" / "festivals_calendar.json"
        self.calendar_path = Path(calendar_path)
        self.calendar_data: Dict[str, Any] = {}
        self._load_calendar()

    def _load_calendar(self) -> None:
        if self.calendar_path.exists():
            with open(self.calendar_path, "r", encoding="utf-8") as f:
                self.calendar_data = json.load(f)
        else:
            self.calendar_data = {"festivals": [], "purattasi_season": [], "karthika_masam": [], "eclipses": []}

    def get_lunar_state(self, target_date: date) -> Dict[str, Any]:
        """Compute the lunar age, phase fraction, tithi number (1-30), and tithi name."""
        dt = datetime(target_date.year, target_date.month, target_date.day, 12, 0)
        delta_days = (dt - self.REF_NEW_MOON).total_seconds() / 86400.0
        lunar_age = delta_days % self.SYNODIC_MONTH

        # Phase fraction: 0.0 = New Moon, 0.5 = Full Moon, 1.0 = New Moon
        phase = (lunar_age / self.SYNODIC_MONTH)
        tithi_num = int(math.floor(phase * 30)) + 1
        tithi_num = max(1, min(30, tithi_num))

        tithi_name = self.TITHI_NAMES[tithi_num - 1]
        is_ekadashi = (tithi_num == 11 or tithi_num == 26)
        is_dwadashi = (tithi_num == 12 or tithi_num == 27)
        is_pournami = (tithi_num == 15)
        is_amavasya = (tithi_num == 30)

        # Moon illumination percentage
        illumination = 0.5 * (1.0 - math.cos(2 * math.pi * phase))

        return {
            "lunar_age_days": round(lunar_age, 2),
            "phase_fraction": round(phase, 4),
            "illumination_pct": round(illumination * 100, 1),
            "tithi_num": tithi_num,
            "tithi_name": tithi_name,
            "paksha": "Shukla" if tithi_num <= 15 else "Krishna",
            "is_ekadashi": is_ekadashi,
            "is_dwadashi": is_dwadashi,
            "is_pournami": is_pournami,
            "is_amavasya": is_amavasya,
        }

    def check_purattasi(self, target_date: date) -> Dict[str, Any]:
        """Check if target date falls in Tamil Purattasi Masam (mid-Sep to mid-Oct).

        Purattasi Saturdays are considered extraordinarily sacred to Lord Venkateswara by
        millions of devotees from Tamil Nadu who travel or trek by foot.
        """
        date_str = target_date.strftime("%Y-%m-%d")
        year = target_date.year

        in_purattasi = False
        for season in self.calendar_data.get("purattasi_season", []):
            if season.get("year") == year:
                if season.get("start") <= date_str <= season.get("end"):
                    in_purattasi = True
                    break

        # Fallback heuristic if not explicitly registered in json
        if not in_purattasi and (target_date.month == 9 and target_date.day >= 17) or (target_date.month == 10 and target_date.day <= 17):
            in_purattasi = True

        # Weekday 5 = Saturday in Python (0=Mon, 6=Sun)
        is_saturday = (target_date.weekday() == 5)
        is_purattasi_saturday = in_purattasi and is_saturday

        return {
            "is_purattasi_season": in_purattasi,
            "is_purattasi_saturday": is_purattasi_saturday,
            "purattasi_note": "Auspicious Purattasi Saturday: Expect massive surge of devotees from Tamil Nadu."
            if is_purattasi_saturday else None
        }

    def check_karthika_masam(self, target_date: date) -> bool:
        """Check if target date falls in auspicious Karthika Masam."""
        date_str = target_date.strftime("%Y-%m-%d")
        year = target_date.year
        for season in self.calendar_data.get("karthika_masam", []):
            if season.get("year") == year:
                if season.get("start") <= date_str <= season.get("end"):
                    return True

        # Fallback window: Nov 5 - Dec 5
        if (target_date.month == 11 and target_date.day >= 5) or (target_date.month == 12 and target_date.day <= 5):
            return True
        return False

    def check_festivals_and_events(self, target_date: date) -> List[Dict[str, Any]]:
        """Match date against curated temple festivals, Brahmotsavam, and special events."""
        date_str = target_date.strftime("%Y-%m-%d")
        events: List[Dict[str, Any]] = []

        for fest in self.calendar_data.get("festivals", []):
            name = fest["name"]
            ftype = fest.get("type")

            # 1. Fixed solar (e.g. English New Year Jan 1)
            if ftype == "fixed_solar":
                if target_date.month == fest.get("month") and target_date.day == fest.get("day"):
                    events.append({
                        "name": name,
                        "type": "fixed",
                        "multiplier": fest.get("crowd_multiplier", 1.3),
                        "description": fest.get("description", ""),
                        "is_peak_surge": True
                    })

            # 2. Multi-day or single explicit dates list
            elif ftype in ("multi_day", "annual_auspicious", "lunar_festival"):
                if date_str in fest.get("dates", []):
                    events.append({
                        "name": name,
                        "type": ftype,
                        "multiplier": fest.get("crowd_multiplier", 1.3),
                        "description": fest.get("description", ""),
                        "is_peak_surge": (fest.get("crowd_multiplier", 1.0) >= 1.4)
                    })

            # 3. Major windows (Brahmotsavam, Vaikunta Dwara)
            elif ftype == "major_festival_window":
                for r in fest.get("ranges", []):
                    start = r.get("start", "")
                    end = r.get("end", "")
                    if start <= date_str <= end:
                        is_garuda_seva = (date_str == r.get("garuda_seva"))
                        is_peak_day = (date_str == r.get("peak_day"))

                        mult = fest.get("crowd_multiplier", 1.4)
                        if is_garuda_seva:
                            mult = fest.get("garuda_seva_multiplier", 1.7)
                            event_label = f"{name} (Garuda Seva Day!)"
                        elif is_peak_day:
                            mult = fest.get("peak_day_multiplier", 1.75)
                            event_label = f"{name} (Opening Day / Peak!)"
                        else:
                            event_label = f"{name} (Day in Festival Window)"

                        events.append({
                            "name": event_label,
                            "base_festival": name,
                            "type": "window_day",
                            "multiplier": mult,
                            "is_garuda_seva": is_garuda_seva,
                            "is_peak_day": is_peak_day,
                            "description": fest.get("description", ""),
                            "is_peak_surge": True
                        })

        return events

    def check_eclipses(self, target_date: date) -> Optional[Dict[str, Any]]:
        """Check for solar or lunar eclipse requiring temple sanctum closure."""
        date_str = target_date.strftime("%Y-%m-%d")
        for ecl in self.calendar_data.get("eclipses", []):
            if ecl.get("date") == date_str:
                return ecl
        return None

    def evaluate_date(self, target_date: date) -> Dict[str, Any]:
        """Perform comprehensive panchangam and religious event evaluation for a date."""
        lunar = self.get_lunar_state(target_date)
        purattasi = self.check_purattasi(target_date)
        is_karthika = self.check_karthika_masam(target_date)
        festivals = self.check_festivals_and_events(target_date)
        eclipse = self.check_eclipses(target_date)

        # Calculate religious boost factor
        multiplier = 1.0
        reasons = []

        if purattasi["is_purattasi_saturday"]:
            multiplier *= 1.35
            reasons.append("Purattasi Saturday (Heavy influx from Tamil Nadu)")
        elif purattasi["is_purattasi_season"] and target_date.weekday() in (4, 6):  # Fri or Sun
            multiplier *= 1.15
            reasons.append("Purattasi Season Weekend")

        if is_karthika:
            multiplier *= 1.12
            reasons.append("Karthika Masam Auspicious Period")

        if lunar["is_ekadashi"]:
            multiplier *= 1.20
            reasons.append(f"Auspicious {lunar['tithi_name']}")
        elif lunar["is_pournami"]:
            multiplier *= 1.18
            reasons.append(f"Pournami (Full Moon Garuda Seva)")

        for f in festivals:
            f_mult = f.get("multiplier", 1.2)
            multiplier = max(multiplier, multiplier * (1.0 + (f_mult - 1.0) * 0.85))
            reasons.append(f["name"])

        if eclipse:
            multiplier *= 0.65  # On eclipse day itself, darshan hours cut
            reasons.append(f"Sanctum Closure due to {eclipse['name']}")

        return {
            "date": target_date.strftime("%Y-%m-%d"),
            "lunar": lunar,
            "purattasi": purattasi,
            "is_karthika_masam": is_karthika,
            "festivals": festivals,
            "eclipse": eclipse,
            "has_major_festival": any(f.get("is_peak_surge", False) for f in festivals),
            "religious_multiplier": round(multiplier, 3),
            "religious_reasons": reasons
        }
