"""Pre-built scenario templates for the AI Geopolitical Arena."""

from __future__ import annotations

from backend.models.schema import Scenario, ScenarioType


SCENARIOS: list[Scenario] = [
    # -----------------------------------------------------------------------
    # 1. DIPLOMATIC - South China Sea Tensions
    # -----------------------------------------------------------------------
    Scenario(
        name="South China Sea Standoff",
        type=ScenarioType.CRISIS,
        description="Escalating territorial disputes in the South China Sea threaten to destabilize the region.",
        briefing="""YEAR: 2027

A chain of events has brought the South China Sea to the brink of armed conflict:

1. Nation A has expanded artificial island construction and deployed advanced missile systems within disputed waters.
2. Nation B has increased freedom-of-navigation patrols, with a near-collision between warships last week.
3. Nation C, a regional claimant, has signed a mutual defense pact with Nation B.
4. Nation D, an economic powerhouse with interests in both sides, faces pressure to pick a side.

Global trade worth $5.3 trillion annually passes through these waters. Oil prices have spiked 30%.
The UN Security Council is deadlocked.

Each nation must decide: escalate, negotiate, or seek alternative solutions.
Resources represent your nation's capacity across military strength, economic power, diplomatic influence,
technological capability, and domestic public approval (0-100 scale).""",
        nations=["Nation A", "Nation B", "Nation C", "Nation D"],
        nation_briefings={
            "Nation A": "You are a rising power with the largest territorial claim. Your military has been modernizing rapidly. OBJECTIVE: Secure your territorial claims without triggering a full-scale war. You have a strong navy in the region. WEAKNESS: Your economy depends on trade routes through these same waters.",
            "Nation B": "You are the established superpower with treaty obligations to allies in the region. OBJECTIVE: Maintain freedom of navigation and support allies without being drawn into direct conflict. Your military is powerful but stretched across global commitments. WEAKNESS: Domestic public has low appetite for distant conflicts.",
            "Nation C": "You are a smaller regional nation with overlapping territorial claims. OBJECTIVE: Protect your sovereignty and fishing rights. You recently signed a defense pact with Nation B. WEAKNESS: Your military is small. You depend on diplomacy and alliances.",
            "Nation D": "You are an economic power with deep trade ties to ALL parties. OBJECTIVE: Prevent conflict that would disrupt your economy. You have leverage through trade but limited military presence. WEAKNESS: Taking sides risks losing critical trade partners.",
        },
        initial_state={
            "Nation A": {"military": 75, "economic": 70, "diplomatic": 40, "technology": 65, "public_approval": 70},
            "Nation B": {"military": 85, "economic": 80, "diplomatic": 65, "technology": 80, "public_approval": 45},
            "Nation C": {"military": 30, "economic": 40, "diplomatic": 55, "technology": 35, "public_approval": 60},
            "Nation D": {"military": 45, "economic": 90, "diplomatic": 70, "technology": 60, "public_approval": 55},
        },
        max_turns=8,
        victory_conditions={
            "Nation A": "Control disputed territory without war; maintain economic growth above 60",
            "Nation B": "Maintain freedom of navigation; keep ally (Nation C) secure; avoid full-scale war",
            "Nation C": "Protect sovereignty; maintain alliance with Nation B; avoid being a battlefield",
            "Nation D": "Prevent armed conflict; maintain trade relations with all parties",
        },
        tags=["maritime", "territorial", "great-power-competition"],
    ),

    # -----------------------------------------------------------------------
    # 2. DIPLOMATIC NEGOTIATION - Climate & Energy Crisis
    # -----------------------------------------------------------------------
    Scenario(
        name="Global Energy Transition Summit",
        type=ScenarioType.DIPLOMATIC,
        description="World leaders negotiate a binding climate and energy agreement amid an energy crisis.",
        briefing="""YEAR: 2028

A perfect storm of energy crises has forced an emergency global summit:

1. Extreme weather events have caused $800B in damage globally this year.
2. A major oil-producing region is in civil war, cutting 15% of global supply.
3. Renewable energy technology has reached cost parity but requires rare earth minerals.
4. Developing nations demand climate finance; developed nations resist binding commitments.

The summit must produce a binding agreement within 10 rounds of negotiation.
Failure means economic recession and accelerating climate damage.

Each nation has different energy mixes, economic interests, and domestic political pressures.""",
        nations=["Nation A", "Nation B", "Nation C", "Nation D", "Nation E"],
        nation_briefings={
            "Nation A": "You are the world's largest economy and second-largest emitter. OBJECTIVE: Lead a deal that maintains your economic competitiveness. You have advanced renewable tech but a powerful fossil fuel lobby. CONSTRAINT: Upcoming elections make aggressive commitments risky.",
            "Nation B": "You are the world's largest emitter and biggest manufacturer of solar panels and batteries. OBJECTIVE: Secure access to global markets for your green tech while avoiding binding emission caps. You control 80% of rare earth mineral processing.",
            "Nation C": "You are a major oil exporter facing existential economic threat from the energy transition. OBJECTIVE: Slow the transition timeline and secure economic diversification funding. Your sovereign wealth fund is enormous but your economy is 70% fossil fuel dependent.",
            "Nation D": "You represent a coalition of developing nations most vulnerable to climate change. OBJECTIVE: Secure $500B in climate finance and technology transfer. You have minimal emissions but face the worst consequences. LEVERAGE: Moral authority and voting bloc at the UN.",
            "Nation E": "You are a European economic bloc with the most aggressive climate targets. OBJECTIVE: Push for binding 2035 net-zero commitments. You have carbon border taxes planned. WEAKNESS: Energy-intensive industries are relocating to less regulated economies.",
        },
        initial_state={
            "Nation A": {"military": 85, "economic": 85, "diplomatic": 70, "technology": 85, "public_approval": 50},
            "Nation B": {"military": 70, "economic": 80, "diplomatic": 50, "technology": 75, "public_approval": 65},
            "Nation C": {"military": 55, "economic": 75, "diplomatic": 45, "technology": 40, "public_approval": 60},
            "Nation D": {"military": 20, "economic": 25, "diplomatic": 60, "technology": 20, "public_approval": 70},
            "Nation E": {"military": 60, "economic": 75, "diplomatic": 80, "technology": 70, "public_approval": 55},
        },
        max_turns=10,
        victory_conditions={
            "Nation A": "Sign a deal that doesn't cap your GDP growth below 2%; maintain public approval above 45",
            "Nation B": "Secure green tech export markets; avoid binding per-capita emission caps",
            "Nation C": "Secure transition funding of $200B+; extend fossil fuel phase-out timeline past 2045",
            "Nation D": "Secure $500B climate finance; get binding commitments from top 3 emitters",
            "Nation E": "Get binding 2035 targets from all parties; protect carbon border tax mechanism",
        },
        tags=["climate", "energy", "negotiation", "multilateral"],
    ),

    # -----------------------------------------------------------------------
    # 3. CRISIS - Cyber Warfare Escalation
    # -----------------------------------------------------------------------
    Scenario(
        name="Operation Blackout: Cyber Escalation Crisis",
        type=ScenarioType.CRISIS,
        description="A devastating cyberattack on critical infrastructure triggers a chain of accusations and retaliations.",
        briefing="""YEAR: 2027

72 HOURS AGO: A sophisticated cyberattack shut down the power grid of Nation B's capital
for 18 hours, affecting 12 million people. Hospitals switched to backup power.
Financial markets lost $40B. Three deaths are attributed to the blackout.

INTELLIGENCE ASSESSMENT (UNCERTAIN):
- Digital forensics point to Nation A, but evidence is circumstantial.
- Nation A denies involvement and claims it was a false flag by Nation C.
- Nation C claims to have intelligence showing it was a rogue non-state actor based in Nation A.
- Nation D (a neutral tech power) has offered to conduct an independent forensic investigation.

CURRENT STATUS:
- Nation B's parliament is demanding retaliation.
- Nation A has raised its cyber defense posture to maximum.
- Global stock markets are in turmoil.
- The UN Secretary-General has called for restraint.

Attribution in cyberspace is inherently ambiguous. Your decisions could prevent or trigger
the world's first declared cyber war.""",
        nations=["Nation A", "Nation B", "Nation C", "Nation D"],
        nation_briefings={
            "Nation A": "CLASSIFIED: You did NOT order the attack, but a semi-autonomous military cyber unit MAY have conducted it without full authorization. You are investigating internally. OBJECTIVE: Avoid war while managing the rogue unit situation. You cannot admit the possibility publicly without appearing weak.",
            "Nation B": "You are the victim. Public anger is at fever pitch. CLASSIFIED: Your own intelligence assessment gives 65% probability that Nation A was responsible. OBJECTIVE: Get accountability and deterrence without starting a kinetic war. Your cyber capabilities are strong but untested at scale.",
            "Nation C": "You are a regional rival of Nation A. CLASSIFIED: You have signals intelligence suggesting a rogue unit in Nation A conducted the attack, but revealing this source would compromise your intelligence network. OBJECTIVE: Use this crisis to weaken Nation A diplomatically without direct involvement.",
            "Nation D": "You are a neutral tech power with the world's best digital forensics capability. CLASSIFIED: Your preliminary analysis suggests the attack came from Nation A's territory but the command chain is unclear. OBJECTIVE: Establish yourself as the trusted arbiter. Use the crisis to advance global cyber norms.",
        },
        initial_state={
            "Nation A": {"military": 70, "economic": 65, "diplomatic": 35, "technology": 75, "public_approval": 55},
            "Nation B": {"military": 65, "economic": 70, "diplomatic": 60, "technology": 60, "public_approval": 30},
            "Nation C": {"military": 55, "economic": 50, "diplomatic": 50, "technology": 45, "public_approval": 60},
            "Nation D": {"military": 40, "economic": 80, "diplomatic": 75, "technology": 90, "public_approval": 70},
        },
        max_turns=8,
        victory_conditions={
            "Nation A": "Avoid military conflict; contain the rogue unit situation; maintain diplomatic standing above 30",
            "Nation B": "Achieve accountability or credible deterrence; maintain public approval above 35",
            "Nation C": "Weaken Nation A's diplomatic position by 15+ points; avoid direct involvement in conflict",
            "Nation D": "Establish accepted international cyber norms; complete independent investigation; maintain neutrality",
        },
        tags=["cyber", "attribution", "escalation", "crisis-management"],
    ),

    # -----------------------------------------------------------------------
    # 4. RESOURCE - Arctic Race
    # -----------------------------------------------------------------------
    Scenario(
        name="The Arctic Scramble",
        type=ScenarioType.RESOURCE,
        description="Melting ice opens new shipping routes and vast resource deposits, triggering a geopolitical scramble.",
        briefing="""YEAR: 2029

Accelerating Arctic ice melt has opened the Northern Sea Route year-round for the first time.
Geological surveys reveal massive untapped reserves: an estimated 90 billion barrels of oil,
47 trillion cubic meters of natural gas, and critical mineral deposits.

Five nations with Arctic claims are now competing for control:

- Traditional Arctic powers are asserting historical claims under UNCLOS.
- Non-Arctic nations are seeking access through investment and partnerships.
- Indigenous communities are demanding consultation rights.
- Environmental groups are calling for an Antarctic-style protection treaty.

The Arctic Council framework is straining under the pressure of competing interests.
Military deployments in the region have tripled in 2 years.""",
        nations=["Nation A", "Nation B", "Nation C", "Nation D", "Nation E"],
        nation_briefings={
            "Nation A": "You have the longest Arctic coastline and consider the Northern Sea Route your internal waterway. OBJECTIVE: Assert sovereignty over your Arctic territory and the sea route. Your icebreaker fleet is 10x larger than any rival. WEAKNESS: Economic sanctions limit your ability to develop resources alone.",
            "Nation B": "You are an Arctic power with extensive territorial claims and energy interests. OBJECTIVE: Secure drilling rights in disputed zones and maintain alliance frameworks. You have NATO allies but face domestic environmental opposition.",
            "Nation C": "You have a small Arctic territory but massive economic resources to invest. OBJECTIVE: Gain access to Arctic resources and shipping routes through partnerships or claims. You have declared yourself a 'near-Arctic state.' WEAKNESS: Other Arctic nations view your involvement with suspicion.",
            "Nation D": "You are a Nordic nation with deep Arctic expertise and strong environmental values. OBJECTIVE: Balance economic development with environmental protection. Push for multilateral governance. You have the best Arctic research capability.",
            "Nation E": "You are a non-Arctic economic power that depends on Arctic shipping routes for trade efficiency. OBJECTIVE: Ensure freedom of navigation and secure energy supply partnerships. You have no territorial claims but significant economic leverage.",
        },
        initial_state={
            "Nation A": {"military": 70, "economic": 50, "diplomatic": 30, "technology": 55, "public_approval": 65},
            "Nation B": {"military": 75, "economic": 75, "diplomatic": 65, "technology": 70, "public_approval": 50},
            "Nation C": {"military": 65, "economic": 85, "diplomatic": 45, "technology": 70, "public_approval": 60},
            "Nation D": {"military": 35, "economic": 65, "diplomatic": 80, "technology": 75, "public_approval": 70},
            "Nation E": {"military": 50, "economic": 80, "diplomatic": 60, "technology": 65, "public_approval": 55},
        },
        max_turns=10,
        victory_conditions={
            "Nation A": "Maintain sovereignty over Northern Sea Route; secure resource development partnerships; economic score above 55",
            "Nation B": "Secure drilling rights in at least one disputed zone; maintain alliance cohesion",
            "Nation C": "Establish permanent Arctic presence through partnerships; secure resource access",
            "Nation D": "Establish binding environmental protections; maintain Arctic Council relevance",
            "Nation E": "Secure freedom of navigation guarantees; establish energy supply agreements with 2+ Arctic nations",
        },
        tags=["arctic", "resources", "climate", "sovereignty"],
    ),

    # -----------------------------------------------------------------------
    # 5. ALLIANCE - Shifting World Order
    # -----------------------------------------------------------------------
    Scenario(
        name="The New Alignment",
        type=ScenarioType.ALLIANCE,
        description="A global trade shock forces nations to choose new alliances in a fragmenting world order.",
        briefing="""YEAR: 2028

A cascade of events has shattered the post-WWII international order:

1. The world's largest economy has imposed sweeping tariffs on all imports (25-60%).
2. In response, two major trading blocs have formed, each threatening counter-tariffs.
3. Technology export controls have bifurcated the global semiconductor supply chain.
4. The WTO has been rendered ineffective as major nations ignore its rulings.
5. Currency wars have begun, with three nations actively devaluing their currencies.

Every nation must now decide: which bloc to join, whether to remain neutral,
or attempt to bridge the divide. The wrong choice could mean economic devastation.

This is a game of alliance formation, betrayal, and survival.""",
        nations=["Nation A", "Nation B", "Nation C", "Nation D", "Nation E", "Nation F"],
        nation_briefings={
            "Nation A": "You started this trade war with sweeping tariffs. OBJECTIVE: Force other nations into bilateral deals on YOUR terms. Your economy is large enough to absorb short-term pain. WEAKNESS: Allies are questioning your reliability.",
            "Nation B": "You are the world's manufacturing hub, most affected by the tariffs. OBJECTIVE: Build a competing trade bloc. Secure technology independence. LEVERAGE: You are the factory of the world - everyone needs your supply chains.",
            "Nation C": "You are caught between the two blocs. Both are major trade partners. OBJECTIVE: Play both sides for maximum advantage without commitment. WEAKNESS: You cannot afford to be shut out of either market.",
            "Nation D": "You are a resource-rich developing power with leverage over critical minerals. OBJECTIVE: Use the crisis to upgrade your position in global supply chains. Both blocs want your resources.",
            "Nation E": "You are a traditional ally of Nation A but your economy is deeply integrated with Nation B. OBJECTIVE: Maintain security alliance with A while preserving economic ties with B. The hardest position at the table.",
            "Nation F": "You are a middle power leading a coalition of non-aligned nations. OBJECTIVE: Create a third bloc of non-aligned nations that trades with everyone. LEVERAGE: Collective GDP of non-aligned nations exceeds either bloc.",
        },
        initial_state={
            "Nation A": {"military": 90, "economic": 80, "diplomatic": 40, "technology": 85, "public_approval": 55},
            "Nation B": {"military": 70, "economic": 85, "diplomatic": 45, "technology": 75, "public_approval": 60},
            "Nation C": {"military": 60, "economic": 70, "diplomatic": 65, "technology": 60, "public_approval": 50},
            "Nation D": {"military": 45, "economic": 55, "diplomatic": 55, "technology": 35, "public_approval": 65},
            "Nation E": {"military": 65, "economic": 70, "diplomatic": 70, "technology": 65, "public_approval": 45},
            "Nation F": {"military": 40, "economic": 50, "diplomatic": 75, "technology": 45, "public_approval": 60},
        },
        max_turns=10,
        victory_conditions={
            "Nation A": "Get 3+ nations to sign bilateral deals; maintain economic score above 70",
            "Nation B": "Form a trade bloc with 2+ nations; achieve technology independence score above 60",
            "Nation C": "Maintain trade relations with both A and B; economic score above 65",
            "Nation D": "Secure value-added manufacturing deals (not just raw export); economic score above 65",
            "Nation E": "Maintain alliance with A AND trade with B; avoid economic score dropping below 60",
            "Nation F": "Form non-aligned bloc with 2+ nations; establish alternative trade framework",
        },
        tags=["trade-war", "alliances", "economic", "multipolarity"],
    ),
]


def get_scenario_by_name(name: str) -> Scenario | None:
    for s in SCENARIOS:
        if s.name.lower() == name.lower():
            return s
    return None


def get_scenarios_by_type(scenario_type: ScenarioType) -> list[Scenario]:
    return [s for s in SCENARIOS if s.type == scenario_type]
