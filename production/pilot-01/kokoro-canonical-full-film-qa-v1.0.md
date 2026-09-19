# Pilot 01 — Kokoro canonical delivery, conform, and full-film review QA v1.0

## Executive verdict

`PASS_FULL_FILM_REVIEW_ONLY`

The Kevin-selected Kokoro voice `am_michael` now has a complete, lineage-pinned 91-take delivery, an exact 597.760-second narration conform, and one full-film review candidate on the canonical v1.2g picture. Human continuous-naturalness and pronunciation review remain open. This is not a final master and conveys no upload or release authority.

## Canonical delivery

- Voice: Kokoro `am_michael`, selected as blind-review candidate 2.
- Model: `hexgrad/Kokoro-82M`; Apache-2.0 model-card license recorded in the provenance manifest.
- Takes: 91/91 dry mono PCM 24-bit / 48 kHz.
- Selection: 58 raw natural-speed takes, 16 existing adaptive takes, 14 surgical rewrites, and 3 editorial boundary transfers.
- Maximum local adaptation: 1.15x. No global speed change.
- Minimum retained slot headroom: 100 ms.
- Protected evidence/transition intervals consumed: zero.
- Intake verdict: `PASS_INTAKE_ONLY`, zero failures.

The intake reports 36 rate-review warnings because active-span WPM is deliberately retained as a listening signal, not promoted into a proxy for naturalness. `Nielsen`, `Spotify`, and continuous naturalness remain explicitly human-review items.

## Narration conform

- Verdict: `PASS_NARRATION_CONFORM_ONLY`.
- Exact duration: 597.760 seconds.
- Exact length: 28,692,480 samples.
- Format: PCM s24le, mono, 48 kHz.
- Takes placed: 91/91.
- Time-stretch: none at conform.
- Music: none.
- Output SHA-256: `bceafeb4e4864fe0973788d10b5d81829b56ac3b41d17093f9240ddca8e4c186`.
- Independent second conform: byte-identical narration and placement map.
- Full decode: pass.

## Full-film review candidate

- Picture authority: v1.2g, SHA-256 `3d1643246c066f377e841edc0f8653fec3c1bd9910d15151fb53732039259d27`.
- Picture: stream-copied; elementary video payload unchanged.
- Runtime: 597.760 seconds.
- Frames: 14,944 at 1920x1080/25 fps.
- Audio: AAC mono/48 kHz, derived only from the canonical narration conform.
- Observed output loudness: -16.4 LUFS integrated, 4.1 LU LRA, -1.3 dBTP.
- Candidate SHA-256: `8076d795c25f2fef0f377fd4abacaa72ad3a22b6f7dddb0cedfb47c7b413c580`.
- Full audiovisual decode: pass.
- Independent second build: byte-identical.
- Embedded identity: `REVIEW ONLY`, `DO NOT UPLOAD`, naturalness/pronunciation open.

## Fail-first findings retained

1. The first delivery build exposed a trimming mismatch on T024 because a point threshold did not match the timing map's frame-RMS detector. The builder was corrected to use the exact timing-map detector.
2. The first synthetic-floor file had a malformed write path. The validator rejected it; the builder was corrected and the regenerated file passed direct format and hash checks.
3. Treating short-phrase active-span WPM as a hard naturalness verdict would have reintroduced metric gaming. It remains a warning; technical timing and human perceived naturalness are separate gates.
4. The first full-film mux was rejected because AAC packet padding extended the container to 597.800 seconds. Explicit duration and shortest-stream constraints produced an exact 597.760-second retained candidate.

## Red-team boundaries

- No performer-consent claim was fabricated for a synthetic voice. TTS model, voice, selection, and license provenance replace the obsolete human-performer fields.
- Technical timing conformity does not prove naturalness.
- License provenance does not authorize publishing the documentary.
- The full-film candidate is for continuous human review only; it cannot satisfy final-master, upload, or publication gates.
- No paid model, paid credit, music, third-party contact, upload, or publication was used.

## Next decision

Watch the single full-film candidate continuously. If naturalness and the two named pronunciations clear the perceptual threshold, freeze narration and move the bottleneck to launch packaging. If a defect is heard, regenerate only the affected take and rerun the same fail-closed chain.
