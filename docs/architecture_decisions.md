# Architecture Decisions (ADR-lite)

## Decision: UI Technology for AS/400-style UX
Chosen: TUI (Textual/Rich) as primary UI adapter.

Alternatives evaluated
- TUI (Textual/Rich)
- Web (HTML/CSS/JS green screen)
- Desktop (Qt)

Advantages / disadvantages
- TUI
  - Pros: Highest fidelity to AS/400, fast keyboard workflows, low infra, runs over SSH, easy packaging.
  - Cons: Terminal dependency, limited graphical affordances, requires terminal sizing (24x80).
- Web
  - Pros: Easy distribution, browser accessibility, simpler onboarding.
  - Cons: Harder to mimic real terminal UX/latency, more front-end complexity, weaker keyboard-first flows.
- Desktop
  - Pros: Total control of UI/keyboard, stable layout, offline friendly.
  - Cons: Heavier distribution, higher maintenance, platform-specific issues.

Rationale
The product goal is AS/400-style productivity and keyboard-first operation. A TUI provides the closest interaction model with minimal infrastructure impact and keeps the UI as an external adapter to the core.

Implications
- UI lives in `src/infrastructure/CLI` (or `src/infrastructure/tui`).
- All UI logic depends on adapters/controllers; no domain or use case imports in UI except through adapters.
- Screen layout is constrained to 24x80 with explicit keyboard mappings.
