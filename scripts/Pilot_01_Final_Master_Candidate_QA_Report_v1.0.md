# Pilot 01 — Final Master Candidate Builder QA v1.0

## Verdict

The builder is validated for later live use. No Pilot 01 master candidate was created because the canonical project remains `HOLD` and no live `PASS_MEDIA_VERIFIED_PREFLIGHT_ONLY` result exists.

## Function

The builder accepts only the exact authorization-bound audio conform named by the v1.1 media-verified preflight. It then performs a metadata-only MP4 remux with video and audio stream copy, strips inherited container metadata and chapters, and applies the explicit identity:

`PILOT 01 FINAL MASTER CANDIDATE — DO NOT UPLOAD`

The resulting object remains a review candidate, not a final master. A successful validation forces `master_candidate_present=true` while keeping `final_master_present=false`, `upload_authorized=false`, `publishable=false`, and `release_authorized=false`.

## Integrity controls

- The input bytes must match `audio_conform_sha256` from preflight v1.1.
- Preflight must have no failures and must prove direct media observation plus full decode.
- All four upstream authority flags must be false.
- FFmpeg uses stream copy; no image or audio re-encoding is permitted.
- Independent SHA-256 stream hashes before and after the remux must be identical.
- The candidate is fully decoded and re-probed for 597.760 seconds, 14,944 frames, 1920×1080/25 fps, mono 48 kHz, loudness and true peak.
- Existing output paths are refused, preventing overwrite.
- A closed preflight produces a validation failure and no candidate file.

## QA results

- 14/14 new tests passed.
- 14/14 media-preflight v1.1 regressions passed.
- 13/13 chained-preflight v1.0 regressions passed.
- 8/8 picture-decision binding regressions passed.
- 9/9 executive-handoff regressions passed.
- 9/9 narration-provenance regressions passed.
- Python compilation and archive CRC passed.

A real two-second 320×180/25 fps, mono 48 kHz fixture was remuxed twice. The two files were byte-identical, both elementary-stream hashes matched the source, and the non-upload identity metadata was present. A separate closed-preflight CLI test returned code 2 and created no candidate file.

## Red-team conclusion

The initial implementation allowed FFmpeg overwrite mode despite checking that the output did not exist. It now uses `-n`, so even a race or unexpected pre-existing path fails rather than replacing bytes. The closed-preflight no-output condition is covered by an end-to-end test.

Residual boundary: captions, description, sources, thumbnail selection and upload packaging remain separate assets. They are intentionally not embedded here, preventing this review candidate from being mistaken for a publishable upload bundle.

## Reproducibility

- Builder SHA-256: `1977e9814c43e35960b65646af1eba780116fdcba8eb037fcdc675e2ec68f741`
- Test runner SHA-256: `5e38a540d950644e9a801955793b8c8ee697e763f8158fc502d41e0c2b4b4f99`
- Test matrix SHA-256: `5071625b69578c6b75785c99fe81541c07cad1b94a9e70a592c3997295dde0fd`

No paid service, third-party asset, contact, upload, or publication was used.
