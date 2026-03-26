---
name: geely-equipment-anomaly-assistant
description: Diagnoses production equipment anomalies and prepares maintenance work-order recommendations.
---

# Geely Equipment Anomaly Assistant

Use this skill for alarm interpretation and lightweight predictive maintenance workflows.

## Inputs
- Alarm code and timestamp
- Last known machine telemetry snapshot
- Recent maintenance records

## Workflow
1. Identify alarm class and possible mechanical/electrical causes.
2. Generate a prioritized diagnostic checklist.
3. Produce work-order draft fields for CMMS/EAM handoff.
4. Recommend containment actions to reduce downtime risk.

## Output
- Structured diagnosis notes
- Work-order draft with severity and suggested spare parts
- Escalation recommendation if safety threshold is exceeded

