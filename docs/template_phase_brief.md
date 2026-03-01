# Phase [N]: [Title] (FR-[XXX])

**Status**: Draft | In Progress | Review | Complete
**Owner**: [Agent Name/User]

## 0. Live Loop State (Project Hierarchy)
- **L1 (Project Pillar)**: [e.g., Backtest Engine (Signal System)]
- **L2 Active Streams**: [Backend | Frontend/UI | Data | Ops]
- **L2 Deferred Streams**: [none or list]
- **L3 Stage Flow**: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
- **Active Stream**: [one stream]
- **Active Stage Level**: [L2 | L3 | L4]
- **Current Stage**: [Planning | Executing | Iterate Loop | Final Verification | CI/CD]
- **Planning Gate Boundary**: [what is in/out for selected stream]
- **Owner/Handoff**: [owner + downstream reviewer/implementer]
- **Acceptance Checks**: [tests/smoke checks required before stage advancement]
- **Primary Next Scope**: [one-line next action + rating + reason]
- **Secondary Next Scope (optional)**: [show only if certainty < 75 and rating diff < 20]

## 1. Problem Statement
- **Context**: What is broken or missing?
- **User Impact**: Why does this matter?

## 2. Goals & Non-Goals
- **Goal**: [e.g., Integrate Sector Data into Scanner]
- **Non-Goal**: [e.g., Real-time streaming sector updates]

## 3. Technical Specs
- **Data Layer**:
  - [e.g., New Parquet file: data/static/sector_map.parquet]
- **Strategy Layer**:
  - [e.g., Logic change in strategies/investor_cockpit.py]
- **UI Layer**:
  - [e.g., New column in Scanner View]

## 4. Acceptance Criteria (Testable)
- [ ] `pytest` passes for new logic.
- [ ] UI renders [X] without errors.
- [ ] Update time remains under [Y] seconds.

## 5. Rollback Plan
- **Trigger**: [e.g., App fails to load sector map]
- **Action**: Revert commit [X] or delete `sector_map.parquet`.
