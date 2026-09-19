# Pilot 01 — Kokoro timing recovery map v1.0

## Verdict

`PASS_MAPPING_ONLY — NOT CONFORM READY`

The exact 91-take raw and adaptive GitHub Actions artifacts were reconciled with the canonical 597.760-second recording script. The earlier adaptive workflow succeeded operationally but did not solve the editorial constraint: 50 takes still failed its untrimmed ≤1.15× test. Direct waveform analysis changes the shape of the problem materially without declaring it solved.

## Observed facts

- Voice authority: Kevin-selected Kokoro `am_michael`; no broad voice search resumed.
- Raw generation: 91/91 WAV takes exist; 62 overflow their frozen slots when container duration is used unchanged.
- Every retained WAV contains measurable outer silence. At a 10 ms RMS gate of −45 dBFS, while preserving 80 ms before and 120 ms after detected speech, the raw set contains 79.035 seconds of removable outer padding in aggregate.
- Canonical take windows contain 48.428 seconds of timeline silence. The conservative provisional rule exposes 23.523 seconds as potentially recoverable, fully locks chapter boundaries and sub-200 ms micro-pauses, and reserves 250–750 ms inside every other gap.
- A deterministic, non-double-counting allocation clears 68 takes at natural speed 1.00 using only safe outer trimming plus unique intra-chapter silence. The existing per-take adaptive outputs clear 9 more. Fourteen takes remain, totaling 10.405 seconds of residual deficit.
- Residual takes: T023, T027, T037, T041, T045, T049, T052, T058, T061, T062, T063, T064, T082, T088.
- T061 and T088 miss only 43 ms and 66 ms respectively after keeping the full 100 ms headroom. They are editorial-window checks, not automatic rewrite candidates.
- No audio was changed, stretched, regenerated, conformed, mixed, or approved for release.

## Inference and bounded decision

The dominant defect was partly measurement policy: total generated-file duration counted large leading/trailing pads as spoken content. This does not prove all 77 mapped takes will sound natural in context. It does show that global acceleration is unnecessary and would destroy quality for no compensating benefit.

The 12 material residuals should receive surgical candidate rewrites, one take at a time, with factual and listening review. T061 and T088 should first test a sub-100 ms local timing adjustment. Only affected takes should be regenerated. The authoritative intake and conformer remain unchanged and fail closed.

## Red-team findings

- The recoverable-silence rule is a planning hypothesis, not editorial approval; visual evidence holds may make some nominal gap unavailable.
- Outer-silence detection can move with threshold. Therefore the builder retains 200 ms of combined boundary padding and does not render from this map.
- Gap capacity is allocated once. No before/after silence is double-counted.
- Chapter transitions are fully protected.
- The candidate rewrites are deliberately provisional. They may not replace canonical text until source meaning and full-context naturalness pass.
- A 91/91 timing KPI is not sufficient: naturalness remains a threshold gate.

## Verification

Fourteen of fourteen deterministic and adversarial checks pass: exact 91-row coverage, unique take IDs, complete remedy partition, nonnegative timing, well-formed lineage hashes, locked chapter gaps, bounded gap capacity, no double counting, per-take speed ceiling ≤1.15, exact residual list, and byte-identical rerender of both CSV maps and the JSON summary.

## Next execution gate

1. Visually audit the 23.523 seconds of provisionally recoverable gaps against evidence semantics.
2. Test the 43 ms and 66 ms local window adjustments for T061/T088.
3. Fact-check and regenerate only the 12 proposed surgical rewrites at natural speed first.
4. Re-run the same waveform map, then the existing fail-closed 91-take intake and 597.760-second conformer.

This artifact has no publication, upload, final-master, or release authority.
