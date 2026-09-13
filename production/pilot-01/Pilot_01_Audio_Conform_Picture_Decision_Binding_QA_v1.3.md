# Pilot 01 — Audio Conform Picture-Decision Binding QA v1.3

Date: 2026-09-13  
Status: **PASS — selected motion and exact picture bytes are now inseparable**

## Material defect corrected

The v1.2 audio conform gate accepted only the v1.2g picture SHA-256. That was safe against arbitrary substitution, but incompatible with the canonical executive option `REVERT_V1_2F`. A complete, valid decision to revert could therefore never be executed; worse, an implementation that ignored the failure could pair authorized narration with the wrong visual candidate.

## v1.3 contract

- `RETAIN_V1_2G` requires exactly the pinned v1.2g progressive-focus bytes: `3d1643246c066f377e841edc0f8653fec3c1bd9910d15151fb53732039259d27`.
- `REVERT_V1_2F` requires exactly the pinned v1.2f pacing-trim bytes: `038b9eb7a638b07be70fe61d8c037c1332d41c5eb40d63862ea7d31717685c7a`.
- The closed-gate dry-run may use only the manifest's declared, pinned review candidate. An unknown candidate fails.
- Retain with v1.2f bytes and revert with v1.2g bytes both fail before FFmpeg starts.
- The output validation now declares schema `pilot-01-audio-conform-validation-v1.3`, the effective motion decision, picture variant, picture hash and decision-manifest hash for downstream chain-of-custody checks.
- All v1.2 executive-decision protections and v1.1 narration-provenance protections remain active.

## Verification

| Test family | Result |
|---|---:|
| v1.3 picture-decision binding | 8/8 PASS |
| v1.2 executive handoff regression | 9/9 PASS |
| v1.1 narration provenance regression | 9/9 PASS |
| Python compilation | PASS |

The v1.3 suite proves both authorized picture branches, both cross-branch substitution failures, the closed-gate candidate restriction, and the new downstream schema/manifest binding. Tests operate on decision data and known hashes only; they do not fabricate an authorization or render media.

## Authority boundary

This correction does not retain or revert the motion pass. That remains an explicit human choice. It does not select a voice or sound treatment, authorize music, create a final master, upload, or publish. Every produced conform remains `publishable=false`, `release_authorized=false`, and `audio_conform_only=true`.

