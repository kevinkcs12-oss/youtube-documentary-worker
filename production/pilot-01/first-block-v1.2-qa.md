# Pilot 01 — First Block 00:00–02:22 v1.2 QA

**Film:** *Why Does Everything Look the Same Now?*  
**Candidate:** v1.2 rights-safe continuous first block  
**Status:** Validated with caption-safe-zone and retention caveats; not whole-pilot picture lock

## Material result

The validated 64-second v1.2 opening has been conformed to the locked 78-second A018–A030 evidence module. The exact 01:04 handoff now moves from the explicit card “AN IMPRESSION IS NOT EVIDENCE” to “COLOR IS ONE PIECE OF A LARGER PATTERN.”

The same first 142 seconds of the repaired scratch-voice master are muxed for timing review only. The voice remains non-canonical and does not imply casting, tone, vendor, or paid-generation approval.

## Binary QA

| Check | Result |
|---|---|
| Picture and narrated duration | exactly 142.000 seconds |
| Video frame count | exactly 3,550 |
| Raster / cadence | 1920×1080 / 25 fps |
| Video codec | H.264 High, yuv420p |
| Narrated audio | AAC mono, 48 kHz, exactly 142.000 seconds |
| Full decode | pass |
| Black-frame interval | none detected at 0.08-second threshold |
| Subtitle cues | 20, ordered, overlap-free, 00:00:00.000–00:02:22.000 |
| Reproduction check | pass; rerun produced byte-identical picture and narrated SHA-256 values |

### Integrity

- Opening input SHA-256: `08282a5c3a62f340bedc6bfa655131a78aee2d0be1184e6121cb1a32baf276cc`
- Evidence input SHA-256: `f3da43d65a290eb45eb0ba4a473cb2ccdce37a4c1fe25b5b813ee97ae54ada41`
- Scratch master input SHA-256: `357bc0f3f0213fdd6dd2a12c1086802bcfa4696cdccbb6085c13fac9ac7ec7d1`
- Conformed picture SHA-256: `98f34bed54d2c7be7d0d06113be12765b3e8ffc5739e4c9e8e328fe57ea501be`
- Narrated candidate SHA-256: `97e14b3d2d64bdb54c188ed4c5276c560dfd2af9d3078c0641af5d009cabad14`
- Sidecar subtitle SHA-256: `1374b8ab20508f8859ee837b01ffdd302691b44da6fbbc470d52e39341ddbe54`

## 01:04 transition audit

- No duplicate, missing, black, or frozen transition frame was found.
- A 1.178-second narration pause crosses the boundary, matching the previously validated 1.177-second pacing measurement within AAC analysis tolerance.
- The outgoing card classifies the opening as an impression; the incoming card narrows the next claim to one measurable fragment. The transition therefore strengthens rather than blurs the illustration/evidence boundary.
- The palette and typography remain coherent across the cut while the evidence module introduces an amber section marker, making the epistemic change visible.

## Evidence and rights red-team

### Passed

- No bookstore, fascia, recognizable bookstore pedestrian, real phone interface, real logo, copied Axalta artwork, Creative PEC chart, or paid/generated footage appears.
- Opening stock footage remains illustrative and carries no geographic or statistical claim.
- The museum finding is explicitly bounded to one collection and not presented as a random sample of the world.
- Axalta values remain 29/23/22/7, 74%, 81%, and Europe gray 26%; observation and explanation remain separated.
- The parking footage stays in natural color and is labelled illustrative before quantitative evidence.
- “The safest color…” remains visibly marked as interpretive synthesis rather than survey evidence.

### Caption and mobile review

A simulated bottom-caption overlay confirms that every primary claim and key number remains readable. Captions can cover some tertiary source lines and lower caveat text, especially on the museum limitation and contributor cards. The essential boundaries remain duplicated in large primary headings, so the candidate passes as an animatic. Before final export, move all indispensable caveats above the lower caption band or provide authored caption positioning; do not rely on tiny bottom text as the only qualifier.

### Residual editorial risks

- The opening contains 21 seconds of original static schematics and repeats the office/apartment motifs. In the continuous cut this reads as a deliberate argument structure, but real audience retention has not been measured.
- The change from bright live footage to dark evidence graphics is clear and intentional, though music and final color could make it feel more abrupt.
- Contact sheets and scratch narration can reject obvious fatigue; they cannot prove audience retention or final mix quality.

## Decision

Promote this file as the working 00:00–02:22 rights-safe candidate. Do not declare whole-pilot picture lock. The first-block gate is technically and editorially cleared with a documented caption-safe-zone requirement for final motion design.

## Next highest-EV action

Resume the reversible whole-pilot v1.2b natural-cadence branch: rewrite and rebuild 02:28–02:48 to a 14-second spoken passage and 06:22–07:26 to 54 seconds without time-compressing narration, while preserving every evidence family, counterexample, and the now-validated first 2:22.
