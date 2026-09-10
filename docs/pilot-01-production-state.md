# Pilot 01 Production State

Canonical title: **Why Does Everything Look the Same Now?**

Current canonical editorial baseline:
- Master script v1.1
- Full animatic v1.1 runtime: 10:22
- Retention-test branch v1.2: 10:02, reversible and not canonical
- Eight-sequence structure
- Layer C production worker and CI validated

Current real-asset gate:
- Sequence 1 opening v1.1 is technically validated at exactly 64.000 seconds / 1,600 frames after corrective commit `fe14361cd595b6e54889cf5b55a4cfb4ba9c53d6`.
- The workflow now asserts runtime and frame count and persists SHA-256 for all seven Pexels source masters.
- The earlier green workflow artifact was rejected after binary QA found only 60.000 seconds / 1,500 frames.
- Opening v1.1 is not picture-locked: the bookstore occupies 17 seconds across three scenes, visible fascia and recognizable pedestrians require mitigation, the real phone UI is a weak and rights-ambiguous proxy, and the final bookstore repeat is a weak transition into the Axalta evidence.

Next production gate:
- Build a reversible opening v1.2 rights-safe conform that preserves the exact 64-second narration timing and the illustration-versus-evidence guardrail.
- Replace the real phone UI with original deterministic interface graphics.
- Reduce the bookstore to at most two motivated appearances, reframe or mask fascia/pedestrians, and replace the final four-second repeat with a clean Axalta bridge.
- After this gate passes, resume the whole-pilot v1.2b natural-cadence microcuts.

Layer C should ingest a repository-relative JSON manifest and render only assets that are explicitly staged in the job directory. No paid APIs, external publishing, or secrets are required.
