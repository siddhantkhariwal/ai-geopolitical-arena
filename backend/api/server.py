"""FastAPI server for the AI Geopolitical Arena web dashboard."""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from backend.engine.tournament import DEFAULT_MODELS, Tournament
from backend.scenarios.templates import SCENARIOS

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Geopolitical Arena",
    description="Sovereign AI models compete in war game simulations",
    version="0.1.0",
)


@app.on_event("startup")
async def ensure_results():
    """Generate default results if none exist."""
    results_dir = Path("results")
    if not results_dir.exists() or not (results_dir / "leaderboard_latest.json").exists():
        logger.info("No results found, generating default leaderboard...")
        try:
            subprocess.run(["python", "generate_results.py"], check=True)
            logger.info("Default results generated.")
        except Exception as e:
            logger.warning(f"Could not generate default results: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

RESULTS_DIR = Path("results")
DASHBOARD_PATH = Path(__file__).parent / "dashboard.html"


@app.get("/")
async def root():
    html = DASHBOARD_PATH.read_text()
    return HTMLResponse(content=html, status_code=200)


@app.get("/api/leaderboard")
async def get_leaderboard():
    """Get the latest leaderboard."""
    path = RESULTS_DIR / "leaderboard_latest.json"
    if not path.exists():
        return {"leaderboard": [], "message": "No tournament results yet. Run a tournament first."}
    with open(path) as f:
        return {"leaderboard": json.load(f)}


@app.get("/api/scenarios")
async def get_scenarios():
    """List all available scenarios."""
    return {
        "scenarios": [
            {
                "id": s.id,
                "name": s.name,
                "type": s.type.value,
                "description": s.description,
                "nations": s.nations,
                "max_turns": s.max_turns,
                "tags": s.tags,
            }
            for s in SCENARIOS
        ]
    }


@app.get("/api/models")
async def get_models():
    """List all registered sovereign AI models."""
    return {
        "models": [
            {
                "id": m.id,
                "name": m.name,
                "provider": m.provider,
                "country": m.country.value,
                "model_id": m.model_id,
                "capability_tier": m.capability_tier,
                "is_open_source": m.is_open_source,
                "description": m.description,
            }
            for m in DEFAULT_MODELS
        ]
    }


@app.get("/api/games")
async def get_games():
    """List all completed game results."""
    results = []
    for p in sorted(RESULTS_DIR.glob("tournament_*.json"), reverse=True):
        with open(p) as f:
            data = json.load(f)
            results.append({
                "file": p.name,
                "timestamp": data.get("tournament", {}).get("timestamp"),
                "total_games": data.get("tournament", {}).get("total_games"),
                "game_summaries": data.get("game_summaries", []),
            })
    return {"tournaments": results}


@app.post("/api/tournament/run")
async def run_tournament(scenario_index: int | None = None, games_per_scenario: int = 1):
    """Trigger a tournament run."""
    scenarios = [SCENARIOS[scenario_index]] if scenario_index is not None else SCENARIOS

    tournament = Tournament(scenarios=scenarios)
    try:
        result = await tournament.run_tournament(games_per_scenario=games_per_scenario)
        return {
            "status": "complete",
            "total_games": result["tournament"]["total_games"],
            "leaderboard": result["leaderboard"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


