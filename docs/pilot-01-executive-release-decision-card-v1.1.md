# Pilot 01 — Executive release decision card v1.1

Project: *Why Does Everything Look the Same Now?*  
Timing authority: **v1.2f, 09:57.760 / 14,944 frames**  
Picture candidate: **v1.2g progressive-focus**  
Current state: **HOLD — human decisions required**

This revision adds explicit sound-design decisions. Silence, partial review, technical QA, or prior production autonomy never counts as approval.

## Required decisions

1. Motion: retain v1.2g or revert to v1.2f picture while preserving timing.
2. Voice: choose A–D or reject all. `REJECT_ALL` deliberately blocks release.
3. Opening sound: choose `DRY` or `PROCEDURAL_V1` after reviewing the 00:00–01:04 A/B reel.
4. Chapter sound: choose `DRY` or `PROCEDURAL_V1` independently for C02 02:22, C03 03:30, C04 04:45, C05 06:04, C06 07:19, and C07 08:35.
5. Mix: choose `NO_MUSIC` or `RIGHTS_CLEARED_MUSIC_AFTER_REVIEW`.
6. Metadata: choose the native A/B/C test or one fixed cell.
7. Publication: keep `HOLD`, authorize an unlisted technical upload, or authorize publication.

All procedural sound is original, deterministic and illustrative only. It is never evidence or a factual/diegetic recording. Any chapter can remain dry even if another transition is retained.

## Release-mode requirements

Before the manifest may open downstream final conform and preflight:

- every decision above must be complete;
- voice cannot be `REJECT_ALL`;
- all six chapter-sound keys must exist exactly once and contain an allowed value;
- `sound_review_attestation` must equal: `I reviewed the opening and six chapter-transition A/B surfaces.`
- `authorization_id` must be present;
- `authorization_attestation` must equal: `I authorize the selected Pilot 01 configuration and the stated publication scope.`
- publication must be `AUTHORIZE_UNLISTED_UPLOAD` or `AUTHORIZE_PUBLICATION`.

A passing decision manifest authorizes only the next gated conform/preflight work. It cannot bypass rights, evidence, captions, decode, loudness, checksums, or an explicit publication scope.

## Current machine verdict

Normal review mode: `PASS_CLOSED_GATES`. Release mode: `BLOCKED` while the decisions and attestations remain incomplete.
