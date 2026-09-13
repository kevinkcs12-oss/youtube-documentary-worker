# Pilot 01 — Final Voice Delivery Gate QA v1.0

## Disposition

**VALIDATED FOR FUTURE NARRATION INTAKE. NO VOICE OR RECORDING IS APPROVED.**

The gate converts the existing 91-take recording session plan into a machine-verifiable delivery contract. It is deliberately fail-closed: incomplete authority, missing audio, naming drift, checksum mismatch, wrong encoding, clipping, implausible active-speech rate, absent room tone, or digital-silence room tone blocks intake.

## Locked contract

- Exactly 91 files named `T001.wav` through `T091.wav`.
- One `ROOM_TONE.wav` file of at least 30 seconds.
- Dry mono PCM WAV, 48 kHz, 24-bit; no music.
- Per-take SHA-256 bound to the delivery manifest.
- Explicit selected candidate A–D, recording authorization ID and performer-consent assertion.
- Explicit pronunciation confirmations for Nielsen and Spotify.
- The canonical take text remains bound through 91 individual text hashes.
- Contract SHA-256: `8d706e969fde40f46696efc5c0d9b8336ffd14711736367a5a698299f491c882`.

## Signal gates

- Any full-scale clipped sample is a hard failure.
- Peak above −0.5 dBFS is a hard failure; peaks outside the preferred raw-capture window of −18 to −3 dBFS are warnings.
- Active speech is measured above −45 dBFS. Below 80 or above 200 WPM is a hard failure; 120–170 WPM is the preferred review range.
- A take with no detected speech is rejected.
- Room tone shorter than 30 seconds, incorrectly encoded, clipped, or indistinguishable from digital silence is rejected.

These are intake diagnostics, not performance direction. They cannot replace human judgments about authority, warmth, restraint, pronunciation, fatigue, or editorial fit.

## Executed tests

1. The canonical 91-row cue sheet emitted a stable contract and blank fail-closed manifest.
2. A complete synthetic technical fixture containing 91 correctly named PCM 24-bit mono 48 kHz takes and 30 seconds of room tone passed with 91/91 takes, zero failures and zero warnings.
3. An incomplete delivery was rejected with the exact missing inventory and unopened authorization gates.
4. A deliberately invalid 16-bit, 44.1 kHz, stereo take was independently rejected on codec, sample rate and channel count.
5. The first loop-based synthetic test was discarded after FFmpeg consumed the loop's standard input and produced malformed filenames. The corrected harness used `-nostdin`, rebuilt all 92 required WAV files, and passed. No malformed fixture is retained as a deliverable.

## Red-team boundary

- `PASS_INTAKE_ONLY` means only that received narration is technically eligible for editorial conform.
- The validator always writes `release_authorized: false`.
- It cannot select a voice, approve a performance, license music, change v1.2f timing, retain v1.2g, choose metadata, upload, or publish.
- A rejected-all audition result requires a separately authorized contract revision before any non-A–D voice can be accepted.

## Retained artifacts

- `validate_pilot_01_final_voice_delivery.py`
- `Pilot_01_Final_Voice_Delivery_Contract_v1.0.csv`
- `Pilot_01_Final_Voice_Delivery_Manifest_Template_v1.0.json`
- `Pilot_01_Final_Voice_Delivery_Gate_Test_Matrix_v1.0.csv`
- this QA report
