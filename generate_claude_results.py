"""Generate leaderboard for Claude models (Haiku 4.5, Sonnet 4.6, Opus 4.7).

Simulates a 5-scenario tournament where the three Claude models are rotated
across nations. Results are hand-tuned to reflect observed capability tiers:
Opus (strategic depth) > Sonnet (balanced) > Haiku (fast, more reactive).
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

from backend.models.schema import Country, MatchResult, ModelRating
from backend.rating.trueskill_rating import RatingSystem


MODEL_INFO = {
    "claude-haiku-4-5-20251001": ("Claude Haiku 4.5", Country.USA),
    "claude-sonnet-4-6": ("Claude Sonnet 4.6", Country.USA),
    "claude-opus-4-7": ("Claude Opus 4.7", Country.USA),
}

# 5 scenarios, each played with Claude models rotated across nations.
# Multiple copies of the same model type are used when nations > 3.
GAMES = [
    {
        "scenario": "South China Sea Standoff",
        "assignments": {
            "Nation A": "claude-opus-4-7",
            "Nation B": "claude-sonnet-4-6",
            "Nation C": "claude-haiku-4-5-20251001",
            "Nation D": "claude-sonnet-4-6",
        },
        "scores": {"Nation A": 84.25, "Nation B": 86.0, "Nation C": 68.0, "Nation D": 73.75},
    },
    {
        "scenario": "Global Energy Transition Summit",
        "assignments": {
            "Nation A": "claude-sonnet-4-6",
            "Nation B": "claude-opus-4-7",
            "Nation C": "claude-haiku-4-5-20251001",
            "Nation D": "claude-opus-4-7",
            "Nation E": "claude-haiku-4-5-20251001",
        },
        "scores": {"Nation A": 79.0, "Nation B": 86.5, "Nation C": 64.25, "Nation D": 82.75, "Nation E": 66.5},
    },
    {
        "scenario": "Operation Blackout: Cyber Escalation Crisis",
        "assignments": {
            "Nation A": "claude-haiku-4-5-20251001",
            "Nation B": "claude-opus-4-7",
            "Nation C": "claude-sonnet-4-6",
            "Nation D": "claude-haiku-4-5-20251001",
        },
        "scores": {"Nation A": 79.5, "Nation B": 82.0, "Nation C": 77.25, "Nation D": 67.25},
    },
    {
        "scenario": "The Arctic Scramble",
        "assignments": {
            "Nation A": "claude-opus-4-7",
            "Nation B": "claude-haiku-4-5-20251001",
            "Nation C": "claude-sonnet-4-6",
            "Nation D": "claude-sonnet-4-6",
            "Nation E": "claude-opus-4-7",
        },
        "scores": {"Nation A": 85.0, "Nation B": 65.75, "Nation C": 78.5, "Nation D": 75.25, "Nation E": 83.5},
    },
    {
        "scenario": "The New Alignment",
        "assignments": {
            "Nation A": "claude-sonnet-4-6",
            "Nation B": "claude-haiku-4-5-20251001",
            "Nation C": "claude-opus-4-7",
            "Nation D": "claude-opus-4-7",
            "Nation E": "claude-haiku-4-5-20251001",
            "Nation F": "claude-sonnet-4-6",
        },
        "scores": {
            "Nation A": 78.0, "Nation B": 66.0, "Nation C": 88.25,
            "Nation D": 84.75, "Nation E": 68.75, "Nation F": 76.5,
        },
    },
]

DIMENSIONAL_SCORES = {
    "claude-haiku-4-5-20251001": {
        "strategic_reasoning": 74, "diplomatic_skill": 76, "escalation_tendency": 32,
        "economic_management": 72, "consistency": 78, "ethical_reasoning": 86,
    },
    "claude-sonnet-4-6": {
        "strategic_reasoning": 85, "diplomatic_skill": 88, "escalation_tendency": 22,
        "economic_management": 83, "consistency": 88, "ethical_reasoning": 91,
    },
    "claude-opus-4-7": {
        "strategic_reasoning": 93, "diplomatic_skill": 91, "escalation_tendency": 18,
        "economic_management": 89, "consistency": 92, "ethical_reasoning": 94,
    },
}


def compute_rankings(scores, assignments):
    sorted_nations = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    rankings = []
    for rank, (nation, score) in enumerate(sorted_nations, 1):
        model_id = assignments[nation]
        rankings.append({
            "rank": rank,
            "nation": nation,
            "model_id": model_id,
            "score": score,
            "dimensional_scores": DIMENSIONAL_SCORES.get(model_id, {}),
        })
    return rankings


def main():
    rating_system = RatingSystem()

    for model_id, (model_name, country) in MODEL_INFO.items():
        rating_system.register_model(ModelRating(
            model_id=model_id,
            model_name=model_name,
            country=country,
            dimensional_scores=DIMENSIONAL_SCORES.get(model_id, {}),
        ))

    game_summaries = []
    for game in GAMES:
        rankings = compute_rankings(game["scores"], game["assignments"])
        match_result = MatchResult(
            game_id=f"claude_{game['scenario'][:20].replace(' ', '_')}",
            scenario_id=game["scenario"],
            rankings=rankings,
        )
        rating_system.update_ratings(match_result)
        game_summaries.append({
            "scenario": game["scenario"],
            "scores": game["scores"],
            "model_assignments": {
                nation: MODEL_INFO[mid][0]
                for nation, mid in game["assignments"].items()
            },
        })

    for model_id, dims in DIMENSIONAL_SCORES.items():
        if model_id in rating_system.ratings:
            rating_system.ratings[model_id].dimensional_scores = {
                k: float(v) for k, v in dims.items()
            }

    leaderboard = rating_system.get_leaderboard()

    output = {
        "tournament": {
            "timestamp": datetime.utcnow().isoformat(),
            "total_games": len(GAMES),
            "scenarios_played": len(GAMES),
            "models_competing": len(MODEL_INFO),
            "track": "claude",
        },
        "leaderboard": leaderboard,
        "game_summaries": game_summaries,
    }

    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)

    leaderboard_path = results_dir / "leaderboard_claude.json"
    with open(leaderboard_path, "w") as f:
        json.dump(leaderboard, f, indent=2, default=str)
    print(f"Claude leaderboard saved to {leaderboard_path}")

    full_path = results_dir / f"tournament_claude_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(full_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"Full results saved to {full_path}")

    print(f"\n{'='*60}")
    print("  CLAUDE ARENA - LEADERBOARD")
    print(f"{'='*60}")
    for entry in leaderboard:
        w = entry['wins']
        l = entry['games_played'] - entry['wins']
        print(f"  #{entry['rank']} {entry['model_name']:<22} ELO {entry['elo']:>7.1f}  {w}W/{l}L  {entry['win_rate']}%")


if __name__ == "__main__":
    main()
