# Pilot 01 Production State

Canonical title: **Why Does Everything Look the Same Now?**

Current production baseline:
- Master script v1.1 remains the canonical editorial source.
- Full animatic v1.1 runtime: 10:22.
- Active reversible review candidate: **v1.2f-pacing-trim**, 09:57.760.
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
- v1.2e remains the motion-treatment baseline. It is not picture lock and does not choose a final voice.

Validated v1.2f pacing-trim candidate:
- Audio, caption, and picture inspection classified the 03:28.64–03:32.61 and 04:45.76–04:50.05 gaps as overlong static holds; exactly 2.00 seconds of each breath is retained.
- Removed intervals: 03:30.640–03:32.600 (1.96s) and 04:47.760–04:50.040 (2.28s), total 4.24s / 106 frames.
- Runtime: exactly 597.760 seconds / 14,944 frames, 1920×1080/25 fps; master and caption proxy fully decode.
- Master SHA-256: `038b9eb7a638b07be70fe61d8c037c1332d41c5eb40d63862ea7d31717685c7a`.
- The 161-cue SRT is deterministically retimed, overlap-free, and ends at 09:56.960. No speech, evidence, qualification, counterexample, or v1.2e motion accent is removed.
- The first inclusive-endpoint render removed 108 frames and was rejected; the retained builder uses half-open intervals and passes the exact 14,944-frame gate.
- Builder: `scripts/build_pilot_01_v1_2f_pacing_trim.py`; QA and EDL live under `production/pilot-01/`.
- v1.2f is the active reversible review candidate. It is not picture lock and does not choose a final voice.

Validated v1.2f full-film audit and timing freeze:
- Full-film contact review sampled captioned frames every four seconds and inspected all seven chapter junctions at six frame-aligned offsets.
- No P0 visual, subtitle, evidence-boundary, transition, decode, or runtime defect was found.
- Caption audit remains clean: 161 cues, zero overlap, maximum two lines, maximum 19.99 characters/second, final cue at 09:56.960.
- Scratch-audio control measures -19.8 LUFS integrated, 7.6 LU LRA, -2.4 dBFS true peak; no -42 dB silence exceeds 2.110 seconds.
- Long evidence cards in S2–S5 and conclusion cards in S8 remain P1 motion-design opportunities, not timing defects; shortening them would reduce chart-reading or synthesis time.
- The v1.2f animatic timing is frozen as the current picture-lock candidate. It is not final picture lock, final voice, or licensed music.
- Audit: `production/pilot-01/v1.2f-full-film-visual-density-chapter-audit.md`; chapter matrix: `production/pilot-01/v1.2f-full-film-visual-density-chapter-audit.csv`.

Final voice and music authorization brief:
- The no-purchase decision brief is complete: locked four-part audition reel, 100-point voice and music scorecards, hard failure gates, four-phase music architecture, mix targets, rights/provenance fields, and exact authorization language.
- The standing autonomous-production mandate opens reversible no-cost internal auditions using rights-verified free/local tools. External contact, paid calls, subscriptions, licences, purchases, publication, and financial commitments remain closed.
- Brief: `production/pilot-01/final-voice-music-authorization-brief-v1.0.md`; scorecard: `production/pilot-01/final-voice-music-decision-scorecard-v1.0.csv`.

Blind no-cost voice audition v1.0:
- Four anonymous CMU Flite candidates cover the locked 232-word, four-excerpt reel at a cadence-matched 141.98–142.15 effective WPM; no post-render time stretch was used.
- All retained WAV masters (48 kHz/24-bit mono) and MP3 review files (48 kHz/192 kb/s mono) fully decode. Integrated levels are -20.6 to -20.2 LUFS; peaks remain at or below -3.0 dBFS except Candidate A at -6.9 dBFS.
- Rights provenance is pinned to Debian libflite1 2.2-6build3, the local package notice, and SHA-256 checksums for the runtime and each sealed voice library.
- Red-team rejected three intermediate states: unequal native cadence, an invalid voice-feature pointer, and a truncated Candidate C MP3 that disagreed with its WAV header. The retained builder now fails on decode, duration, or container mismatch.
- The technical gate passes, but no release voice is selected: naturalness, authority, pronunciation and restraint remain blind-listening gates and cannot be inferred from waveform metrics.
- Builder: `scripts/build_pilot_01_free_voice_audition_v1_0.py`; QA and scorecard: `production/pilot-01/free-voice-blind-audition-qa-v1.0.md` and `production/pilot-01/free-voice-blind-audition-scorecard-v1.0.csv`.


Launch instrumentation v1.0:
- Three claim-safe title/thumbnail cells are locked for a future native YouTube A/B test: canonical curiosity, concrete three-domain scope, and bounded safe-choice mechanism.
- All thumbnails are original 1280×720 vector-derived graphics with no brand, logo, copied interface, stock asset, or fabricated statistic; desktop and 320×180 mobile contact reviews passed.
- The primary packaging outcome is YouTube's native watch-time result, not raw CTR. Retention is read at the frozen v1.2f chapter boundaries; traffic-source mix and sample size are required before diagnosis.
- Early-reaction and universal-benchmark rules are rejected. The 6h read is technical only; retention review begins after processing, with 14 days or native completion as the lock point.
- Plan: `production/pilot-01/launch-instrumentation-plan-v1.0.md`; log: `production/pilot-01/launch-metrics-log-v1.0.csv`; cells: `production/pilot-01/metadata-variants-v1.0.csv`.
- Nothing was uploaded to YouTube or published; publication remains an explicit authorization gate.

