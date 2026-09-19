# Pilot 01 — Full-film perceptual review companion QA v1.0

## Verdict

`PASS_REVIEW_COMPANION_ONLY`

The companion is bound to the retained full-film review candidate SHA-256 `8076d795c25f2fef0f377fd4abacaa72ad3a22b6f7dddb0cedfb47c7b413c580`. It contains an exact 91-take scorecard, a 38-take machine-signal/pronunciation recheck list, a one-pass review card, and a closed-authority manifest.

## Purpose

Reduce the founder-time cost and ambiguity of the only remaining production gate: continuous human perception. The first pass stays uninterrupted and unprimed. Machine rate signals are exposed only for a second, targeted recheck and are explicitly not automatic failures.

## Checks

All 11 checks passed:

1. canonical happy path;
2. deterministic byte-identical ZIP from independent builds;
3. wrong full-film bytes rejected;
4. missing take rejected;
5. duplicate take rejected;
6. out-of-order take rejected;
7. wrong final spoken-cue boundary rejected;
8. non-passing intake verdict rejected;
9. missing named-pronunciation warning rejected;
10. output overwrite refused;
11. all human decision fields remain blank and every downstream authority remains false.

## Red-team findings

- A hotspot-first review would create anchoring and could convert weak machine signals into false subjective defects. The protocol therefore requires a blind continuous pass before opening the hotspot list.
- Timing and active-span rate cannot prove naturalness. The builder preserves those values only as listening signals.
- The scorecard cannot silently authorize repairs: every row starts with `repair_authorized=NO`.
- The companion is not a second film candidate and does not alter picture, narration, timing, mix, or evidence semantics.

## Counts and hashes

- 91 ordered take rows (`T001`–`T091`).
- 36 active-span rate signals.
- 38 unique recheck takes after adding `T035`, `T062`, and `T065` pronunciation checks.
- Deterministic pack SHA-256: `e61e60fc448dd3210aea6fd039085fe0c5584db9eda5470af5dbea80ecaec718`.

## Authority limits

Human decision remains `OPEN`. Final master, upload, publishability, and release authorization remain false.
