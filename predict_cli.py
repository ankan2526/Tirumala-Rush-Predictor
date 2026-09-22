#!/usr/bin/env python3
"""Interactive Command-Line Interface for Tirumala Tirupati Rush Predictor.

Examples:
  python predict_cli.py --date 2026-10-06
  python predict_cli.py --month 2026-10
  python predict_cli.py --recommend --start 2026-11-01 --end 2026-11-30
  python predict_cli.py --live
  python predict_cli.py --train
"""

from __future__ import annotations
import argparse
import sys
from datetime import date, datetime, timedelta

from src.models.predictor import TirumalaRushPredictor
from src.models.ml_trainer import MLTrainer
from src.data_pipeline.dataset_generator import DatasetGenerator


def format_rush_badge(rush_level: str) -> str:
    badges = {
        "LOW": "🟢 LOW RUSH",
        "MODERATE": "🟡 MODERATE",
        "HIGH": "🟠 HIGH RUSH",
        "PEAK": "🔴 PEAK SURGE"
    }
    return badges.get(rush_level, rush_level)


def cmd_predict_date(predictor: TirumalaRushPredictor, target_date: date) -> None:
    res = predictor.predict_date(target_date)
    print("\n" + "=" * 68)
    print(f"🛕  TIRUMALA TIRUPATI DARSHANAM RUSH FORECAST")
    print(f"    Date: {res['date']} ({res['day_name']})")
    print("=" * 68)

    print(f"Status:             {format_rush_badge(res['rush_level'])} ({res['rush_label']})")
    print(f"Lunar Tithi:        {res['tithi']} ({res['paksha']} Paksha, Moon: {res['moon_illumination']})")
    print(f"Estimated Devotees: {res['estimated_pilgrims']:,} pilgrims")
    print(f"VKC Compartments:   {res['compartments_filled']} / 31 filled")
    print("-" * 68)
    print(f"⏱️  WAITING TIMES:")
    print(f"  • Sarva Darshan (Free / SSD):   {res['sarva_darshan_wait_range']} ({res['sarva_darshan_wait_hours']} hrs average)")
    print(f"  • Special Entry (SED ₹300):     {res['sed_wait_range']} ({res['sed_wait_hours']} hrs average)")
    print(f"  • Divya Darshan (Pedestrians):  ~{res['divya_darshan_wait_hours']} hrs")
    print("-" * 68)
    print(f"💰 Secondary Indicators:")
    print(f"  • Estimated Hundi: ₹ {res['est_hundi_crores']} Crores")
    print(f"  • Tonsures:        ~{res['est_tonsures']:,}")
    print(f"  • Laddus:          ~{res['est_laddus']:,}")

    if res['factors']:
        print("-" * 68)
        print("🔍 Contributing Factors:")
        for f in res['factors']:
            sign = "✓" if f['favorable'] else "▲"
            print(f"  [{sign}] {f['name']} ({f['category']}): {f['impact']} -> {f['detail']}")

    print("-" * 68)
    print("💡 Tactical Advice:")
    print(f"  • Best Sarva Entry: {res['recommendations']['best_sarva_entry']}")
    print(f"  • Best SED Entry:   {res['recommendations']['best_sed_entry']}")
    for tip in res['recommendations']['travel_tips']:
        print(f"  • {tip}")
    print("=" * 68 + "\n")


def cmd_predict_month(predictor: TirumalaRushPredictor, year: int, month: int) -> None:
    days = predictor.predict_month(year, month)
    month_name = datetime(year, month, 1).strftime("%B %Y")
    print("\n" + "=" * 80)
    print(f"📅  TIRUMALA MONTHLY RUSH CALENDAR — {month_name.upper()}")
    print("=" * 80)
    print(f"{'Date':<12} {'Day':<10} {'Rush Level':<14} {'Devotees':<12} {'Sarva Wait':<12} {'SED Wait':<10} {'Event / Note'}")
    print("-" * 80)

    for d in days:
        badge = format_rush_badge(d['rush_level'])
        evt = d['highlight_event'] or "-"
        print(f"{d['date']:<12} {d['day_name'][:3]:<10} {badge:<14} {d['estimated_pilgrims']:<12,d} {str(d['sarva_darshan_wait_hours']) + ' hrs':<12} {str(d['sed_wait_hours']) + ' hrs':<10} {evt[:18]}")

    print("=" * 80 + "\n")


