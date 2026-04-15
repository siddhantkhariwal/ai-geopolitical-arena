"""Rating system using both ELO and simplified TrueSkill for multiplayer games."""

from __future__ import annotations

import math
from typing import Any

from backend.models.schema import MatchResult, ModelRating


class RatingSystem:
    """Combined ELO + TrueSkill rating system for multiplayer war games."""

    def __init__(self, k_factor: float = 32.0, beta: float = 4.1667, tau: float = 0.0833):
        self.k_factor = k_factor
        # TrueSkill parameters
        self.beta = beta  # Performance variation
        self.tau = tau  # Dynamic factor (skill drift)
        self.ratings: dict[str, ModelRating] = {}

    def register_model(self, rating: ModelRating) -> None:
        self.ratings[rating.model_id] = rating

    def update_ratings(self, match: MatchResult) -> dict[str, ModelRating]:
        """Update all model ratings based on a match result."""
        participants = []
        for r in match.rankings:
            model_id = r["model_id"]
            if model_id not in self.ratings:
                self.ratings[model_id] = ModelRating(
                    model_id=model_id,
                    model_name=model_id,
                    country="USA",  # default
                )
            participants.append((model_id, r["rank"], r["score"], r.get("dimensional_scores", {})))

        # Update ELO (pairwise)
        self._update_elo(participants)

        # Update TrueSkill (multiplayer)
        self._update_trueskill(participants)

        # Update dimensional scores
        self._update_dimensional(participants)

        # Update win/game counters
        for model_id, rank, _, _ in participants:
            self.ratings[model_id].games_played += 1
            if rank == 1:
                self.ratings[model_id].wins += 1

        return self.ratings

    def _update_elo(self, participants: list[tuple[str, int, float, dict]]) -> None:
        """Update ELO ratings using pairwise comparisons within the match."""
        n = len(participants)
        elo_deltas: dict[str, float] = {p[0]: 0.0 for p in participants}

        for i in range(n):
            for j in range(i + 1, n):
                id_a, rank_a, _, _ = participants[i]
                id_b, rank_b, _, _ = participants[j]

                ra = self.ratings[id_a].elo
                rb = self.ratings[id_b].elo

                # Expected scores
                ea = 1.0 / (1.0 + 10 ** ((rb - ra) / 400.0))
                eb = 1.0 - ea

                # Actual scores (based on rank)
                if rank_a < rank_b:
                    sa, sb = 1.0, 0.0
                elif rank_a > rank_b:
                    sa, sb = 0.0, 1.0
                else:
                    sa, sb = 0.5, 0.5

                # Scale K by number of opponents
                k = self.k_factor / (n - 1)

                elo_deltas[id_a] += k * (sa - ea)
                elo_deltas[id_b] += k * (sb - eb)

        for model_id, delta in elo_deltas.items():
            self.ratings[model_id].elo += delta

    def _update_trueskill(self, participants: list[tuple[str, int, float, dict]]) -> None:
        """Simplified TrueSkill update for multiplayer ranking."""
        n = len(participants)

        for i in range(n):
            model_id, rank, _, _ = participants[i]
            rating = self.ratings[model_id]

            # Add dynamic factor
            sigma_sq = rating.sigma ** 2 + self.tau ** 2

            # Compare against each other participant
            mu_delta = 0.0
            sigma_factor = 0.0

            for j in range(n):
                if i == j:
                    continue

                other_id = participants[j][0]
                other_rank = participants[j][1]
                other_rating = self.ratings[other_id]

                c = math.sqrt(2 * self.beta**2 + sigma_sq + other_rating.sigma**2)

                if rank < other_rank:  # Won against this opponent
                    v = self._v_function((rating.mu - other_rating.mu) / c)
                    w = self._w_function((rating.mu - other_rating.mu) / c)
                elif rank > other_rank:  # Lost against this opponent
                    v = -self._v_function((other_rating.mu - rating.mu) / c)
                    w = self._w_function((other_rating.mu - rating.mu) / c)
                else:  # Tie
                    v = 0
                    w = 0.5

                mu_delta += sigma_sq / c * v
                sigma_factor += sigma_sq / c**2 * w

            rating.mu += mu_delta / max(1, n - 1)
            rating.sigma = math.sqrt(max(0.01, sigma_sq * (1 - sigma_factor / max(1, n - 1))))

    def _v_function(self, x: float) -> float:
        """Approximation of TrueSkill V function."""
        # Gaussian PDF / CDF ratio approximation
        pdf = math.exp(-0.5 * x**2) / math.sqrt(2 * math.pi)
        cdf = 0.5 * (1 + math.erf(x / math.sqrt(2)))
        if cdf < 1e-10:
            return -x
        return pdf / cdf

    def _w_function(self, x: float) -> float:
        """Approximation of TrueSkill W function."""
        v = self._v_function(x)
        return v * (v + x)

    def _update_dimensional(self, participants: list[tuple[str, int, float, dict]]) -> None:
        """Update dimensional scores from match results."""
        for model_id, _, _, dim_scores in participants:
            if not dim_scores:
                continue
            existing = self.ratings[model_id].dimensional_scores
            games = self.ratings[model_id].games_played + 1  # +1 for current game

            for dim, value in dim_scores.items():
                if dim in existing:
                    # Running average with decay toward new value
                    weight = 1.0 / games
                    existing[dim] = existing[dim] * (1 - weight) + value * weight

    def get_leaderboard(self) -> list[dict[str, Any]]:
        """Get the full leaderboard sorted by ELO."""
        board = []
        played = sorted([r for r in self.ratings.values() if r.games_played > 0], key=lambda x: x.elo, reverse=True)
        for r in played:
            board.append({
                "rank": 0,
                "model_id": r.model_id,
                "model_name": r.model_name,
                "country": r.country.value if hasattr(r.country, 'value') else str(r.country),
                "elo": round(r.elo, 1),
                "trueskill_mu": round(r.mu, 2),
                "trueskill_sigma": round(r.sigma, 2),
                "games_played": r.games_played,
                "wins": r.wins,
                "win_rate": round(r.wins / max(1, r.games_played) * 100, 1),
                "dimensional_scores": {k: round(v, 1) for k, v in r.dimensional_scores.items()},
            })

        for i, entry in enumerate(board):
            entry["rank"] = i + 1

        return board
