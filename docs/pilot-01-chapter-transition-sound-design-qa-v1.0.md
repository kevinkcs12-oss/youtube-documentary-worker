# Pilot 01 — Chapter Transition Sound Design QA v1.0

## Verdict

**PASS — reversible human-review sampler only.** Six chapter handoffs are now directly comparable in dry and designed form. The asset does not retain a treatment, alter the master, or authorize final sound, voice, music, mix, upload, or publication.

## Editorial boundary

- Anchors: 02:22, 03:30, 04:45, 06:04, 07:19, and 08:35.
- Each review window runs from five seconds before to seven seconds after its chapter anchor.
- Every treatment consists only of locally generated, fixed-seed noise: a three-second filtered pink-noise bridge and one 460 ms filtered white-noise accent.
- The previously validated opening bed is reproduced in the full-length stem, but the new sampler evaluates chapter transitions only.
- No sample, melody, harmony, musical work, third-party asset, copied interface sound, factual recording, or simulated real location is present.
- Added audio is **illustrative only**. It is not evidence and must not imply that a depicted brand, place, interface, vehicle, or building emitted that sound.

## Technical validation

| Check | Result |
|---|---|
| Full stem | 597.760 s; PCM 24-bit stereo, 48 kHz |
| Stem loudness | −38.5 LUFS integrated; 6.7 LU LRA; −23.7 dBTP |
| A/B sampler | 156.000 s / 3,900 frames |
| Sampler video | H.264, 1280×720, 25 fps |
| Sampler audio | AAC stereo, 48 kHz |
| Sampler loudness | −17.0 LUFS integrated; 7.8 LU LRA; −3.4 dBTP |
| Full decode | PASS for stem and sampler |
| Determinism | PASS: independent rerender produced byte-identical stem, sampler, and manifest |
| Timing authority | v1.2f remains unchanged at 597.760 s / 14,944 frames |

## Red-team record

The first sampler render placed persistent A/B badges in the upper evidence band. Contact-sheet inspection showed collisions with source and boundary text. That render was rejected. The retained version uses standalone A/B slates and leaves every source, limitation, and evidence label unobscured during picture playback.

The six treatments intentionally share one restrained vocabulary. This creates a consistent test but may become predictable or over-direct attention. Human review must score each transition separately for clarity, fatigue, tonal fit, false-diegesis risk, and whether silence would better serve the evidence. A global approval must not be inferred from approval of the opening test or any single chapter.

## Integrity hashes

- Source master: `3d1643246c066f377e841edc0f8653fec3c1bd9910d15151fb53732039259d27`
- Full stem: `3cb47996309b7dd486c4f0b6f2457eca56b3149197791e20e381c8fcff7d6fb3`
- A/B sampler: `9adae98226e0cb3a4f6ae5216a7f124c4e3f588a8730db10b9e51ffa83bd54e7`
- Manifest: `b4781010abb20e5c1008e72a9c5b690446e46bfce99ee7ef4d7080276d0df554`

## Gate status

Status is `REVERSIBLE_HUMAN_REVIEW_REQUIRED`. The full stem is a review input, not a final-mix asset. No approval is inferred from silence or incomplete scoring.
