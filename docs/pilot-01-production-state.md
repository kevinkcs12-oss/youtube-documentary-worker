# Pilot 01 Production State

Canonical title: **Why Does Everything Look the Same Now?**

Current canonical editorial baseline:
- Master script v1.1
- Full animatic v1.1 runtime: 10:22
- Retention-test branch v1.2: 10:02, reversible and not canonical
- Eight-sequence structure
- Layer C production worker and CI validated

Current real-asset gate:
- Sequence 1 opening v1.2 is the accepted reversible working candidate at exactly 64.000 seconds / 1,600 frames, 1080p/25 fps.
- Commit `2ff6432608f51b6087d2893c002513e2b807234a`; CI run `34434585786`; render run `34434585813`; artifact `10135723905`.
- Picture SHA-256: `08282a5c3a62f340bedc6bfa655131a78aee2d0be1184e6121cb1a32baf276cc`.
- All bookstore footage and the real phone interface are absent.
- Five retained Pexels sources and four original deterministic graphics have source/render SHA-256 manifests.
- The opening passes exact-duration, frame-count, full-decode, contact-sheet, claim-function, rights and mobile-hierarchy QA.
- It is not yet picture-locked: graphics occupy 21 seconds and repeated office/apartment motifs still need continuous-context audiovisual review.

Next production gate:
- Assemble the v1.2 opening with the validated 01:04–02:22 A018–A030 evidence block.
- Add the existing scratch-timing narration and separate subtitles without choosing a final voice.
- Assert exactly 142.000 seconds / 3,550 frames at 1080p/25 fps.
- Inspect the 01:04 transition, claim-to-visual alignment, subtitle safe zones, mobile legibility, repetition and full decode.
- Promote the first 2:22 only if every gate passes; then resume whole-pilot v1.2b natural-cadence microcuts.

Layer C should ingest a repository-relative JSON manifest and render only assets explicitly staged in the job directory. No paid APIs, external publishing, or secrets are required.
