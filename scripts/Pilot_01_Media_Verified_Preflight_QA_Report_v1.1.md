# Pilot 01 — Media-Verified Chained Preflight QA v1.1

## Verdict

`PASS_MEDIA_VERIFIED_PREFLIGHT_ONLY` for the synthetic positive contract fixture. The live project remains `HOLD`; no authorization-bound final narration, final master, upload, or publication exists.

## Superseding change

Version 1.0 bound the supplied media bytes to the upstream v1.3 JSON but trusted that JSON's technical fields. A matching file hash therefore did not independently prove duration, frame count, geometry, frame rate, stream topology, audio format, loudness, true peak, decode integrity, or identity metadata.

Version 1.1 now inspects the supplied media directly:

- `ffprobe -count_frames` verifies one video stream, one audio stream, 597.760 seconds, 14,944 decoded frames, 1920×1080, 25 fps, mono 48 kHz;
- `ffmpeg` performs a full decode;
- an independent EBU-style loudness pass requires −16.6 to −15.4 LUFS and true peak no higher than −1.0 dBTP;
- title and comment must both equal `PILOT 01 AUTHORIZATION-BOUND AUDIO CONFORM — NOT FINAL MASTER`;
- directly observed values must agree with every corresponding field declared by audio conform v1.3.

The complete v1.0 chain remains mandatory: technical baseline, canonical executive decision, media hash, decision-manifest hash, motion/picture binding, publication scope, and non-fixture narration lineage.

## QA results

- 14/14 new media-verification adversarial tests passed.
- 13/13 chained-preflight v1.0 regressions passed.
- 8/8 picture-decision binding regressions passed.
- 9/9 executive-handoff regressions passed.
- 9/9 narration-provenance regressions passed.
- Python compilation passed.

The real probe, loudness reader, and decoder were also exercised against a disposable one-second negative fixture. Its 320×240/30 fps image, 44.1 kHz stereo audio, −21.75 LUFS, 30 frames, one-second duration, and wrong identity metadata were observed correctly. The validator returned `BLOCKED` with fourteen explicit mismatch reasons.

## Red-team conclusion

The technical fields are no longer accepted on assertion alone. Byte identity and direct media observation must both pass. Non-finite observed values, extra/missing primary streams, incomplete decode, loudness excursions, metadata substitution, and declared/observed disagreements all fail closed.

Every output still forces `final_master_present=false`, `upload_authorized=false`, `publishable=false`, `release_authorized=false`, and `preflight_only=true`. The validator has no rendering, upload, or publication capability.

## Reproducibility

- Validator SHA-256: `c474cd5e730ad57fae1036718117fa12ee62d201058fc453f6654b5ea2d1afeb`
- Test runner SHA-256: `1e56bb04b38e1cb9f4af4722ab187b5ce9028d0dca0d8d6f1b3b07932f39fb65`
- Test matrix SHA-256: `c80f2f8ae704a5a2188a5beee8daa67f1861d5742385ae69b71a6cc4bc2c1e02`

No paid service, external asset, third-party contact, upload, or publication was used.
