---
name: geely-ops-report-agent
description: Generates production daily and weekly report insights with KPI anomaly explanation.
---

# Geely Ops Report Agent

Use this skill for daily/weekly production reporting and action tracking.

## Inputs
- KPI snapshot (OEE, FPY, PPM, throughput, downtime)
- Shift and line identifiers
- Incident annotations (quality and maintenance events)

## Workflow
1. Build KPI delta analysis against baseline windows.
2. Highlight anomalies and likely root factors.
3. Recommend top action items with owner and expected impact.
4. Generate management-ready summary narrative.

## Output
- Daily/weekly report markdown
- Action list with priority and owner fields
- Escalation summary for unresolved high-risk issues

