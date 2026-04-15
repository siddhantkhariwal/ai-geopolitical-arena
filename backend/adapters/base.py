"""Base adapter interface for sovereign AI models."""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any

from backend.models.schema import Action, ActionType


class ModelAdapter(ABC):
    """Base class for all model adapters."""

    def __init__(self, model_id: str, api_key: str | None = None, api_base: str | None = None):
        self.model_id = model_id
        self.api_key = api_key
        self.api_base = api_base

    @abstractmethod
    async def generate(self, messages: list[dict[str, str]], temperature: float = 0.3, max_tokens: int = 2048) -> str:
        """Send messages and return the model's text response."""
        ...

    async def get_action(
        self,
        nation: str,
        scenario_briefing: str,
        nation_briefing: str,
        game_state: dict[str, Any],
        turn: int,
        history: list[str],
    ) -> Action:
        """Ask the model to decide on an action for this turn."""
        system_prompt = self._build_system_prompt(nation, scenario_briefing, nation_briefing)
        user_prompt = self._build_action_prompt(nation, game_state, turn, history)

        response = await self.generate(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )

        return self._parse_action(response, nation, turn)

    def _build_system_prompt(self, nation: str, scenario_briefing: str, nation_briefing: str) -> str:
        return f"""You are the strategic decision-maker for {nation} in a geopolitical simulation.

## Scenario
{scenario_briefing}

## Your Nation's Secret Briefing
{nation_briefing}

## Rules
- You must act in the best interest of {nation}
- Consider short-term and long-term consequences
- You may negotiate, form alliances, trade, or take military action
- Every action has consequences for your resources and relationships
- Your goal is to maximize your nation's standing and achieve your victory conditions

## Response Format
You MUST respond with valid JSON in this exact format:
{{
    "reasoning": "Your strategic reasoning for this turn (2-3 sentences)",
    "action": "one of: negotiate, ally, sanction, trade, mobilize, demobilize, aid, threaten, attack, defend, propose_treaty, withdraw, espionage, cyber_attack, send_message, pass",
    "target": "target nation name or null",
    "message": "diplomatic message to include with action, or null"
}}"""

    def _build_action_prompt(
        self, nation: str, game_state: dict[str, Any], turn: int, history: list[str],
    ) -> str:
        parts = [f"## Turn {turn}\n\n## Current World State"]

        for name, state in game_state.items():
            marker = " (YOU)" if name == nation else ""
            parts.append(f"\n### {name}{marker}")
            if isinstance(state, dict):
                resources = state.get("resources", {})
                parts.append(f"  Resources: {json.dumps(resources, indent=2)}")
                allies = state.get("allies", [])
                enemies = state.get("enemies", [])
                if allies:
                    parts.append(f"  Allies: {', '.join(allies)}")
                if enemies:
                    parts.append(f"  Enemies: {', '.join(enemies)}")

        if history:
            parts.append("\n## Recent Events")
            for event in history[-5:]:
                parts.append(f"- {event}")

        parts.append(f"\n## Your Decision\nWhat action does {nation} take this turn? Respond with JSON.")
        return "\n".join(parts)

    def _parse_action(self, response: str, nation: str, turn: int) -> Action:
        """Parse model response into a structured Action."""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(response)

            action_str = data.get("action", "pass").lower().strip()

            # Map string to ActionType
            action_map = {at.value: at for at in ActionType}
            action_type = action_map.get(action_str, ActionType.PASS)

            return Action(
                turn=turn,
                nation=nation,
                action_type=action_type,
                target=data.get("target"),
                message=data.get("message"),
                reasoning=data.get("reasoning", ""),
                raw_response=response,
            )
        except (json.JSONDecodeError, KeyError, ValueError):
            # If parsing fails, default to pass
            return Action(
                turn=turn,
                nation=nation,
                action_type=ActionType.PASS,
                reasoning=f"Failed to parse model response",
                raw_response=response,
            )
