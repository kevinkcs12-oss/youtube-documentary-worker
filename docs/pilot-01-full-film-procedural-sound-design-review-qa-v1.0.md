# Pilot 01 — Full-Film Procedural Sound-Design Review QA v1.0

Status: **VALIDATED REVERSIBLE REVIEW CANDIDATE / DO NOT PUBLISH**

## Outcome

The opening bed and six chapter-transition treatments can now be judged in one uninterrupted 09:57.760 viewing. The candidate uses the captioned v1.2g review picture and the previously validated procedural stem. It does not change the v1.2f timing authority, select any sound treatment, choose a voice, introduce music, or authorize release.

## Retained candidate

- Runtime: 597.760 seconds.
- Frames: 14,944 at 1280×720 / 25 fps.
- Video elementary-stream MD5: `7164f03dad3ea9059a0097ea208ad817`, identical to the canonical captioned v1.2g proxy.
- Audio: AAC-LC, stereo, 48 kHz, 192 kb/s target.
- Integrated loudness: -19.8 LUFS.
- Loudness range: 7.7 LU.
- True peak: -2.4 dBTP.
- Full audiovisual decode: PASS.
- Independent rerender SHA-256 equality: PASS.
- Candidate SHA-256: `189a708711ef292ef819b7144b30c435d06203ca6fe4f4f82f2a89502794c5d5`.
- Container metadata explicitly states `REVIEW ONLY - SCRATCH VOICE - DO NOT PUBLISH`.

## Narration-dominance check

The procedural stem remains well below narration in every decision window:

| Scope | Narration RMS | Stem RMS | Stem below narration |
|---|---:|---:|---:|
| Opening 00:00–01:04 | -21.5 dBFS | -42.7 dBFS | 21.2 dB |
| C02 02:22 | -23.3 dBFS | -48.8 dBFS | 25.5 dB |
| C03 03:30 | -23.6 dBFS | -48.9 dBFS | 25.2 dB |
| C04 04:45 | -26.1 dBFS | -48.8 dBFS | 22.7 dB |
| C05 06:04 | -24.7 dBFS | -49.0 dBFS | 24.3 dB |
| C06 07:19 | -25.2 dBFS | -48.9 dBFS | 23.7 dB |
| C07 08:35 | -25.6 dBFS | -48.9 dBFS | 23.3 dB |

These measurements establish headroom and narration dominance, not editorial suitability.

## Rejected intermediate

The first continuous render duplicated the mono scratch narration into two full-level stereo channels. Its integrated loudness rose to -16.8 LUFS, roughly 3 dB above the dry reference. That would bias a human A/B decision toward the designed version. It was rejected and replaced with an equal-power mono-to-stereo conversion. The retained candidate returns to -19.8 LUFS while preserving the stereo procedural field.

## Evidence and rights boundary

- Burned captions and all upper-band evidence qualifications are inherited unchanged.
- Added sound remains illustrative, not evidence and not a claim of diegetic or factual recording.
- The stem contains only deterministic fixed-seed noise synthesis.
- No music, sample, copied interface sound, third-party recording, paid service, or external asset is present.

## Red-team limits

1. Objective loudness cannot establish that repeated cues feel restrained; only continuous human listening can.
2. The scratch voice is not the final performance. Final narration may alter masking and require a new mix.
3. Accepting the global pattern must not collapse the seven independent DRY/PROCEDURAL_V1 decisions.
4. A review-candidate pass is not a rights, final-mix, upload, or publication pass.
5. The exact sound-review attestation in the executive v1.1 gate remains blank until a human completes the review.

## Verdict

**PASS for continuous human sound-design review only. All executive and release gates remain closed.**