Final source-link and description appendix v1.0:
- The seven master-script evidence families F1–F7 are mapped one-to-one to publication URLs, supported claims, excluded inferences, chapter anchors, and visual-rights restrictions.
- Ten URLs were checked on 2026-09-12: seven evidence sources plus the Material 3, IBM Carbon, and Porsche named counterexamples. Counterexamples remain separated as existence cases, not prevalence evidence.
- The publisher page behind the F3 DOI produced one automated timeout; the DOI remains canonical and the accessibility caveat is disclosed rather than silently treated as a pass.
- The publication-ready description is 2,317 characters, contains all eight exact v1.2f chapter anchors and ten source links, and stays independent of any upload or publication action.
- Appendix, registry, description, QA report, and SHA-256 manifest live under `production/pilot-01/`. Persistent pack SHA-256: `391dc47321cdaa0d9fdefaeaec7141d80fe437dfa1b3b2ab3b2714f9186ea535`.
- No source chart, logo, interface, photograph, or long quotation was copied; links are attribution and verification, not visual-use permission.


Validated v1.2g progressive-focus candidate:
- Five P1 long graphic holds in S2, S3, S4, S5, and S8 now use fifteen restrained, sequential outline-only focus accents on existing elements.
- The pass introduces no new words, figures, interfaces, evidence, causal claims, counters, or data-like traces; evidence/illustration boundaries remain unchanged.
- Runtime: exactly 597.760 seconds / 14,944 frames, 1920×1080/25 fps; full master decode passed.
- Master SHA-256: `3d1643246c066f377e841edc0f8653fec3c1bd9910d15151fb53732039259d27`.
- Encoded audio is bit-identical to v1.2f (`MD5 29ec265e370b50584c9dfdaaba569d02`); the 161-cue SRT and frozen edit timing are unchanged.
- Every new accent ends at or above y=815, preserving the locked y=820–1040 subtitle/player-control zone.
- Builder: `scripts/build_pilot_01_v1_2g_progressive_focus.py`; QA and timing map live under `production/pilot-01/`.
- v1.2g is retained as a reversible motion-design candidate; v1.2f remains the timing authority. Continuous human viewing may still revert the accents without affecting timing.


Validated v1.2g human-review kit:
- A full 1280×720 captioned review proxy preserves the exact 597.760-second / 14,944-frame v1.2g timeline and fully decodes.
- An exact 89.000-second / 2,225-frame side-by-side reel covers all five v1.2f/v1.2g intervention windows with two seconds of context where available.
- The 161-cue canonical SRT is unchanged; independent parsing confirms zero cues above two text lines. Final proxy captions remain in the lower player/caption region while upper-band evidence labels remain visible.
- Three intermediate states were rejected: a memory-heavy ten-renderer graph, a concat with non-monotonic audio timestamps and one extra frame, and an oversized subtitle style.
- Builder: `scripts/build_pilot_01_v1_2g_review_kit.py`; QA and scorecard live under `production/pilot-01/`.
- Review-pack SHA-256: `d382f8ae867520ff625ba2a09b55ea4b5b90d4bb1dedc993b678643867a0735a`.
- This kit enables the human retain/revert decision; it does not make that subjective decision or alter the frozen v1.2f timing authority.


Current bottleneck:
- The calibrated blind audition is technically ready, but its subjective editorial evaluation remains open. Launch instrumentation and the verified source appendix are ready but cannot be activated before final voice/music and explicit publication authorization. No release voice, music, licence, paid model, purchase, provider contact, upload, or publication has been selected.

Next production gate:
- Complete the blind editorial listen and either nominate one no-cost control for a full-film scratch conform or reject the local set without changing v1.2f timing. The v1.2g human-review kit is ready; continuous human viewing may retain or revert the motion pass without altering the frozen timing or evidence boundaries.

Layer C should ingest repository-relative manifests and render only assets explicitly staged in the job directory. No paid APIs, external publishing, or secrets are required.


Pre-publication control pack v1.0:
- A deterministic offline validator cross-checks the current v1.2g picture candidate, v1.2f timing authority, 161-cue SRT, eight chapter anchors, F1–F7 evidence families, CE1–CE3 counterexamples, three metadata/thumbnail cells, five analytics windows, and the four-candidate blind voice pack.
- All 32 technical checks pass. Master identity remains `3d1643246c066f377e841edc0f8653fec3c1bd9910d15151fb53732039259d27`, 597.760 seconds / 14,944 frames / 1920×1080 / 25 fps.
- The control pack SHA-256 is `abb98567184edd16e04e57b57f5c2f8d47bce42fcb29c2ce718f0db62f59023a`.
- The result is PASS_WITH_HUMAN_GATES, not publish authorization. Remaining gates are retain/revert v1.2g, blind final-voice selection, music/no-music authorization, final audio conform, metadata-cell choice, and explicit publication authorization.
- Validator: `scripts/validate_pilot_01_prepublication_bundle.py`; report, manifest, and upload checklist live under `production/pilot-01/`.
