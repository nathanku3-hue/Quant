# Dashboard Ops Relocation Policy

Status: DASH-0 planning-only ops policy
Authority: Phase 65 DASH-0
Date: 2026-05-10

## Purpose

Move operational diagnostics out of the main dashboard workflow in the future redesign. DASH-0 does not move runtime code.

## Ops Page

Target page:

```text
Settings & Ops
```

Contains:

- Data Health;
- Drift Monitor;
- diagnostics;
- refresh controls;
- runtime status;
- provenance/context checks;
- provider-gap reminders.

## Main-Cockpit Badges

Command Center may show compact badges only:

```text
Data Health: healthy/degraded
Drift: clear/yellow/red
Source Freshness: fresh/stale/unknown
Provider Gaps: count
```

Badges are navigation hints, not full workflows.

## Drift Monitor Relocation

Future runtime work should move the full Drift Monitor workflow to Settings & Ops.

Allowed outside Settings & Ops:

- one status badge;
- active issue count;
- link/navigation affordance to Settings & Ops.

Not allowed outside Settings & Ops:

- force drift check workflow;
- acknowledge/resolve controls;
- historical drift timeline;
- allocation drift heatmap.

## Data Health Relocation

Future runtime work should move full Data Health tables to Settings & Ops.

Allowed outside Settings & Ops:

- compact status badge;
- degraded signal count;
- stale-source count.

## Refresh Controls

Future runtime work should move broad refresh/diagnostic controls into Settings & Ops unless they are required for the current page's primary workflow.

## Boundary

Ops relocation does not authorize:

- alerts;
- broker calls;
- provider ingestion;
- source registry implementation;
- score/rank displays;
- buy/sell/hold outputs;
- action-state promotion.
