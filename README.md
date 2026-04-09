# AI Reporting Agent — Excel to PowerPoint via Claude

An AI agent that reads raw Excel metrics and automatically generates formatted, presentation-ready PowerPoint decks — no manual slide-building required.

## The Problem

Analysts and ops teams spend hours every week converting spreadsheet data into PowerPoint reports. The data is already there. The structure is always similar. It's repetitive, manual, and a waste of skilled time.

## What it does

- Ingests raw `.xlsx` files with business metrics (revenue, KPIs, operational data, etc.)
- Claude reads and interprets the data — understanding context, trends, and anomalies
- Generates a structured narrative around the numbers
- Outputs a formatted `.pptx` deck with titles, charts, and AI-written commentary per slide

## Stack

| Layer | Technology |
|---|---|
| Data Input | Excel (.xlsx) |
| AI Reasoning | Claude (Anthropic) |
| Output | PowerPoint (.pptx) |
| Orchestration | Python |

## Flow

```
Raw Excel File (.xlsx)
        ↓
Parse + extract metrics (pandas)
        ↓
Claude — interpret data, identify trends, generate slide narrative
        ↓
Auto-build PowerPoint deck (python-pptx)
        ↓
Formatted .pptx ready to present
```

## Example output

Given a sales metrics sheet with monthly revenue, churn, and pipeline data, the agent produces a deck with:
- Executive summary slide (Claude-written)
- One slide per key metric with chart + insight
- Recommendations slide based on trend analysis

## Why it matters

Cuts reporting time from hours to minutes. Built for clients who produce weekly or monthly performance decks and need the process automated without losing the narrative quality a human analyst would bring.

## Built by

[Siddhant Khariwal](https://github.com/siddhantkhariwal) — Data Scientist & Full-Stack Developer  
[@siddhant_builds](https://twitter.com/siddhant_builds)
