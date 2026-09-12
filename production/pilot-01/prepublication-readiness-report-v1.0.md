# Pilot 01 — Pre-publication readiness report v1.0

## Decision

**PASS WITH HUMAN GATES.** The current delivery system is technically coherent. All 32 deterministic checks passed. No late-stage mismatch was found between picture timing, captions, chapters, evidence registry, metadata variants, thumbnails, measurement windows, or the blind voice-audition package.

This is not authorization to publish and it is not a declaration that the scratch-voice master is final.

## Canonical timing and identity

- Timing authority: v1.2f, 597.760 seconds, 14,944 frames, 25 fps.
- Current reversible picture candidate: v1.2g progressive-focus.
- v1.2g SHA-256: `3d1643246c066f377e841edc0f8653fec3c1bd9910d15151fb53732039259d27`.
- Captions: 161 cues, no overlap, two lines maximum, 19.99 characters/second maximum, final cue ends at 596.960 seconds.
- Description chapters: 00:00, 01:04, 02:22, 03:30, 04:45, 06:04, 07:19, 08:35.

## Evidence and launch controls

- Evidence registry contains F1–F7 plus CE1–CE3, with a populated `claim_not_supported` boundary on every row.
- The description retains both the bounded-claim disclaimer and the visual-rights disclaimer.
- Three title/thumbnail cells are present; all thumbnails are exactly 1280×720.
- Measurement log contains the locked 6 h, 24 h, 72 h, 7 d, and 14 d/completion windows.
- The voice-audition archive passes ZIP CRC validation and contains exactly four anonymized MP3 candidates.

## Human gates that remain

1. Retain or revert v1.2g progressive-focus after continuous viewing. This does not alter the v1.2f timing authority.
2. Select the final voice after blind listening. The current master still contains scratch narration.
3. Authorize a music/no-music final mix and any licensing, spending, external contact, or publication.

## Release-control rule

Do not create a publishable final master until gates 1–3 have explicit outcomes. After those outcomes, rerun the validator against the final voice/mix render and replace the master hash in the release manifest. Any duration, frame-count, chapter, subtitle, evidence-boundary, or thumbnail-dimension drift is a hard stop.

## Red-team conclusion

The principal residual risk is procedural, not technical: mistaking a technically valid scratch-voice candidate for an authorized final. The pack therefore labels unresolved subjective and authorization decisions as gates rather than silently treating them as passed.
