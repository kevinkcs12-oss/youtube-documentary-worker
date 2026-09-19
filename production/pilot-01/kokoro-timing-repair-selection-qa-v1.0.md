# Pilot 01 — Kokoro Timing Repair Selection QA Report v1.0

Date: 2026-09-19  
Voice: Kevin-selected Kokoro candidate 2, `am_michael`  
Timeline authority: 597.760 seconds / 91 canonical takes  
Verdict: `PASS_REPAIR_SELECTION_ONLY — INTAKE/CONFORM NOT YET RUN`

## Outcome

The evidence-protected v1.1 timing map reduces the timing problem to 17 affected takes. A deterministic repair-selection lot now contains exactly those 17 takes: 14 fact-preserving surgical rewrites and three existing adaptive takes assigned sub-100 ms editorial boundary transfers. The other 74 takes are unchanged.

This is not a canonical 91-take delivery, an intake pass, a narration conform, a mix, or release authority.

## Evidence-protected timing map

- 91/91 slots mapped against the frozen 597.760-second timeline.
- 26 evidence or chapter-transition intervals protected.
- 48.428 seconds of apparent timeline silence inspected; only 11.157 seconds classified as conservatively recoverable.
- 58 takes recover through safe trim plus unique silence at 1.00x.
- 16 more recover with their existing per-take adaptive setting, never above 1.15x.
- 17 required targeted repair selection.

## Selected repairs

### Surgical rewrites — 14

`T023, T025, T027, T037, T041, T045, T049, T052, T058, T062, T063, T064, T065, T082`

The first targeted generation pass repaired ten. A second pass regenerated only the four residual failures (`T023, T027, T037, T062`) and all four passed the planning timing gate. No global speed change occurred.

The rewrites preserve the material claim boundaries:

- probabilistic research language remains bounded;
- McDonald's statements remain company-authored case evidence;
- Spotify remains limited to familiarity, similarity, and discovery trade-offs;
- the feedback-loop mechanism remains explicitly the film's synthesis, not Spotify's finding;
- the conclusion remains case-linked and does not claim global prevalence.

### Editorial boundary transfers — 3

| Take | Borrowed | Donor | Repaired take headroom | Donor headroom after transfer |
|---|---:|---|---:|---:|
| T061 | 0.043 s | T062 | 0.100 s | 0.965 s |
| T074 | 0.056 s | T075 | 0.100 s | 0.436 s |
| T088 | 0.066 s | T089 | 0.100 s | 0.922 s |

Each transfer stays inside its current protected visual region. None crosses an evidence or chapter-transition boundary.

## Machine checks

- 17 manifest rows; 17 unique take IDs.
- Expected affected set matches exactly.
- 14 rewrite selections and three boundary transfers.
- 17/17 source WAV files exist, match their recorded SHA-256 values, and decode fully.
- Maximum selected per-take speed: 1.15x.
- 74 unaffected takes explicitly preserved.
- Manifest and summary are byte-identical after an independent rerun.
- `publishable=false`, `release_authorized=false`, `intake_passed=false`, and `conform_passed=false` remain fail-closed.

## Red-team findings

1. **False 91/91 completion risk:** a planning pass is not an authoritative intake or conform. Mitigation: the verdict is narrowly named `PASS_REPAIR_SELECTION_ONLY`; downstream authority flags remain false.
2. **Visual-semantic theft risk:** using all apparent gaps would consume evidence-reading or transition breathing room. Mitigation: the v1.1 map locks chapter bridges and all 26 protected visual intervals before allocating silence.
3. **Metric-gaming risk:** global acceleration could force nominal fit while degrading perceived quality. Mitigation: no global speed change; only existing bounded per-take settings are retained.
4. **Rewrite drift risk:** shortening could inflate causality or erase provenance caveats. Mitigation: all 14 rewritten claims were checked against the locked editorial rules; bounded attribution is retained.
5. **Donor starvation risk:** micro-transfers could create a new failure in the neighboring take. Mitigation: every donor retains more than 0.4 seconds of planning headroom after transfer.
6. **Container-versus-speech ambiguity:** retained WAV containers include leading/trailing silence and are not yet canonical trimmed 48 kHz/24-bit delivery files. Mitigation: do not run the final conform from this selection lot directly; first materialize the revised full 91-take set and pass the existing fail-closed intake.

## Next gate

Materialize a complete revised 91-take delivery from the selected sources, preserving lineage and the revised cue boundaries. Then run the authoritative intake and timing conform. Only a 91/91 pass may authorize assembly of the 597.760-second narration timeline and one full-film review candidate.

## Decision

`ITERATE` — retain `am_michael`; stop rewriting and global-speed experimentation; advance to canonical 91-take materialization and authoritative intake/conform.
