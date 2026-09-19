# Pilot 01 — Full-film perceptual review card v1.0

## Authority and scope

- Review exactly `Pilot_01_Kokoro_Full_Film_Review_DO_NOT_UPLOAD_v1.0.mp4`.
- Verified SHA-256: `8076d795c25f2fef0f377fd4abacaa72ad3a22b6f7dddb0cedfb47c7b413c580`.
- Runtime: 09:57.760. Voice: Kevin-selected Kokoro `am_michael`.
- This card records human perception only. It cannot authorize upload, publication, release, or a final master.

## One-pass protocol

1. Watch the film once from 00:00 to 09:57.760 at normal speed, without opening the hotspot list. Use ordinary listening equipment and a comfortable fixed volume.
2. Mark only defects that are actually heard. Record the clock time immediately; do not infer a defect from a machine flag.
3. Classify each marked defect as `CRITICAL`, `MAJOR`, or `MINOR`:
   - `CRITICAL`: wrong/missing words, meaning changed, broken audio, or materially misleading pronunciation.
   - `MAJOR`: clearly synthetic cadence, distracting speed, or pause/visual mismatch that damages trust.
   - `MINOR`: noticeable but non-distracting imperfection.
4. After the uninterrupted pass, use the hotspot list only to recheck ambiguous moments. It contains 38 takes derived from 36 machine rate signals plus named-pronunciation checks.
5. Decide:
   - `PASS_PERCEPTUAL_REVIEW`: zero critical or major defects; minor issues are below the distraction threshold.
   - `TARGETED_REPAIR`: one or more localized critical/major defects; list exact take IDs. Regenerate only those takes and rerun the existing intake/conform/review chain.
   - `REJECT_VOICE`: only if defects are systemic across chapters and cannot plausibly be repaired take-by-take.

## Required named checks

- `T035` around 03:35.656 — “Jakob Nielsen”.
- `T062` around 06:32.145 — “Spotify”.
- `T065` around 07:01.689 — possessive “Spotify’s”.

## Closed fields

Human decision: `OPEN`

Final master authorized: `NO`  
Upload authorized: `NO`  
Publishable: `NO`  
Release authorized: `NO`
