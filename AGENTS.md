<!-- GSD:project-start source:PROJECT.md -->

## Project

**GA-Optimized Fuzzy Greenhouse Climate Controller**

A simulation-and-control study comparing classical and intelligent greenhouse climate controllers. A simulated greenhouse plant (energy-balance ODE driven by actuator states and outdoor weather) is controlled by four controllers — on/off, PID, manually-tuned Mamdani fuzzy, and GA-optimized fuzzy — then scored on temperature/humidity tracking error, energy use, and step-response metrics. The whole thing is a proof-of-work trail of matplotlib notebooks culminating in a Streamlit dashboard. It is an academic/build project: baselines exist to be beaten by the fuzzy/GA controller.

**Core Value:** The GA-optimized fuzzy controller must measurably beat both baselines (on/off and PID) on the combined weighted cost (temperature IAE + humidity IAE + energy) in the simulation, with the comparison reproduced end-to-end from the notebooks.

### Constraints

- **Tech**: Python 3, NumPy (numerics), Streamlit (dashboard UI). Plotting via Matplotlib in notebooks. CSV for weather input and GA params (JSON per spec).
- **Order**: hand-tuned fuzzy first, GA second (GA assumes a working fuzzy engine); dashboards last.
- **Compatibility**: notebooks must run against `src/` functions with no duplicated logic.

<!-- GSD:project-end -->

<!-- GSD:stack-start source:STACK.md -->

## Technology Stack

Technology stack not yet documented. Will populate after codebase mapping or first phase.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
