# Pilot 01 — Executive Human-Review Reel QA v1.0

Status: **VALIDATED CONSOLIDATED REVIEW SURFACE / SCRATCH VOICE / DO NOT PUBLISH**

## Outcome

The three outstanding human-review surfaces are now available in one chaptered reel: motion, counterbalanced blind voice audition, and continuous full-film procedural sound design. The reel records no decision and changes no production authority. Silence or an incomplete v1.1 form remains `HOLD`.

## Retained artifact

- Review timeline authority: 1,126.760 seconds (18:46.760).
- Frames: 28,169 at 1280×720 / 25 fps.
- Container duration: 1,126.781 seconds; the 21 ms excess is AAC encoder padding, not video drift.
- Audio: AAC-LC stereo, 48 kHz, 192 kb/s target.
- Integrated loudness: -20.05 LUFS.
- Loudness range: 7.10 LU.
- True peak: -5.42 dBTP.
- Full audiovisual decode: PASS.
- Eight ordered chapters: PASS.
- Independent complete rerender: byte-identical.
- Candidate SHA-256: `58876a5fc5217c55a40475e70657c20ec808a1e046ac9590b9b82bc07de4934e`.
- Container metadata states `REVIEW ONLY - SCRATCH VOICE - DO NOT PUBLISH`.

## Review order and boundaries

| Start | End | Surface | Decision boundary |
|---:|---:|---|---|
| 00:11.000 | 01:40.000 | Motion comparison | Retain v1.2g or revert to v1.2f |
| 01:45.000 | 08:36.000 | Counterbalanced voice audition | A, B, C, D, or REJECT_ALL |
| 08:41.000 | 18:38.760 | Continuous sound-design review | Seven independent DRY/PROCEDURAL_V1 choices |

Standalone slates separate every surface. The final slate directs decisions to the canonical v1.1 form and explicitly states that silence means `HOLD`.

## Source integrity

- Motion source SHA-256: `5392d8333a345c8a82f7cd826638084e45fc7cb9fa58a6138d5ecbae43cd56b9`.
- Voice source SHA-256: `6bf3f5348f24b7a28a07f850a5e9ad25ab74262f74a0fadbe2125f1e7fd6e33a`.
- Sound source SHA-256: `189a708711ef292ef819b7144b30c435d06203ca6fe4f4f82f2a89502794c5d5`.
- The 1920×600 motion comparison is proportionally reduced and letterboxed; it is not cropped.
- Mono review audio is converted with equal-power coefficients of 0.70710678 per channel, preventing the +3 dB stereo-duplication bias previously rejected.

The original three review artifacts remain the fidelity authorities. This consolidated reel is convenience media and must not supersede their individual manifests or QA reports.

## Visual inspection

The intro, three section slates and closing slate were inspected from the retained render. Titles, instructions and the `DO NOT PUBLISH` boundary are legible at 720p. No slate overlays any evidentiary frame because all labels are confined to standalone separator segments.

## Red-team limits

1. A fixed review order can create fatigue or primacy effects. The counterbalanced ordering inside the voice section is preserved, but reviewers may still revisit the standalone source reels.
2. The convenience transcode is unsuitable for judging pixel-level master fidelity; use the original review assets for close inspection.
3. The scratch voice is not a final performance. Any selected final narration requires a fresh intake, conform and mix review.
4. The continuous sound section does not collapse its seven choices into one global verdict.
5. Watching the reel does not itself constitute the exact v1.1 attestations. The decision form must be completed explicitly.
6. No motion, voice, sound, mix, metadata, upload or publication decision is inferred from this artifact.

## Verdict

**PASS as a consolidated human-review surface only. All eleven v1.1 configuration choices and every release gate remain closed.**
