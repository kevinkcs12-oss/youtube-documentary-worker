# Pilot 01 — Audio Conform Provenance Gate QA v1.1

## Verdict

`VALIDATED — FIXTURE CANNOT ENTER RELEASE MODE`

The audio conform gate previously accepted any narration file whose container duration was approximately 597.760 seconds. That was insufficient after introduction of the final-narration timeline conformer: a synthetic fixture had the correct duration and could satisfy the old technical check.

Version 1.1 makes `--narration-conform-result` mandatory and binds the supplied narration bytes to the upstream conform result before checking the picture or rendering audio.

## Required provenance

- Schema: `pilot-01-final-narration-timeline-conform-v1.0`
- Exact narration SHA-256 match
- 28,692,480 samples and 91 placed takes
- PCM24 mono/48 kHz contract
- No time stretching or music
- `publishable=false`
- `release_authorized=false`
- Valid 64-character SHA-256 lineage for cue sheet, intake validator, intake result, delivery manifest and placement map

Dry-run mode may accept `PASS_FIXTURE_CONFORM_ONLY` only with `fixture_mode=true`. Release mode accepts only `PASS_NARRATION_CONFORM_ONLY` with `fixture_mode=false`.

## Validation

Nine of nine unit/adversarial tests pass:

1. Fixture accepted for review-only dry run.
2. The same fixture blocked in release mode.
3. Production conform provenance accepted in release-mode gate isolation.
4. Narration byte/hash substitution blocked.
5. Upstream `publishable=true` claim blocked.
6. Sample-count drift blocked.
7. Time-stretch claim blocked.
8. Schema substitution blocked.
9. Missing intake lineage blocked.

The actual 597.760-second synthetic fixture from the preceding milestone also passes dry-run provenance and is blocked in release mode. No picture render or publishable master was produced in this validation.

## Red-team boundary

This gate establishes internal chain-of-custody consistency; it is not a cryptographic signature service and does not replace human authorization, performer consent, rights review or the final release gate. A production result cannot be created autonomously because the final selected voice and authorized delivery do not yet exist.

The command-line interface intentionally changes: all future invocations must provide `--narration-conform-result`. No repository workflow or caller currently invokes this script, so the migration does not break an active automation.
