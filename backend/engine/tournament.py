"""Tournament runner - orchestrates multiple games across scenarios."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.adapters.providers import create_adapter
from backend.engine.game_engine import GameEngine
from backend.engine.judge import JudgeEngine
from backend.models.schema import (
    Country,
    Game,
    MatchResult,
    ModelRating,
    Scenario,
    SovereignModel,
)
from backend.rating.trueskill_rating import RatingSystem
from backend.scenarios.templates import SCENARIOS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Default model registry
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# FREE models (Groq + OpenRouter) - $0 cost
# ---------------------------------------------------------------------------

FREE_MODELS: list[SovereignModel] = [
    # --- Via Groq (fast, free) ---
    SovereignModel(
        name="Llama 3.3 70B",
        provider="groq",
        country=Country.USA,
        model_id="llama-3.3-70b-versatile",
        capability_tier="near-frontier",
        is_open_source=True,
        description="Meta's Llama 3.3 via Groq (USA)",
    ),
    SovereignModel(
        name="Llama 4 Scout",
        provider="groq",
        country=Country.USA,
        model_id="meta-llama/llama-4-scout-17b-16e-instruct",
        capability_tier="strong",
        is_open_source=True,
        description="Meta's Llama 4 Scout via Groq (USA)",
    ),
    SovereignModel(
        name="Qwen 3 32B",
        provider="groq",
        country=Country.CHINA,
        model_id="qwen/qwen3-32b",
        capability_tier="strong",
        is_open_source=True,
        description="Alibaba's Qwen 3 via Groq (China)",
    ),
    SovereignModel(
        name="Kimi K2",
        provider="groq",
        country=Country.CHINA,
        model_id="moonshotai/kimi-k2-instruct",
        capability_tier="frontier",
        is_open_source=True,
        description="Moonshot AI's Kimi K2 via Groq (China)",
    ),
    SovereignModel(
        name="ALLaM 2 7B",
        provider="groq",
        country=Country.UAE,
        model_id="allam-2-7b",
        capability_tier="mid",
        is_open_source=True,
        description="Saudi SDAIA's ALLaM 2 Arabic model via Groq (Saudi/UAE)",
    ),
    SovereignModel(
        name="GPT-OSS 120B",
        provider="groq",
        country=Country.USA,
        model_id="openai/gpt-oss-120b",
        capability_tier="near-frontier",
        is_open_source=True,
        description="OpenAI's open-source 120B model via Groq (USA)",
    ),
    # --- Via OpenRouter (free tier) ---
    SovereignModel(
        name="GLM-4.5 Air",
        provider="openrouter",
        country=Country.CHINA,
        model_id="z-ai/glm-4.5-air:free",
        capability_tier="strong",
        is_open_source=True,
        description="Zhipu AI's GLM-4.5 Air (China)",
    ),
    SovereignModel(
        name="Gemma 4 31B",
        provider="openrouter",
        country=Country.USA,
        model_id="google/gemma-4-31b-it:free",
        capability_tier="strong",
        is_open_source=True,
        description="Google's Gemma 4 31B (USA)",
    ),
    SovereignModel(
        name="Mistral Small 3.2",
        provider="openrouter",
        country=Country.FRANCE,
        model_id="mistralai/mistral-small-3.2-24b-instruct",
        capability_tier="strong",
        is_open_source=True,
        description="Mistral AI's Small 3.2 24B (France)",
    ),
]

# ---------------------------------------------------------------------------
# PREMIUM models (requires paid API keys)
# ---------------------------------------------------------------------------

PREMIUM_MODELS: list[SovereignModel] = [
    SovereignModel(
        name="GPT-4o",
        provider="openai",
        country=Country.USA,
        model_id="gpt-4o",
        capability_tier="frontier",
        description="OpenAI's flagship model (USA)",
    ),
    SovereignModel(
        name="Claude Sonnet 4",
        provider="anthropic",
        country=Country.USA,
        model_id="claude-sonnet-4-20250514",
        capability_tier="frontier",
        description="Anthropic's Claude (USA)",
    ),
]

# Default to free models
DEFAULT_MODELS = FREE_MODELS


class Tournament:
    """Runs a full tournament across models and scenarios."""

    def __init__(
        self,
        models: list[SovereignModel] | None = None,
        scenarios: list[Scenario] | None = None,
        output_dir: str = "results",
    ):
        self.models = models or DEFAULT_MODELS
        self.scenarios = scenarios or SCENARIOS
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.rating_system = RatingSystem()
        self.judge = JudgeEngine()
        self.results: list[MatchResult] = []
        self.games: list[Game] = []

        # Register models in rating system
        for model in self.models:
            self.rating_system.register_model(ModelRating(
                model_id=model.model_id,
                model_name=model.name,
                country=model.country,
            ))

    def _get_api_key(self, model: SovereignModel) -> str | None:
        """Get API key for a model from environment variables."""
        key_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "mistral": "MISTRAL_API_KEY",
            "qwen": "DASHSCOPE_API_KEY",
            "google": "GOOGLE_API_KEY",
            "cohere": "COHERE_API_KEY",
            "groq": "GROQ_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
        }
        env_var = key_map.get(model.provider, f"{model.provider.upper()}_API_KEY")
        return os.environ.get(env_var)

    def _create_adapter(self, model: SovereignModel):
        """Create an adapter for a sovereign model."""
        return create_adapter(
            provider=model.provider,
            model_id=model.model_id,
            api_key=self._get_api_key(model),
            api_base=model.api_base,
        )

    async def run_game(self, scenario: Scenario, model_assignments: dict[str, SovereignModel]) -> Game | None:
        """Run a single game with specific model assignments."""
        adapters = {}
        for nation, model in model_assignments.items():
            adapters[nation] = self._create_adapter(model)

        engine = GameEngine(scenario, adapters)

        async def on_turn(turn_result):
            logger.info(f"  Turn {turn_result.turn} narrative:")
            for line in turn_result.narrative.split("\n"):
                if line.strip():
                    logger.info(f"    {line.strip()}")

        try:
            game = await engine.run(on_turn=on_turn)
            return game
        except Exception as e:
            logger.error(f"Game failed: {e}")
            return None

    async def run_tournament(self, games_per_scenario: int = 1) -> dict[str, Any]:
        """Run the full tournament.

        Each scenario is played `games_per_scenario` times, rotating model assignments.
        """
        logger.info(f"Starting tournament: {len(self.models)} models x {len(self.scenarios)} scenarios")

        for scenario in self.scenarios:
            logger.info(f"\n{'='*60}")
            logger.info(f"SCENARIO: {scenario.name}")
            logger.info(f"{'='*60}")

            for game_num in range(games_per_scenario):
                # Assign models to nations (rotate assignments)
                assignments = self._assign_models(scenario, game_num)

                assignment_str = ", ".join(
                    f"{nation}: {model.name}" for nation, model in assignments.items()
                )
                logger.info(f"\nGame {game_num + 1} assignments: {assignment_str}")

                game = await self.run_game(scenario, assignments)

                if game:
                    self.games.append(game)

                    # Judge the game
                    match_result = self.judge.evaluate(game)
                    self.results.append(match_result)

                    # Update ratings
                    self.rating_system.update_ratings(match_result)

                    # Log results
                    logger.info(f"\nGame results:")
                    for r in match_result.rankings:
                        logger.info(f"  #{r['rank']} {r['nation']} ({r['model_id']}): {r['score']}")

        # Generate final output
        leaderboard = self.rating_system.get_leaderboard()
        output = {
            "tournament": {
                "timestamp": datetime.utcnow().isoformat(),
                "total_games": len(self.games),
                "scenarios_played": len(self.scenarios),
                "models_competing": len(self.models),
            },
            "leaderboard": leaderboard,
            "game_summaries": [self._summarize_game(g) for g in self.games],
        }

        # Save results
        self._save_results(output)

        return output

    def _assign_models(self, scenario: Scenario, rotation: int) -> dict[str, SovereignModel]:
        """Assign models to nations, rotating based on game number.

        Uses a deterministic shuffle so all models get a chance to play
        across different scenarios even when nation count < model count.
        """
        import random
        available = list(self.models)
        n_nations = len(scenario.nations)

        # Deterministic shuffle based on scenario name + rotation
        seed = hash(scenario.name) + rotation
        rng = random.Random(seed)
        rng.shuffle(available)

        assignments = {}
        for i, nation in enumerate(scenario.nations):
            assignments[nation] = available[i % len(available)]

        return assignments

    def _summarize_game(self, game: Game) -> dict[str, Any]:
        return {
            "game_id": game.id,
            "scenario": game.scenario.name,
            "turns_played": len(game.turns),
            "scores": game.scores,
            "model_assignments": game.model_assignments,
        }

    def _save_results(self, output: dict[str, Any]) -> None:
        """Save tournament results to JSON."""
        filepath = self.output_dir / f"tournament_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filepath, "w") as f:
            json.dump(output, f, indent=2, default=str)
        logger.info(f"\nResults saved to {filepath}")

        # Also save latest leaderboard separately
        leaderboard_path = self.output_dir / "leaderboard_latest.json"
        with open(leaderboard_path, "w") as f:
            json.dump(output["leaderboard"], f, indent=2, default=str)
        logger.info(f"Leaderboard saved to {leaderboard_path}")
