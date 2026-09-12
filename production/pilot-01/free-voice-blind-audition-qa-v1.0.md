# Pilot 01 — Free Voice Blind Audition QA Report v1.0

## Decision

The no-cost internal audition set is technically valid and ready for blind listening. No candidate is approved as the final release voice. The four subjective dimensions remain deliberately unscored because this execution environment cannot perform a reliable auditory judgment. Promoting a voice on waveform metrics alone would violate the premium-documentary gate.

The v1.2f picture-lock timing candidate remains unchanged at 09:57.760 / 14,944 frames.

## Locked test design

- Four anonymous candidates: A, B, C and D.
- Four excerpts, 232 words total: hook/scope; numerical evidence boundary; Spotify/model boundary; final landing.
- Identical wording and excerpt order for every candidate.
- Four 1.5-second inter-excerpt silences (6.0 seconds total).
- Cadence calibrated inside the synthesis engine; no post-render time stretch.
- Review encodes: mono MP3, 48 kHz, 192 kb/s.
- Archival audition masters: mono PCM WAV, 48 kHz, 24-bit.
- Each excerpt loudness-normalized before concatenation; no music or sound design.

## Objective results

| Candidate | Duration | Effective WPM* | Integrated | LRA | True peak | Decode |
|---|---:|---:|---:|---:|---:|---|
| A | 104.020 s | 142.01 | -20.4 LUFS | 2.2 LU | -6.9 dBFS | pass |
| B | 103.925 s | 142.15 | -20.2 LUFS | 2.9 LU | -3.0 dBFS | pass |
| C | 104.000 s | 142.04 | -20.3 LUFS | 2.9 LU | -3.0 dBFS | pass |
| D | 104.041 s | 141.98 | -20.6 LUFS | 2.3 LU | -3.0 dBFS | pass |

\*232 words divided by voiced-program duration after subtracting the locked 6.0 seconds of inter-excerpt silence.

The cadence spread is 0.17 WPM, small enough that listeners are not effectively choosing the fastest voice. Every WAV and MP3 fully decodes. All retained outputs are 48 kHz mono and remain below the audition peak ceiling.

## Rights and provenance

- Engine: CMU Flite, installed Debian package `libflite1 2.2-6build3`.
- Runtime library SHA-256: `d456d49a5e39689cf2012df85fb8e5c37c7c85f2de9df061fee0450231c348da`.
- Voice-library SHA-256 values are sealed with the A–D mapping, so the review pack stays blind.
- Package copyright notice SHA-256: `77d13a5e6cbe7277b4721033f9ad15707241c2832baa8c74ec823c9ee5ebf71c`.
- The bundled package notice grants broad use and distribution rights for the relevant Flite files, subject to retained notice, modification marking and non-endorsement conditions. The complete notice is included in the reproducibility pack.
- No model API, paid credit, subscription, contact, purchase or external publication was used.

## Red-team record

Three outputs were rejected before retention:

1. Native-rate audition: rejected because candidates ranged from 145.3 to 157.0 WPM.
2. First calibration attempt: rejected after an invalid C pointer caused a segmentation fault before rendering.
3. First complete-looking calibrated pass: rejected because Candidate C's MP3 ended at 65.510 seconds even though the WAV header claimed 104.000 seconds. The builder was hardened to normalize through a fresh temporary file, and the final Candidate C MP3 now decodes to 104.040 seconds.

This is why the retained gate checks both container duration and full decode instead of trusting a green render or a WAV header.

## Blind evaluation gate

Score each candidate on the existing 100-point brief:

- naturalness and absence of synthetic artifacts: 40;
- authority without theatricality: 15;
- pronunciation and numerical clarity: 15;
- restraint and tonal consistency: 10;
- technical/cadence/rights gate: 20 (already passed).

Disqualify any candidate with distracting synthesis artifacts, unstable numbers, false gravitas, exaggerated cadence, or a result that would require timing changes to v1.2f. Keep the sealed mapping closed until scores are recorded.

## Status

`TECHNICAL AUDITION READY / NO RELEASE VOICE SELECTED`

Next highest-value step: conduct the blind editorial listen, unseal only after scoring, and either nominate a no-cost control for a full-film scratch conform or reject the entire local set without changing picture-lock timing.
