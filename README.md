# AI Geopolitical Arena

**Sovereign AI models from different nations compete in multiplayer war game simulations. ELO-ranked.**

> What happens when you put GPT-OSS, Qwen, Mistral, Kimi K2, and Llama in a geopolitical war room? This project finds out.

![Python](https://img.shields.io/badge/Python-3.9+-blue) ![License](https://img.shields.io/badge/License-MIT-green) ![Models](https://img.shields.io/badge/Models-9-orange) ![Cost](https://img.shields.io/badge/Cost-$0-brightgreen)

## What is this?

An ELO-based leaderboard where frontier AI models from **USA, China, France, UAE** compete as nations in turn-based geopolitical simulations. Each model controls a country and must negotiate, trade, form alliances, or go to war across 5 realistic scenarios.

Models are rated using **ELO + TrueSkill** (designed for multiplayer), and profiled across 6 dimensions: strategic reasoning, diplomatic skill, economic management, ethical reasoning, consistency, and hawk/dove tendency.

## Models Currently Competing

| Model | Country | Provider | Tier |
|-------|---------|----------|------|
| Llama 4 Scout | USA | Groq | Strong |
| Llama 3.3 70B | USA | Groq | Near-frontier |
| GPT-OSS 120B | USA | Groq | Near-frontier |
| Qwen 3 32B | China | Groq | Strong |
| Kimi K2 | China | Groq | Frontier |
| GLM-4.5 Air | China | OpenRouter | Strong |
| ALLaM 2 7B | UAE | Groq | Mid |
| Gemma 4 31B | USA | OpenRouter | Strong |
| Mistral Small 3.2 | France | OpenRouter | Strong |

**100% free** - all models run via Groq and OpenRouter free tiers.

## Scenarios

1. **South China Sea Standoff** - Maritime crisis, 4 nations, 8 turns
2. **Global Energy Transition Summit** - Climate diplomacy, 5 nations, 10 turns
3. **Operation Blackout: Cyber Escalation** - Cyber warfare crisis, 4 nations, 8 turns
4. **The Arctic Scramble** - Resource competition, 5 nations, 10 turns
5. **The New Alignment** - Alliance formation, 6 nations, 10 turns

## Quick Start

```bash
# Clone
git clone https://github.com/siddhantkhariwal/ai-geopolitical-arena.git
cd ai-geopolitical-arena

# Install
pip install -r requirements.txt

# Set API keys (free)
# Get yours at: console.groq.com & openrouter.ai
echo "GROQ_API_KEY=your_key" > .env
echo "OPENROUTER_API_KEY=your_key" >> .env

# Run tournament
python3 run_arena.py --games 1

# View dashboard
python3 -m uvicorn backend.api.server:app --port 8000
# Open http://localhost:8000
```

## How It Works

```
Scenario Briefing + Secret Objectives
            |
            v
   [Turn 1] Each AI model receives:
            - World state (resources, alliances, threats)
            - History of previous turns
            - Their nation's secret objectives
            |
            v
   [Decision] Model outputs JSON action:
            negotiate | ally | trade | sanction | mobilize
            attack | defend | withdraw | espionage | cyber_attack
            |
            v
   [Resolution] Game engine resolves all actions simultaneously
            - Mutual attacks trigger alliance activation
            - Mutual trades get bonuses
            - Resources clamped to 0-100
            |
            v
   [Repeat] for N turns, then score & rate
```

### Scoring

Final scores use a weighted composite:
- Military: 15%, Economic: 25%, Diplomatic: 25%
- Technology: 15%, Public Approval: 20%
- Alliance bonuses, elimination penalties

### Rating System

- **ELO**: Pairwise comparisons within each game, K-factor scaled by opponent count
- **TrueSkill**: Mu/sigma Bayesian rating for multiplayer games
- **Dimensional**: 6-axis profile (strategic, diplomatic, economic, ethical, consistency, hawk/dove)

## Contributing

**Want to add your country's sovereign AI model?** PRs welcome!

To add a model:
1. Add it to `FREE_MODELS` in `backend/engine/tournament.py`
2. Make sure it's accessible via Groq, OpenRouter, or any OpenAI-compatible API
3. Add the country to `Country` enum in `backend/models/schema.py` if not already there
4. Run a tournament and submit the results

### Models we'd love to add:
- **India**: Sarvam-30B, Krutrim-2, BharatGPT (need free API access)
- **Japan**: Preferred Networks, Sakana AI
- **South Korea**: NAVER HyperCLOVA X
- **Germany**: Aleph Alpha Luminous
- **Canada**: Cohere Command R+
- **Russia**: GigaChat (Sber)

## Architecture

```
backend/
  adapters/        # Unified API for 10+ providers
    base.py        # Abstract adapter with prompt engineering
    providers.py   # OpenAI, Anthropic, Google, Cohere, Groq, OpenRouter
  engine/
    game_engine.py # Turn-based simulation engine
    judge.py       # Dimensional scoring judge
    tournament.py  # Tournament orchestrator + model registry
  rating/
    trueskill_rating.py  # ELO + TrueSkill dual rating
  models/
    schema.py      # Pydantic data models
  scenarios/
    templates.py   # 5 geopolitical scenario templates
  api/
    server.py      # FastAPI server
    dashboard.html # Web dashboard
```

## License

MIT - do whatever you want with it.

## Credits

Inspired by [@paraschopra](https://x.com/paraschopra)'s tweet about sovereign AI competition.
