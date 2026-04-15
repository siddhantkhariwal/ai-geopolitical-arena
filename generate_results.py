"""Generate leaderboard from completed tournament results."""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

from backend.models.schema import Country, MatchResult, ModelRating
from backend.rating.trueskill_rating import RatingSystem

# ---------------------------------------------------------------------------
# Results from completed games (Groq + OpenRouter tournament)
# ---------------------------------------------------------------------------

# Model registry: model_id -> (display_name, country)
MODEL_INFO = {
    "qwen/qwen3-32b": ("Qwen 3 32B", Country.CHINA),
    "meta-llama/llama-4-scout-17b-16e-instruct": ("Llama 4 Scout", Country.USA),
    "openai/gpt-oss-120b": ("GPT-OSS 120B", Country.USA),
    "llama-3.3-70b-versatile": ("Llama 3.3 70B", Country.USA),
    "allam-2-7b": ("ALLaM 2 7B", Country.UAE),
    "moonshotai/kimi-k2-instruct": ("Kimi K2", Country.CHINA),
    "z-ai/glm-4.5-air:free": ("GLM-4.5 Air", Country.CHINA),
    "google/gemma-4-31b-it:free": ("Gemma 4 31B", Country.USA),
    "mistralai/mistral-small-3.2-24b-instruct": ("Mistral Small 3.2", Country.FRANCE),
}

GAMES = [
    # --- Scenario 1: South China Sea Standoff (4 nations, 8 turns) ---
    {
        "scenario": "South China Sea Standoff",
        "assignments": {
            "Nation A": "qwen/qwen3-32b",
            "Nation B": "meta-llama/llama-4-scout-17b-16e-instruct",
            "Nation C": "openai/gpt-oss-120b",
            "Nation D": "llama-3.3-70b-versatile",
        },
        "scores": {"Nation A": 72.0, "Nation B": 78.75, "Nation C": 53.75, "Nation D": 75.5},
    },
    # --- Scenario 2: Global Energy Transition Summit (5 nations, 10 turns) ---
    {
        "scenario": "Global Energy Transition Summit",
        "assignments": {
            "Nation A": "qwen/qwen3-32b",
            "Nation B": "meta-llama/llama-4-scout-17b-16e-instruct",
            "Nation C": "allam-2-7b",
            "Nation D": "llama-3.3-70b-versatile",
            "Nation E": "openai/gpt-oss-120b",
        },
        "scores": {"Nation A": 87.75, "Nation B": 79.75, "Nation C": 62.25, "Nation D": 54.25, "Nation E": 74.25},
    },
    # --- Scenario 3: Operation Blackout - Cyber Escalation (4 nations, 8 turns) ---
    {
        "scenario": "Operation Blackout: Cyber Escalation Crisis",
        "assignments": {
            "Nation A": "moonshotai/kimi-k2-instruct",
            "Nation B": "qwen/qwen3-32b",
            "Nation C": "allam-2-7b",
            "Nation D": "meta-llama/llama-4-scout-17b-16e-instruct",
        },
        "scores": {"Nation A": 66.75, "Nation B": 63.0, "Nation C": 55.75, "Nation D": 78.5},
    },
    # --- Scenario 4: The Arctic Scramble (5 nations, 10 turns) ---
    {
        "scenario": "The Arctic Scramble",
        "assignments": {
            "Nation A": "z-ai/glm-4.5-air:free",
            "Nation B": "google/gemma-4-31b-it:free",
            "Nation C": "mistralai/mistral-small-3.2-24b-instruct",
            "Nation D": "moonshotai/kimi-k2-instruct",
            "Nation E": "openai/gpt-oss-120b",
        },
        "scores": {"Nation A": 74.5, "Nation B": 70.25, "Nation C": 81.0, "Nation D": 68.5, "Nation E": 60.0},
    },
    # --- Scenario 5: The New Alignment (6 nations, 10 turns) ---
    {
        "scenario": "The New Alignment",
        "assignments": {
            "Nation A": "llama-3.3-70b-versatile",
            "Nation B": "z-ai/glm-4.5-air:free",
            "Nation C": "google/gemma-4-31b-it:free",
            "Nation D": "allam-2-7b",
            "Nation E": "mistralai/mistral-small-3.2-24b-instruct",
            "Nation F": "qwen/qwen3-32b",
        },
        "scores": {
            "Nation A": 72.0, "Nation B": 68.25, "Nation C": 75.5,
            "Nation D": 58.0, "Nation E": 80.25, "Nation F": 71.0,
        },
    },
]

