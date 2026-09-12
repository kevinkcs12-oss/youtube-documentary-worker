# Pilot 01 — Audio conform gate v1.0

## Purpose

This gate proves the narration-only final-conform path without selecting a voice, licensing music, or producing an authorized release master.

## Hard gates

- Picture input must match the locked v1.2g SHA-256 and the v1.2f timing authority.
- Narration must already occupy the complete 597.760-second timeline; the script does not time-stretch performance.
- Output must remain 597.760 seconds, 14,944 frames, 1920×1080 at 25 fps.
- Audio must be mono 48 kHz, approximately −16 LUFS integrated, and no higher than −1 dBTP.
- Release mode refuses to run without affirmative motion, voice, mix-path, and publication fields plus an authorization identifier.
- Music is deliberately excluded from v1.0. A music branch requires a rights-approved source, mix architecture, and separate validation.

## Red-team boundary

A technically passing dry run is not publishable. The retained control output carries “DRY-RUN CONTROL — DO NOT PUBLISH” container metadata. It uses the existing scratch track only to test remuxing, loudness, duration, frame count, and decode.

## Current verdict

Narration-only conform architecture is testable and reversible. Final use remains blocked on the human v1.2g decision, blind voice selection, music/no-music authorization, and explicit publication authorization.

## Dry-run result

- Status: PASS, explicitly non-publishable.
- Output: 597.760 seconds, 14,944 frames, 1920×1080 at 25 fps; full decode passed.
- Audio: mono 48 kHz, −15.88 LUFS integrated, −1.06 dBTP.
- Output SHA-256: `852f6fe5bc8cfdbff1d6c97f248abe94890fac084d1a365653c39d992c7ccbc0`.
- Narration control SHA-256: `a5df1f993a9688835a6055551651a5cd36a0217fb2bc0e7935cdd5d6d6233d7a`.

## Rejected states

1. A release-mode invocation with all decision flags false was refused before rendering, as designed.
2. The first one-pass loudness render retained picture timing but measured −15.14 LUFS and was rejected.
3. The initial two-pass validation incorrectly read loudnorm's hypothetical `output_*` fields instead of the rendered file's observed `input_*` fields. The validator was corrected and AAC headroom increased to a −1.2 dBTP processing target; the retained render measures −1.06 dBTP.
