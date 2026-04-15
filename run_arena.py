#!/usr/bin/env python3
"""
AI Geopolitical Arena - Main entry point.

Run sovereign AI models against each other in war game simulations
and rank them on an ELO-based leaderboard.

Usage:
    python3 run_arena.py                       # Run free models tournament
    python3 run_arena.py --premium             # Include paid models (GPT-4o, Claude)
    python3 run_arena.py --scenario 0          # Run specific scenario by index
    python3 run_arena.py --models 4            # Use only first N models
    python3 run_arena.py --games 3             # Games per scenario
    python3 run_arena.py --list-scenarios      # List available scenarios
    python3 run_arena.py --list-models         # List registered models
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Load .env file
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

from backend.engine.tournament import DEFAULT_MODELS, FREE_MODELS, PREMIUM_MODELS, Tournament
from backend.scenarios.templates import SCENARIOS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                  AI GEOPOLITICAL ARENA                       ║
║        Sovereign AI Models in Strategic War Games            ║
║                                                              ║
║  Pit frontier AI models from different nations against       ║
║  each other in geopolitical simulations and rank them        ║
║  on an ELO-based leaderboard.                               ║
╚══════════════════════════════════════════════════════════════╝
    """)


def list_scenarios():
    print("\nAvailable Scenarios:")
    print("-" * 60)
    for i, s in enumerate(SCENARIOS):
        print(f"  [{i}] {s.name}")
        print(f"      Type: {s.type.value} | Nations: {len(s.nations)} | Turns: {s.max_turns}")
        print(f"      {s.description}")
        print()


def list_models(models):
    print("\nRegistered Sovereign AI Models:")
    print("-" * 60)
    for m in models:
        cost = "FREE" if m.provider in ("groq", "openrouter") else "PAID"
        print(f"  {m.name} [{cost}]")
        print(f"      Country: {m.country.value} | Provider: {m.provider} | Tier: {m.capability_tier}")
        print(f"      Model ID: {m.model_id}")
        print()


def print_leaderboard(leaderboard):
    print("\n" + "=" * 80)
    print("                        FINAL LEADERBOARD")
    print("=" * 80)
    print(f"{'Rank':<6}{'Model':<25}{'Country':<12}{'ELO':<10}{'W/L':<10}{'Win%':<8}")
    print("-" * 80)

    for entry in leaderboard:
        wins = entry['wins']
        games = entry['games_played']
        losses = games - wins
        print(
            f"#{entry['rank']:<5}"
            f"{entry['model_name']:<25}"
            f"{entry['country']:<12}"
            f"{entry['elo']:<10}"
            f"{wins}W/{losses}L{'':<4}"
            f"{entry['win_rate']}%"
        )

    print("\n" + "-" * 80)
    print("Dimensional Scores:")
    print("-" * 80)

    for entry in leaderboard:
        print(f"\n  {entry['model_name']} ({entry['country']}):")
        ds = entry['dimensional_scores']
        print(f"    Strategic: {ds.get('strategic_reasoning', 'N/A'):<8}"
              f"Diplomatic: {ds.get('diplomatic_skill', 'N/A'):<8}"
              f"Economic: {ds.get('economic_management', 'N/A'):<8}")

        esc = ds.get('escalation_tendency', 50)
        if isinstance(esc, (int, float)):
            hawk_dove = "HAWK" if esc > 60 else "DOVE" if esc < 40 else "MODERATE"
        else:
            hawk_dove = "N/A"
        print(f"    Escalation: {esc:<8} ({hawk_dove})  "
              f"Ethics: {ds.get('ethical_reasoning', 'N/A'):<8}"
              f"Consistency: {ds.get('consistency', 'N/A')}")


async def main():
    parser = argparse.ArgumentParser(description="AI Geopolitical Arena")
    parser.add_argument("--scenario", type=int, help="Run specific scenario by index")
    parser.add_argument("--models", type=int, help="Use only first N models")
    parser.add_argument("--games", type=int, default=1, help="Games per scenario (default: 1)")
    parser.add_argument("--list-scenarios", action="store_true", help="List available scenarios")
    parser.add_argument("--list-models", action="store_true", help="List registered models")
    parser.add_argument("--premium", action="store_true", help="Include premium models (GPT-4o, Claude)")
    parser.add_argument("--output", type=str, default="results", help="Output directory")

    args = parser.parse_args()

    print_banner()

    # Select models
    if args.premium:
        all_models = FREE_MODELS + PREMIUM_MODELS
        print("Mode: FREE + PREMIUM models")
    else:
        all_models = FREE_MODELS
        print("Mode: FREE models only (Groq + OpenRouter)")

    if args.list_scenarios:
        list_scenarios()
        return

    if args.list_models:
        list_models(all_models)
        return

    models = all_models[:args.models] if args.models else all_models

    # Select scenarios
    if args.scenario is not None:
        if args.scenario >= len(SCENARIOS):
            print(f"Error: Scenario index {args.scenario} out of range (0-{len(SCENARIOS)-1})")
            sys.exit(1)
        scenarios = [SCENARIOS[args.scenario]]
    else:
        scenarios = SCENARIOS

    # Check for API keys
    print("\nChecking API keys...")
    t_check = Tournament(models=models)
    missing = []
    for model in models:
        key = t_check._get_api_key(model)
        status = "OK" if key else "MISSING"
        if not key:
            missing.append(model.name)
        print(f"  {model.name} ({model.country.value}): {status}")

    if missing:
        print(f"\nWarning: Missing API keys for: {', '.join(missing)}")
        print("Models without keys will fail during gameplay.\n")
        response = input("Continue anyway? [y/N] ")
        if response.lower() != 'y':
            print("Aborted.")
            return

    print(f"\nStarting tournament:")
    print(f"  Models: {len(models)}")
    print(f"  Scenarios: {len(scenarios)}")
    print(f"  Games per scenario: {args.games}")
    print(f"  Total games: {len(scenarios) * args.games}")
    print()

    # Run tournament
    tournament = Tournament(models=models, scenarios=scenarios, output_dir=args.output)
    results = await tournament.run_tournament(games_per_scenario=args.games)

    # Print results
    print_leaderboard(results["leaderboard"])

    print(f"\nTournament complete!")
    print(f"  Games played: {results['tournament']['total_games']}")
    print(f"  Results saved to: {args.output}/")


if __name__ == "__main__":
    asyncio.run(main())
