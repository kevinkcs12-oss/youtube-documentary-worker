# Pilot 01 Production State

Canonical title: **Why Does Everything Look the Same Now?**

Current production baseline:
- Master script v1.1 remains the canonical editorial source.
- Full animatic v1.1 runtime: 10:22.
- Active reversible retention candidate: **v1.2b-natural-cadence**, 10:02.
- Eight-sequence structure and all seven evidence families remain intact.
- Layer C production worker and CI are validated; no paid assets or services are used.

Validated first block:
- Sequence 1 v1.2 remains the accepted rights-safe opening candidate and is conformed to the locked A018–A030 evidence module through 02:22.
- Picture and scratch-voice versions are exactly 142.000 seconds / 3,550 frames at 1080p25 and pass full decode.
- Picture SHA-256: `98f34bed54d2c7be7d0d06113be12765b3e8ffc5739e4c9e8e328fe57ea501be`.
- Scratch-voice SHA-256: `97e14b3d2d64bdb54c188ed4c5276c560dfd2af9d3078c0641af5d009cabad14`.
- Rights and claim-function gates pass. Final motion design must keep indispensable caveats above the lower caption band.

Validated v1.2b retention candidate:
- Runtime: exactly 602.000 seconds / 15,050 frames, 1920×1080/25 fps; full decode passed.
- Master SHA-256: `274fc7d2903dc1366b4bcebc3434b9244d37e43b5ab9eda139e0def651cba95a`.
- The v1.2 speedups are removed. Replacement A is 32 words in 14 seconds (137.1 effective WPM); replacement B is 131 words in 54 seconds (145.6 effective WPM).
- Local Flite speech is generated at native cadence and padded; no `atempo` or finished-voice acceleration is used.
- F3 remains probabilistic; Spotify remains limited to familiarity/similarity/discovery in music recommendation; the visual-convergence loop is explicitly the documentary's model, not Spotify's finding.
- The rights-safe first 2:22, quantitative evidence, all named counterexamples, and the 82-second conclusion candidate are preserved.
- v1.2b supersedes v1.2-retention-test as the active reversible timing/cadence candidate, but is not picture lock and does not choose a final voice.
- Reproducible script: `scripts/render_pilot_01_v1.2b_natural_cadence.sh`.
- QA: `production/pilot-01/v1.2b-natural-cadence-qa.md`.
- Narration diff: `production/pilot-01/v1.2b-natural-cadence-narration.md`.

Current bottleneck:
- The 10:02 timeline lacks an exact full subtitle/EDL conform for the new timing map.
- Tertiary source lines remain vulnerable to player-caption occlusion.
- Final audiovisual retention and motion timing cannot be judged from contact sheets alone.

Next production gate:
- Build the exact full 10:02 SRT/EDL conform, then run real-time audiovisual and caption-safe-zone QA before any canonical promotion or picture lock.

Layer C should ingest repository-relative manifests and render only assets explicitly staged in the job directory. No paid APIs, external publishing, or secrets are required.
