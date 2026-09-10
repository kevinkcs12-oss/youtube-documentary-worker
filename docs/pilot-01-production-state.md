# Pilot 01 Production State

Canonical title: **Why Does Everything Look the Same Now?**

Current production baseline:
- Master script v1.1 remains the canonical editorial source.
- Full animatic v1.1 runtime: 10:22.
- Active reversible review candidate: **v1.2e-motion-accent**, 10:02.
- Eight-sequence structure and all seven evidence families remain intact.
- Layer C production worker and CI are validated; no paid assets or services are used.

Validated first block:
- Sequence 1 v1.2 remains the accepted rights-safe opening candidate and is conformed to the locked A018–A030 evidence module through 02:22.
- Picture and scratch-voice versions are exactly 142.000 seconds / 3,550 frames at 1080p25 and pass full decode.
- Picture SHA-256: `98f34bed54d2c7be7d0d06113be12765b3e8ffc5739e4c9e8e328fe57ea501be`.
- Scratch-voice SHA-256: `97e14b3d2d64bdb54c188ed4c5276c560dfd2af9d3078c0641af5d009cabad14`.
- Rights and claim-function gates pass. Final motion design must keep indispensable caveats above the lower caption band.

Validated v1.2c timing and caption conform:
- Runtime: exactly 602.000 seconds / 15,050 frames, 1920×1080/25 fps; full decode passed.
- Corrected master SHA-256: `03c6d5dd01a4bce55e860a89e32e8a924fba5dcc9f419fde858cbafd27d77e11`.
- The earlier v1.2b master (`274fc7d...`) is rejected: full subtitle conform exposed a partial semantic duplicate at the Sequence 6 splice.
- Replacement B is corrected to 128 words in 54 seconds (142.2 effective WPM; 52.765 seconds / 145.5 WPM native Flite speech). It now ends by labeling the loop as the documentary's model; the retained close separately rejects conspiracy framing and defines the expensive-exception pressure.
- Replacement A remains 32 words in 14 seconds (137.1 effective WPM). No `atempo` or finished-voice acceleration is used.
- Exact EDL: Sequences 1–2 00:00–02:22; S3 02:22–03:32; S4 03:32–04:49; S5 04:49–06:09; S6 06:09–07:24; S7 07:24–08:40; S8 08:40–10:02.
- Full SRT has 161 ordered, overlap-free cues, maximum two lines, one 43-character legacy exception and no cue above 20 characters/second; final cue ends at 10:01.200.
- F3 remains probabilistic; Spotify remains limited to familiarity/similarity/discovery in music recommendation; the visual-convergence loop is explicitly the documentary's synthesis.
- The rights-safe first 2:22, quantitative evidence, named counterexamples and 82-second conclusion candidate are preserved.
- v1.2c is an active reversible timing, semantic-continuity and subtitle authority. It is not picture lock and does not choose a final voice.
- Caption generator: `scripts/build_pilot_01_v1_2c_caption_conform.py`.
- QA: `production/pilot-01/v1.2c-caption-conform-qa.md`.
- SRT/EDL: `production/pilot-01/v1.2c-caption-conform.srt` and `production/pilot-01/v1.2c-caption-conform-edl.csv`.

Validated v1.2d evidence safe-zone conform:
- Captioned contact-sheet review found a systematic defect: lower source and claim-boundary text was often hidden by two-line player captions.
- Twenty bounded upper-band overlays now duplicate only indispensable source, scope, illustration-status, and falsification labels. Narration, subtitles, EDL, and runtime are unchanged.
- Runtime: exactly 602.000 seconds / 15,050 frames, 1920×1080/25 fps; full decode passed.
- Master SHA-256: `528af6373501f57a64b333696679856d6ea85309e041f273caecb9ac40e81e80`.
- Encoded audio is byte-identical to v1.2c (`MD5 2d00f8a41c542f1c07eac5fbd074cc26`).
- Locked layout rule: reserve y=820–1040 at 1080p for captions/player chrome; indispensable evidence text must finish above y=810.
- Builder: `scripts/build_pilot_01_v1_2d_evidence_safezone.py`; QA and overlay map live under `production/pilot-01/`.
- v1.2d remains the evidence-safe layout baseline. It is not picture lock and does not choose a final voice.

Validated v1.2e motion-accent candidate:
- The 06:53–07:10 static explanatory-loop hold is replaced by one restrained qualitative cycle: five stages of 3.4 seconds, each with a low-alpha halo and traveling bead.
- No numbers, counters, rates, rankings, or data-like traces were introduced; the on-screen “EXPLANATORY MODEL / NOT A SPOTIFY FINDING” boundary remains visible.
- Runtime: exactly 602.000 seconds / 15,050 frames, 1920×1080/25 fps; full master decode passed.
- Master SHA-256: `12dc2f21b408ec44d1b06cb659fab7d1c6a48f0896626be1d5300d58e1d48ae4`.
- Encoded audio remains byte-identical to v1.2d (`MD5 2d00f8a41c542f1c07eac5fbd074cc26`); the canonical 161-cue SRT is unchanged.
- Overlay reproducibility was verified by identical independent SHA-256 renders: `25de248a59920161475fc3dafdf53bfac8d20dcb94e2ab8481beb8bcf602df17`.
- A local partial-file fault in the v1.2d source was caught before retention; the source was recovered from persistent storage and matched the locked v1.2d SHA before rebuilding.
- Builder: `scripts/build_pilot_01_v1_2e_motion_accent.py`; QA and timing map live under `production/pilot-01/`.
- v1.2e is the active reversible audiovisual review candidate. It is not picture lock and does not choose a final voice.

Current bottleneck:
- The static-loop fatigue risk is resolved in the active candidate.
- Transition silences at 03:28.65–03:32.61 and 04:45.77–04:50.04 now require a real-time editorial listen before any cut.

Next production gate:
- Perform a real-time audiovisual review of v1.2e and classify both long silences as intentional breathing room or pacing defects; only then build a reversible trim branch if needed.

Layer C should ingest repository-relative manifests and render only assets explicitly staged in the job directory. No paid APIs, external publishing, or secrets are required.
