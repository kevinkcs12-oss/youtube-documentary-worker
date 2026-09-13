# Pilot 01 — Opening Procedural Sound Design QA v1.0

## Verdict

**PASS — reversible human-review candidate only.** The 00:00–01:04 opening now has an A/B-testable, rights-safe sound-design option. This verdict does not retain the design in the film, select music, approve final narration, or authorize release.

## Scope and editorial boundary

- Scope: opening 00:00–01:04 only.
- Source picture: v1.2g progressive-focus candidate; v1.2f remains the timing authority.
- Added audio: deterministic pink/white noise and five short noise accents generated locally from fixed seeds.
- No samples, melody, harmony, musical work, third-party audio, copied interface sound, or factual recording.
- Every added sound is **illustrative only**. It is not evidence and must not imply that any depicted place, interface, brand, or event emitted that sound.
- The designed candidate carries an on-screen provenance label during its first four seconds. The comparison reel labels the dry and designed versions separately.

## Technical validation

| Check | Result |
|---|---|
| Candidate duration / frames | 64.000 s / 1,600 frames |
| Candidate video | H.264, 1920×1080, 25 fps |
| Candidate audio | AAC stereo, 48 kHz |
| Candidate loudness | −18.2 LUFS integrated; 2.0 LU LRA; −3.5 dBTP |
| Comparison duration / frames | 132.000 s / 3,300 frames |
| Comparison video | H.264, 1280×720, 25 fps |
| Comparison audio | AAC stereo, 48 kHz |
| Comparison loudness | −18.7 LUFS integrated; 2.8 LU LRA; −3.5 dBTP |
| Procedural stem | 64.000 s; PCM 24-bit stereo, 48 kHz |
| Stem loudness | −38.4 LUFS integrated; 1.0 LU LRA; −23.7 dBTP |
| Full decode | PASS for candidate and comparison |
| Determinism | PASS: independent rerender produced byte-identical stem, candidate, comparison, and manifest |

## Red-team record

The first generated stem measured −62.3 LUFS and was rejected before retention because it was too quiet to support a meaningful editorial comparison. The corrected retained stem measures −38.4 LUFS, roughly 20 LU below the mixed candidate, preserving narration dominance while making the design perceptible.

Remaining human decision: compare A (dry) with B (designed) for clarity, fatigue, tonal fit, and whether the transition accents over-direct attention. Silence or partial review must not be interpreted as approval. If B distracts from evidence or suggests false diegetic realism, revert to A without changing timing.

## Integrity hashes

- Source master: `3d1643246c066f377e841edc0f8653fec3c1bd9910d15151fb53732039259d27`
- Stem: `f14e511cde9108e1212236906087f91dab78b7d99c2b2e4ffd153dc259da1aa0`
- Candidate: `ad06fc64827d5372c02e387dfe41abfa08507e88102fe3f1db047228bd0e976e`
- A/B comparison: `3322ebb52d9aae5d48e8096fa68d16da999b397aa8e274e7915fb7cf23d2b70d`
- Manifest: `e40ba86e8844116a3aaebe9d4148249a64063486df6b5f3225d60f52d7923fd6`

## Release gate

Status remains `REVERSIBLE_HUMAN_REVIEW_REQUIRED`. No final voice, music, license, spend, external contact, upload, or publication is authorized by this artifact.