def cmd_recommend(predictor: TirumalaRushPredictor, start_date: date, end_date: date, darshan_type: str) -> None:
    recs = predictor.recommend_best_dates(start_date, end_date, darshan_type=darshan_type, max_results=7)
    print("\n" + "=" * 76)
    print(f"✈️  TOP LOW-CROWD DARSHAN DATES: {start_date} to {end_date}")
    print(f"    Preference: {darshan_type.upper()}")
    print("=" * 76)

    for idx, r in enumerate(recs, 1):
        saved = f" (Saves {r['hours_saved_vs_peak']} hrs vs peak!)" if r.get('hours_saved_vs_peak', 0) > 0 else ""
        print(f"#{idx}  {r['date']} ({r['day_name']}) — {format_rush_badge(r['rush_level'])}")
        print(f"    Sarva Wait: {r['sarva_darshan_wait_hours']} hrs | SED ₹300: {r['sed_wait_hours']} hrs | Crowd: {r['estimated_pilgrims']:,}{saved}")
        print(f"    Tithi: {r['tithi']}")
        print(f"    Advice: {r['advice']}\n")

    print("=" * 76 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Tirumala Tirupati Daily Rush & Crowd Predictor CLI")
    parser.add_argument("--date", help="Target date in YYYY-MM-DD format (e.g. 2026-10-06)")
    parser.add_argument("--month", help="Target month in YYYY-MM format (e.g. 2026-10)")
    parser.add_argument("--live", action="store_true", help="Show today's live darshan status")
    parser.add_argument("--recommend", action="store_true", help="Recommend best visit dates in a range")
    parser.add_argument("--start", help="Start date for recommendations (YYYY-MM-DD)")
    parser.add_argument("--end", help="End date for recommendations (YYYY-MM-DD)")
    parser.add_argument("--ticket", default="all", choices=["all", "sed"], help="Darshan ticket category")
    parser.add_argument("--train", action="store_true", help="Regenerate dataset and train ML models")

    args = parser.parse_args()
    predictor = TirumalaRushPredictor()

    if args.train:
        print("Regenerating calibrated historical dataset (2018-2026)...")
        gen = DatasetGenerator()
        gen.generate()
        print("Training baseline regression models...")
        trainer = MLTrainer()
        metrics = trainer.train_and_evaluate()
        print("Training complete! Model metrics:")
        print(f"  Pilgrims MAE: ±{metrics['pilgrims_model']['mae']}, R²: {metrics['pilgrims_model']['r2']}")
        print(f"  Sarva Wait MAE: ±{metrics['sarva_wait_hours_model']['mae']} hrs, R²: {metrics['sarva_wait_hours_model']['r2']}")
        return

    if args.live:
        cmd_predict_date(predictor, date.today())
        return

    if args.recommend:
        today = date.today()
        start = datetime.strptime(args.start, "%Y-%m-%d").date() if args.start else today
        end = datetime.strptime(args.end, "%Y-%m-%d").date() if args.end else today + timedelta(days=30)
        cmd_recommend(predictor, start, end, args.ticket)
        return

    if args.month:
        try:
            parts = args.month.split("-")
            year = int(parts[0])
            month = int(parts[1])
            cmd_predict_month(predictor, year, month)
        except Exception as e:
            print(f"Invalid month format '{args.month}'. Expected YYYY-MM, e.g. 2026-10")
            sys.exit(1)
        return

    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
            cmd_predict_date(predictor, target_date)
        except ValueError:
            print(f"Invalid date format '{args.date}'. Expected YYYY-MM-DD, e.g. 2026-10-06")
            sys.exit(1)
        return

    # Default to today
    cmd_predict_date(predictor, date.today())


if __name__ == "__main__":
    main()
