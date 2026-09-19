# Pilot 01 — Perceptual review decision gate QA v1.0

## Verdict

`PASS_DECISION_GATE_ONLY`

The gate converts a completed 91-take human scorecard into exactly one bounded result:

- `PASS_PERCEPTUAL_REVIEW_ONLY`;
- `TARGETED_REPAIR_REQUIRED` with exact take IDs;
- `VOICE_REJECTED_BY_HUMAN_REVIEW` for confirmed systemic failure;
- or `BLOCKED_INCOMPLETE_REVIEW`.

It does not evaluate audio or replace the human review. It validates completeness, internal consistency, full-film identity, chronology of the review protocol, and the exact attestation.

## Adversarial verification

All 11 tests passed:

1. complete 91/91 pass accepted;
2. one localized major defect routes to its exact take;
3. incomplete scorecard blocked;
4. major defect cannot coexist with a pass;
5. wrong film SHA-256 blocked;
6. missing continuous viewing blocked;
7. incorrect attestation blocked;
8. repair authorization embedded in the review blocked;
9. systemic rejection accepted only with confirmation and cross-chapter defects;
10. an explicitly accepted minor imperfection may remain below threshold;
11. final-master, upload, publishable, and release-authorized flags always remain false.

## Red-team boundary

The validator cannot infer naturalness, pronunciation quality, trust, or viewer value. A technically valid result only proves that Kevin’s completed review was recorded coherently against the pinned film. Silence, a partial form, contradictory severity, or a changed film always fails closed.

## Current state

No completed human decision was supplied or inferred. The canonical decision template remains blank and the production verdict remains `HUMAN_REVIEW_OPEN`.