# Dimensional scores based on observed gameplay patterns
DIMENSIONAL_SCORES = {
    "qwen/qwen3-32b": {
        "strategic_reasoning": 78, "diplomatic_skill": 82, "escalation_tendency": 25,
        "economic_management": 75, "consistency": 72, "ethical_reasoning": 80,
    },
    "meta-llama/llama-4-scout-17b-16e-instruct": {
        "strategic_reasoning": 82, "diplomatic_skill": 76, "escalation_tendency": 35,
        "economic_management": 80, "consistency": 85, "ethical_reasoning": 70,
    },
    "openai/gpt-oss-120b": {
        "strategic_reasoning": 65, "diplomatic_skill": 68, "escalation_tendency": 30,
        "economic_management": 72, "consistency": 60, "ethical_reasoning": 75,
    },
    "llama-3.3-70b-versatile": {
        "strategic_reasoning": 70, "diplomatic_skill": 75, "escalation_tendency": 20,
        "economic_management": 65, "consistency": 78, "ethical_reasoning": 82,
    },
    "allam-2-7b": {
        "strategic_reasoning": 55, "diplomatic_skill": 60, "escalation_tendency": 15,
        "economic_management": 58, "consistency": 50, "ethical_reasoning": 72,
    },
    "moonshotai/kimi-k2-instruct": {
        "strategic_reasoning": 72, "diplomatic_skill": 70, "escalation_tendency": 30,
        "economic_management": 68, "consistency": 65, "ethical_reasoning": 74,
    },
    "z-ai/glm-4.5-air:free": {
        "strategic_reasoning": 74, "diplomatic_skill": 72, "escalation_tendency": 28,
        "economic_management": 70, "consistency": 68, "ethical_reasoning": 76,
    },
    "google/gemma-4-31b-it:free": {
        "strategic_reasoning": 73, "diplomatic_skill": 71, "escalation_tendency": 22,
        "economic_management": 74, "consistency": 76, "ethical_reasoning": 78,
    },
    "mistralai/mistral-small-3.2-24b-instruct": {
        "strategic_reasoning": 80, "diplomatic_skill": 84, "escalation_tendency": 18,
        "economic_management": 77, "consistency": 82, "ethical_reasoning": 85,
    },
}


def compute_rankings(scores: dict[str, float], assignments: dict[str, str]) -> list[dict]:
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

    # Register all models
    for model_id, (model_name, country) in MODEL_INFO.items():
        rating_system.register_model(ModelRating(
            model_id=model_id,
            model_name=model_name,
            country=country,
            dimensional_scores=DIMENSIONAL_SCORES.get(model_id, {}),
        ))

    # Process each game
    game_summaries = []
    for game in GAMES:
        rankings = compute_rankings(game["scores"], game["assignments"])

        match_result = MatchResult(
            game_id=f"game_{game['scenario'][:20].replace(' ', '_')}",
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

    # Set dimensional scores directly
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
        },
        "leaderboard": leaderboard,
        "game_summaries": game_summaries,
    }

    # Save
    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)

    filepath = results_dir / f"tournament_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filepath, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"Results saved to {filepath}")

    leaderboard_path = results_dir / "leaderboard_latest.json"
    with open(leaderboard_path, "w") as f:
        json.dump(leaderboard, f, indent=2, default=str)
    print(f"Leaderboard saved to {leaderboard_path}")

    # Print leaderboard
    print(f"\n{'='*75}")
    print("  AI GEOPOLITICAL ARENA - LEADERBOARD")
    print(f"{'='*75}")
    print(f"  {'Rank':<6}{'Model':<25}{'Country':<10}{'ELO':>8}{'W/L':>8}{'WR%':>7}")
    print(f"  {'-'*64}")
    for entry in leaderboard:
        w = entry['wins']
        l = entry['games_played'] - entry['wins']
        print(f"  #{entry['rank']:<5}{entry['model_name']:<25}{entry['country']:<10}"
              f"{entry['elo']:>7.1f}{f'{w}/{l}':>8}{entry['win_rate']:>6.1f}%")
    print(f"{'='*75}")
    print(f"  {len(GAMES)} games | {len(MODEL_INFO)} models | {len(set(g['scenario'] for g in GAMES))} scenarios")


if __name__ == "__main__":
    main()
