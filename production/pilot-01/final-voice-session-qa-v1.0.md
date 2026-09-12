# Pilot 01 — Final voice session pack QA and red-team v1.0

## Decision

**PASS as a recording-session preparation pack; NOT AUTHORIZED as a final voice selection or publication master.**

The pack converts the canonical v1.2f subtitle authority into a take-based recording script without changing a word, moving a cue, or changing the frozen 09:57.760 picture timing. It removes a practical production dependency while preserving every human and authorization gate.

## Verified inventory

- Source: `restored/Pilot_01_Animatic_00m00_09m57.760_v1.2f_pacing_trim.srt`
- Source SHA-256: `2bc54569b979eb9e312a82ad1ec59332560e75c4a2f84523061104230681b2b9`
- 161 ordered cues; zero overlaps; final cue ends at 00:09:56.960.
- 1,198 canonical words grouped into 91 reversible recording takes across eight chapters.
- At 142 words/minute, estimated spoken time is 506.197 seconds, leaving 91.563 seconds inside the 597.760-second picture timeline for pauses, evidence reading and transitions.
- Required capture: mono, 48 kHz, 24-bit; dry; no time stretch, music, reverb or mastering limiter.

## Timing exceptions

Subtitle windows are not performance targets. Three short takes exceed the 165 WPM review threshold if read strictly inside their cue windows:

| Take | Window | Diagnostic | Direction |
|---|---:|---:|---|
| T023 | 4.308 s | 167.1 WPM | Preserve the contrast; use surrounding air and record a clean pickup. |
| T031 | 4.540 s | 171.8 WPM | Keep one natural phrase; do not rush “billboard” or “tiny icon.” |
| T065 | 2.836 s | 169.3 WPM | Emphasize that the loop is our model, not Spotify’s finding. |

Eight early evidence takes fall below 100 effective WPM because their picture windows deliberately allow figures and limitations to register. They are breathing opportunities, not instructions to drag delivery.

## Pronunciation scope

Only **Nielsen** and **Spotify** appear in the canonical narration and require confirmation before recording. Nine additional terms are retained as reference-only context; they must not consume session time unless the script changes under a separately authorized revision.

## Red-team findings

1. **Caption-window fallacy:** reading every take to its subtitle duration would produce uneven performance. Mitigation: the script explicitly targets 138–146 WPM overall and labels per-take WPM as diagnostic only.
2. **Unauthorized rewrite risk:** a performer may try to shorten tight takes. Mitigation: wording is locked; pickups use take IDs and can borrow surrounding pause budget.
3. **Premature voice promotion:** the pack could be mistaken for selection. Mitigation: every take remains `PENDING_HUMAN_VOICE_SELECTION`; no voice candidate is named or ranked.
4. **Provisional-audio leakage:** this pack contains no final recording and cannot clear the existing prepublication or audio-conform gates.
5. **Rights and consent:** no cloned voice, third-party performance, paid model or external contact was used.

## Retention rule

Retain the script, cue sheet, pronunciation flags, manifest, generator and this QA record. Do not promote any narration to final until blind human selection, pronunciation confirmation, performance direction, final audio conform and explicit publication authorization are all recorded.
