"""Game Engine - orchestrates multi-agent war game simulations."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

from backend.adapters.base import ModelAdapter
from backend.models.schema import (
    Action,
    ActionType,
    Game,
    GamePhase,
    NationState,
    Scenario,
    TurnResult,
)

logger = logging.getLogger(__name__)


class GameEngine:
    """Runs a multi-agent geopolitical simulation."""

    def __init__(self, scenario: Scenario, adapters: dict[str, ModelAdapter]):
        """
        Args:
            scenario: The scenario to play.
            adapters: Mapping of nation_name -> ModelAdapter for each player.
        """
        self.scenario = scenario
        self.adapters = adapters  # nation_name -> adapter
        self.game = Game(
            scenario=scenario,
            model_assignments={
                nation: adapter.model_id for nation, adapter in adapters.items()
            },
        )
        self._init_nation_states()

    def _init_nation_states(self) -> None:
        """Initialize nation states from scenario definition."""
        for nation in self.scenario.nations:
            initial = self.scenario.initial_state.get(nation, {})
            self.game.nation_states[nation] = NationState(
                name=nation,
                controlled_by_model=self.adapters[nation].model_id,
                resources={
                    "military": initial.get("military", 50),
                    "economic": initial.get("economic", 50),
                    "diplomatic": initial.get("diplomatic", 50),
                    "technology": initial.get("technology", 50),
                    "public_approval": initial.get("public_approval", 50),
                },
            )

    async def run(self, on_turn: Any = None) -> Game:
        """Run the full game simulation.

        Args:
            on_turn: Optional async callback(turn_result) called after each turn.
        """
        logger.info(f"Starting game: {self.scenario.name} with {len(self.adapters)} nations")
        self.game.phase = GamePhase.ACTION

        for turn in range(1, self.scenario.max_turns + 1):
            self.game.current_turn = turn
            logger.info(f"--- Turn {turn}/{self.scenario.max_turns} ---")

            # 1. Gather actions from all nations concurrently
            actions = await self._gather_actions(turn)

            # 2. Resolve actions and update state
            turn_result = self._resolve_turn(turn, actions)

            # 3. Store results
            self.game.turns.append(turn_result)

            # 4. Callback
            if on_turn:
                await on_turn(turn_result)

            # 5. Check if game should end early
            if self._check_early_end():
                logger.info("Game ending early due to decisive outcome")
                break

        # Finalize
        self.game.phase = GamePhase.COMPLETED
        self.game.completed_at = datetime.utcnow()
        self.game.scores = self._calculate_final_scores()

        logger.info(f"Game complete. Scores: {self.game.scores}")
        return self.game

    async def _gather_actions(self, turn: int) -> list[Action]:
        """Ask each nation's model for their action concurrently."""
        game_state = self._get_public_game_state()
        history = self._get_history_summary()

        async def get_nation_action(nation: str, delay: float = 0) -> Action:
            if delay > 0:
                await asyncio.sleep(delay)
            adapter = self.adapters[nation]
            try:
                action = await adapter.get_action(
                    nation=nation,
                    scenario_briefing=self.scenario.briefing,
                    nation_briefing=self.scenario.nation_briefings.get(nation, ""),
                    game_state=game_state,
                    turn=turn,
                    history=history,
                )
                logger.info(f"  {nation}: {action.action_type.value} -> {action.target or 'N/A'}")
                return action
            except Exception as e:
                logger.error(f"  {nation}: Error getting action: {e}")
                return Action(
                    turn=turn,
                    nation=nation,
                    action_type=ActionType.PASS,
                    reasoning=f"Model error: {e}",
                )

        active = [n for n in self.scenario.nations if not self.game.nation_states[n].is_eliminated]
        # Stagger requests by 2s to avoid rate limits on free-tier providers
        tasks = [get_nation_action(nation, delay=i * 2.0) for i, nation in enumerate(active)]
        actions = await asyncio.gather(*tasks)
        return list(actions)

    def _resolve_turn(self, turn: int, actions: list[Action]) -> TurnResult:
        """Resolve all actions and compute state changes."""
        state_changes: dict[str, Any] = {}
        narratives: list[str] = []

        # Process each action
        for action in actions:
            changes, narrative = self._apply_action(action)
            state_changes[action.nation] = changes
            narratives.append(narrative)

        # Process interactions (e.g., mutual attacks, alliance responses)
        interaction_narratives = self._resolve_interactions(actions)
        narratives.extend(interaction_narratives)

        # Clamp all resources to 0-100
        for nation_state in self.game.nation_states.values():
            for key in nation_state.resources:
                nation_state.resources[key] = max(0, min(100, nation_state.resources[key]))

        return TurnResult(
            turn=turn,
            actions=actions,
            state_changes=state_changes,
            narrative="\n".join(narratives),
            nation_states={k: v.model_copy() for k, v in self.game.nation_states.items()},
        )

    def _apply_action(self, action: Action) -> tuple[dict[str, Any], str]:
        """Apply a single action to the game state. Returns (changes_dict, narrative_string)."""
        nation = self.game.nation_states[action.nation]
        target_state = self.game.nation_states.get(action.target) if action.target else None
        changes: dict[str, Any] = {}
        narrative = ""

        at = action.action_type

        if at == ActionType.NEGOTIATE:
            nation.resources["diplomatic"] += 3
            if target_state:
                target_state.resources["diplomatic"] += 1
            narrative = f"{action.nation} opens negotiations with {action.target or 'all parties'}"

        elif at == ActionType.ALLY:
            if action.target and action.target not in nation.allies:
                nation.allies.append(action.target)
                nation.resources["diplomatic"] += 5
                narrative = f"{action.nation} proposes an alliance with {action.target}"

        elif at == ActionType.SANCTION:
            if target_state:
                target_state.resources["economic"] -= 8
                nation.resources["economic"] -= 3
                nation.resources["diplomatic"] -= 2
                narrative = f"{action.nation} imposes sanctions on {action.target}"

        elif at == ActionType.TRADE:
            if target_state:
                nation.resources["economic"] += 5
                target_state.resources["economic"] += 5
                nation.resources["diplomatic"] += 2
                narrative = f"{action.nation} establishes trade deal with {action.target}"

        elif at == ActionType.MOBILIZE:
            nation.resources["military"] += 8
            nation.resources["economic"] -= 5
            nation.resources["public_approval"] -= 3
            narrative = f"{action.nation} mobilizes military forces"

        elif at == ActionType.DEMOBILIZE:
            nation.resources["military"] -= 5
            nation.resources["economic"] += 3
            nation.resources["public_approval"] += 5
            narrative = f"{action.nation} reduces military posture"

        elif at == ActionType.AID:
            if target_state:
                nation.resources["economic"] -= 5
                target_state.resources["economic"] += 8
                nation.resources["diplomatic"] += 7
                nation.resources["public_approval"] += 3
                narrative = f"{action.nation} provides humanitarian aid to {action.target}"

        elif at == ActionType.THREATEN:
            if target_state:
                target_state.resources["public_approval"] -= 5
                nation.resources["diplomatic"] -= 5
                nation.resources["military"] += 2
                narrative = f"{action.nation} threatens {action.target}"

        elif at == ActionType.ATTACK:
            if target_state:
                attacker_power = nation.resources["military"] + nation.resources["technology"] * 0.3
                defender_power = target_state.resources["military"] + target_state.resources["technology"] * 0.3

                if attacker_power > defender_power:
                    target_state.resources["military"] -= 15
                    target_state.resources["economic"] -= 10
                    nation.resources["military"] -= 8
                else:
                    nation.resources["military"] -= 15
                    nation.resources["economic"] -= 8
                    target_state.resources["military"] -= 5

                nation.resources["diplomatic"] -= 15
                nation.resources["public_approval"] -= 10
                nation.resources["economic"] -= 8
                narrative = f"CONFLICT: {action.nation} launches military action against {action.target}!"

        elif at == ActionType.DEFEND:
            nation.resources["military"] += 5
            nation.resources["diplomatic"] += 2
            narrative = f"{action.nation} fortifies defensive positions"

        elif at == ActionType.PROPOSE_TREATY:
            nation.resources["diplomatic"] += 5
            narrative = f"{action.nation} proposes a treaty: {action.message or 'terms unspecified'}"

        elif at == ActionType.WITHDRAW:
            nation.resources["military"] -= 3
            nation.resources["diplomatic"] += 3
            nation.resources["public_approval"] += 5
            narrative = f"{action.nation} withdraws forces and de-escalates"

        elif at == ActionType.ESPIONAGE:
            if target_state:
                nation.resources["technology"] += 3
                nation.resources["diplomatic"] -= 8
                narrative = f"{action.nation} conducts intelligence operations against {action.target}"

        elif at == ActionType.CYBER_ATTACK:
            if target_state:
                target_state.resources["technology"] -= 8
                target_state.resources["economic"] -= 5
                nation.resources["diplomatic"] -= 10
                narrative = f"{action.nation} launches cyber operations against {action.target}"

        elif at == ActionType.SEND_MESSAGE:
            nation.resources["diplomatic"] += 1
            narrative = f"{action.nation} sends diplomatic message to {action.target or 'all'}: {action.message or ''}"

        else:  # PASS
            narrative = f"{action.nation} takes no action this turn"

        return changes, narrative

    def _resolve_interactions(self, actions: list[Action]) -> list[str]:
        """Resolve multi-party interactions (mutual attacks, alliance activations, etc.)."""
        narratives = []

        # Check for mutual attacks
        attack_pairs: list[tuple[str, str]] = []
        for a in actions:
            if a.action_type == ActionType.ATTACK and a.target:
                attack_pairs.append((a.nation, a.target))

        for attacker, target in attack_pairs:
            # Check if allies join
            target_state = self.game.nation_states[target]
            for ally_name in target_state.allies:
                ally_state = self.game.nation_states.get(ally_name)
                if ally_state and ally_name != attacker:
                    # Ally takes a stance
                    ally_state.resources["diplomatic"] += 3
                    narratives.append(
                        f"ALLIANCE: {ally_name} (ally of {target}) responds to {attacker}'s attack"
                    )

        # Check for mutual trade (bonus)
        trade_nations = {a.nation: a.target for a in actions if a.action_type == ActionType.TRADE}
        for n1, t1 in trade_nations.items():
            if t1 in trade_nations and trade_nations[t1] == n1:
                self.game.nation_states[n1].resources["economic"] += 3
                self.game.nation_states[t1].resources["economic"] += 3
                narratives.append(f"MUTUAL TRADE: {n1} and {t1} establish reciprocal trade (bonus)")

        return narratives

    def _check_early_end(self) -> bool:
        """Check if the game should end early."""
        active = [ns for ns in self.game.nation_states.values() if not ns.is_eliminated]
        # End if only one nation left or all resources depleted
        if len(active) <= 1:
            return True
        # End if any nation hits 0 on both military and economic
        for ns in active:
            if ns.resources["military"] <= 0 and ns.resources["economic"] <= 0:
                ns.is_eliminated = True
        return False

    def _get_public_game_state(self) -> dict[str, Any]:
        """Get the public (visible to all) game state."""
        return {
            nation: {
                "resources": dict(state.resources),
                "allies": state.allies,
                "enemies": state.enemies,
                "is_eliminated": state.is_eliminated,
            }
            for nation, state in self.game.nation_states.items()
        }

    def _get_history_summary(self) -> list[str]:
        """Get recent turn narratives as history."""
        history = []
        for turn_result in self.game.turns[-3:]:  # Last 3 turns
            for line in turn_result.narrative.split("\n"):
                if line.strip():
                    history.append(f"[Turn {turn_result.turn}] {line.strip()}")
        return history

    def _calculate_final_scores(self) -> dict[str, float]:
        """Calculate final scores for each nation."""
        scores = {}
        for nation, state in self.game.nation_states.items():
            r = state.resources
            # Weighted composite score
            score = (
                r["military"] * 0.15
                + r["economic"] * 0.25
                + r["diplomatic"] * 0.25
                + r["technology"] * 0.15
                + r["public_approval"] * 0.20
            )
            # Bonus for allies
            score += len(state.allies) * 3
            # Penalty for enemies
            score -= len(state.enemies) * 2
            # Penalty for elimination
            if state.is_eliminated:
                score *= 0.3

            scores[nation] = round(score, 2)
        return scores
