"""Core data models for the AI Geopolitical Arena."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ModelProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    MISTRAL = "mistral"
    QWEN = "qwen"
    GOOGLE = "google"
    FALCON = "falcon"
    GIGACHAT = "gigachat"
    HYPERCLOVA = "hyperclova"
    SARVAM = "sarvam"
    COHERE = "cohere"
    GROQ = "groq"
    OPENROUTER = "openrouter"
    LOCAL = "local"  # For self-hosted open-source models


class Country(str, Enum):
    USA = "USA"
    CHINA = "China"
    FRANCE = "France"
    UAE = "UAE"
    SOUTH_KOREA = "South Korea"
    RUSSIA = "Russia"
    INDIA = "India"
    JAPAN = "Japan"
    GERMANY = "Germany"
    CANADA = "Canada"
    SINGAPORE = "Singapore"
    UK = "UK"


class ScenarioType(str, Enum):
    DIPLOMATIC = "diplomatic"
    CRISIS = "crisis"
    RESOURCE = "resource"
    ALLIANCE = "alliance"
    HUMANITARIAN = "humanitarian"
    TRADE = "trade"


class ActionType(str, Enum):
    NEGOTIATE = "negotiate"
    ALLY = "ally"
    SANCTION = "sanction"
    TRADE = "trade"
    MOBILIZE = "mobilize"
    DEMOBILIZE = "demobilize"
    AID = "aid"
    THREATEN = "threaten"
    ATTACK = "attack"
    DEFEND = "defend"
    PROPOSE_TREATY = "propose_treaty"
    WITHDRAW = "withdraw"
    ESPIONAGE = "espionage"
    CYBER_ATTACK = "cyber_attack"
    SEND_MESSAGE = "send_message"
    PASS = "pass"


class GamePhase(str, Enum):
    BRIEFING = "briefing"
    NEGOTIATION = "negotiation"
    ACTION = "action"
    RESOLUTION = "resolution"
    DEBRIEF = "debrief"
    COMPLETED = "completed"


# ---------------------------------------------------------------------------
# Sovereign AI Model
# ---------------------------------------------------------------------------

class SovereignModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # e.g. "DeepSeek-V3"
    provider: ModelProvider
    country: Country
    model_id: str  # API model identifier, e.g. "deepseek-chat"
    api_base: str | None = None  # Custom API base URL
    description: str = ""
    is_open_source: bool = False
    capability_tier: str = "mid"  # "frontier", "near-frontier", "strong", "mid"


# ---------------------------------------------------------------------------
# Game state models
# ---------------------------------------------------------------------------

class NationState(BaseModel):
    """The state of a nation within a game."""
    name: str
    controlled_by_model: str  # SovereignModel.id
    resources: dict[str, float] = Field(default_factory=lambda: {
        "military": 50.0,
        "economic": 50.0,
        "diplomatic": 50.0,
        "technology": 50.0,
        "public_approval": 50.0,
    })
    allies: list[str] = Field(default_factory=list)
    enemies: list[str] = Field(default_factory=list)
    treaties: list[str] = Field(default_factory=list)
    is_eliminated: bool = False


class Action(BaseModel):
    """An action taken by a nation during a turn."""
    turn: int
    nation: str
    action_type: ActionType
    target: str | None = None  # Target nation or resource
    message: str | None = None  # Diplomatic message content
    reasoning: str = ""  # Model's reasoning for the action
    raw_response: str = ""  # Full model response


class TurnResult(BaseModel):
    """The outcome of resolving all actions in a turn."""
    turn: int
    actions: list[Action]
    state_changes: dict[str, Any] = Field(default_factory=dict)
    narrative: str = ""  # Human-readable summary of what happened
    nation_states: dict[str, NationState] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Game & Scenario
# ---------------------------------------------------------------------------

class Scenario(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: ScenarioType
    description: str
    briefing: str  # Detailed scenario briefing shown to all players
    nations: list[str]  # Nation names participating
    nation_briefings: dict[str, str] = Field(default_factory=dict)  # Per-nation secret briefings
    initial_state: dict[str, dict[str, float]] = Field(default_factory=dict)
    max_turns: int = 10
    victory_conditions: dict[str, str] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class Game(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario: Scenario
    model_assignments: dict[str, str]  # nation_name -> SovereignModel.id
    nation_states: dict[str, NationState] = Field(default_factory=dict)
    turns: list[TurnResult] = Field(default_factory=list)
    current_turn: int = 0
    phase: GamePhase = GamePhase.BRIEFING
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    scores: dict[str, float] = Field(default_factory=dict)  # nation -> final score


# ---------------------------------------------------------------------------
# Rating
# ---------------------------------------------------------------------------

class ModelRating(BaseModel):
    model_id: str
    model_name: str
    country: Country
    elo: float = 1500.0
    mu: float = 25.0  # TrueSkill mu
    sigma: float = 8.333  # TrueSkill sigma
    games_played: int = 0
    wins: int = 0
    dimensional_scores: dict[str, float] = Field(default_factory=lambda: {
        "strategic_reasoning": 1500.0,
        "diplomatic_skill": 1500.0,
        "escalation_tendency": 50.0,  # 0=dove, 100=hawk
        "economic_management": 1500.0,
        "consistency": 1500.0,
        "ethical_reasoning": 1500.0,
    })


class MatchResult(BaseModel):
    game_id: str
    scenario_id: str
    rankings: list[dict[str, Any]]  # [{model_id, nation, score, rank}]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
